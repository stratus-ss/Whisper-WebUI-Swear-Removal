#!/usr/bin/env python3
"""stt_uploader.py

Background watcher that pulls MP3s from SOURCE_DIR, uploads them to
the Whisper-WebUI STT server, polls for completion, and writes the SRT
result locally. Designed to run as a long-lived nohup process on
stratus-nas.

Behavior
--------
- Modes:
    --once   Process every mp3 currently in SOURCE_DIR, then exit.
    --watch  (default) Loop forever, scanning for new mp3 every
             SCAN_INTERVAL seconds.
- Layout:
    SOURCE_DIR/                      (default /tmp/forTTS)
      *.mp3                          input queue
      srt/<name>.srt                 transcribed output
      done/<name>.mp3                mp3 moved here on success
      bad/<name>.mp3                 mp3 moved here on upload error
      bad/<name>.srt                 srt kept here if invalid
      .stt_uploader.pid              PID file (watch mode only)
      .stt_uploader.log              log file
- Restart-safe: any mp3 already in done/ is considered processed;
  any in bad/ is left for manual review. tmp partials (.uploading)
  are cleaned up on start.
- Cleanly handles SIGINT / SIGTERM: stops after the current file
  completes and removes its PID file.

API contract (matches download_ANS/new_transcription_upload.py):
  POST {api_url}/transcription/?<params>  multipart file=<mp3>
       -> {"identifier": "...", "message": "Task queued"}
  GET  {api_url}/task/{id}
       -> {"status": "completed|failed|error|...",
           "progress": 0.0..1.0,
           "result":  [{"start": ..., "end": ..., "text": "..."}]}
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
import yaml


# ---------- defaults ------------------------------------------------------- #

DEFAULT_SOURCE_DIR = "/tmp/forTTS"
DEFAULT_CONFIG = """\
# Default config for stt_uploader.py on stratus-nas
# Edit values as needed; English-language transcription of the sitcom batch.
whisper:
  host: "whisper.x86experts.com"
  port: 8001

  # Pass null to let the server auto-detect language.
  lang: "english"

  # Model selection. large-v3 is highest quality; medium is a good speed/quality tradeoff.
  model_size: "large-v3"

  # Tuning (passed as query params to /transcription/)
  vad_filter: true
  compute_type: "float16"
  beam_size: 5
  best_of: 5
  batch_size: 8
  no_speech_threshold: 0.5
  log_prob_threshold: -1.0
  temperature: 0
  word_timestamps: true
  condition_on_previous_text: true

  # Optional flags left disabled
  diarize: false
  bgm_separation: false
"""

POLL_INTERVAL = 5            # seconds between /task/ status checks
UPLOAD_TIMEOUT = 600         # seconds for the initial POST (large mp3)
POLL_TIMEOUT = 7200          # 2h per-task ceiling
SCAN_INTERVAL = 15           # seconds between scans in --watch mode
STUCK_PROGRESS_TIMEOUT = 600 # seconds with NO progress change on an
                             # in_progress task before we assume it
                             # died (e.g. model-bin download race
                             # during cold-cache first request) and
                             # cancel + re-POST


# ---------- config --------------------------------------------------------- #

@dataclass
class Config:
    api_url: str
    api_settings: dict

    @classmethod
    def load(cls, path: Path) -> "Config":
        with path.open() as f:
            data = yaml.safe_load(f)
        w = data.get("whisper", {})
        host = w.pop("host", "localhost")
        port = w.pop("port", 8001)
        api_url = f"http://{host}:{port}"
        # Drop keys that are local-only and shouldn't be sent to the API.
        settings = {k: v for k, v in w.items() if v is not None}
        return cls(api_url=api_url, api_settings=settings)


# ---------- API helpers ---------------------------------------------------- #

def upload(mp3_path: Path, api_url: str, settings: dict, log: logging.Logger) -> str:
    with mp3_path.open("rb") as fh:
        files = {"file": (mp3_path.name, fh, "audio/mpeg")}
        log.info("POST %s/transcription/  size=%s", api_url,
                 f"{mp3_path.stat().st_size/1e6:.1f}MB")
        r = requests.post(
            f"{api_url}/transcription/",
            files=files,
            params=settings,
            timeout=UPLOAD_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    task_id = data.get("identifier") or data.get("task_id") or data.get("id")
    if not task_id:
        raise RuntimeError(f"No task id in upload response: {data}")
    log.info("Queued task %s (%s)", task_id, data.get("message", "ok"))
    return task_id


def poll(task_id: str, api_url: str, log: logging.Logger) -> dict:
    """Poll /task/{id} until status is completed / failed / error.

    Detects "stuck" tasks: the API reports ``in_progress`` with
    ``progress=0.0`` even after the server-side worker has crashed
    (commonly: model download race on first cold-cache hit). When we
    see no progress change for STUCK_PROGRESS_TIMEOUT seconds, we
    raise StuckTask so the caller can re-POST.
    """
    deadline = datetime.now() + timedelta(seconds=POLL_TIMEOUT)
    last_pct = -1.0
    last_change_at = datetime.now()
    while datetime.now() < deadline:
        try:
            r = requests.get(f"{api_url}/task/{task_id}", timeout=30)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as exc:
            log.warning("Poll error on %s: %s — retrying", task_id, exc)
            time.sleep(POLL_INTERVAL)
            continue

        status = (data.get("status") or "").lower()
        progress = data.get("progress") or 0
        try:
            pct = float(progress)
        except (TypeError, ValueError):
            pct = 0.0

        if pct != last_pct:
            log.info("[%s] status=%s progress=%.1f%%", task_id, status, pct * 100)
            last_pct = pct
            last_change_at = datetime.now()

        if status == "completed":
            return data
        if status in ("failed", "error"):
            raise RuntimeError(
                f"Task {task_id} {status}: {data.get('error') or data}"
            )
        # Stuck-task detection (server silently abandons the worker but
        # leaves the task in_progress indefinitely).
        if status == "in_progress" and (
            datetime.now() - last_change_at
        ).total_seconds() > STUCK_PROGRESS_TIMEOUT:
            raise StuckTask(
                f"Task {task_id} stuck at progress={pct:.4f} for >"
                f"{STUCK_PROGRESS_TIMEOUT}s with no status change"
            )
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Task {task_id} exceeded {POLL_TIMEOUT}s deadline")


class StuckTask(RuntimeError):
    """Task is in_progress but progress hasn't changed for too long."""


def seconds_to_srt(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def save_srt(payload: dict, dest: Path) -> bool:
    """Convert the API result to SRT; return True if written, False if empty."""
    result = payload.get("result")
    if not isinstance(result, list) or not result:
        # Fallback: dump raw payload as JSON alongside the SRT path.
        raw = dest.with_suffix(".raw.json")
        raw.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return False
    with dest.open("w", encoding="utf-8") as f:
        for i, seg in enumerate(result, 1):
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            f.write(f"{i}\n")
            f.write(f"{seconds_to_srt(seg.get('start', 0))} --> "
                    f"{seconds_to_srt(seg.get('end', 0))}\n")
            f.write(f"{text}\n\n")
    return True


# ---------- state ---------------------------------------------------------- #

class State:
    """Per-run mutable state, including the SIGTERM flag."""

    def __init__(self) -> None:
        self.stop = False

    def install_signals(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._on_signal)
        # SIGHUP doesn't exist on Windows; OK to skip on Linux/Mac.
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, self._on_signal)

    def _on_signal(self, signum, _frame) -> None:
        self.stop = True


def setup_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("stt_uploader")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s",
                            datefmt="%Y-%m-%dT%H:%M:%S")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)
    return log


# ---------- core ----------------------------------------------------------- #

def process_one(mp3: Path, cfg: Config, dirs: "Dirs", log: logging.Logger) -> str:
    """Process one mp3. Returns 'ok' | 'bad' | 'skipped'."""
    srt_dst = dirs.srt / (mp3.stem + ".srt")
    if srt_dst.exists():
        log.info("Skip %s — SRT already exists at %s", mp3.name, srt_dst)
        return "skipped"

    # Mark-in-progress so we don't double-pick in --watch mode.
    lock = mp3.with_suffix(mp3.suffix + ".uploading")
    if lock.exists():
        log.info("Skip %s — upload lock present (%s)", mp3.name, lock.name)
        return "skipped"
    try:
        lock.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as exc:
        log.warning("Could not create lock for %s: %s", mp3.name, exc)

    try:
        task_id = upload(mp3, cfg.api_url, cfg.api_settings, log)
        payload = poll(task_id, cfg.api_url, log)
        if save_srt(payload, srt_dst):
            shutil.move(str(mp3), str(dirs.done / mp3.name))
            log.info("OK  %s  →  %s", mp3.name, srt_dst)
            return "ok"
        log.error("Empty result for %s; raw dumped, moving to bad/", mp3.name)
        dirs.bad.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mp3), str(dirs.bad / mp3.name))
        shutil.move(str(srt_dst), str(dirs.bad / srt_dst.name))
        return "bad"
    except StuckTask as exc:
        log.warning("STUCK %s — server abandoned task %s: %s — will re-POST",
                    mp3.name, task_id, exc)
        # The mp3 is still in source dir (no move happened yet).  Return
        # 'skipped' so the outer scan loop gives up on it for now; the
        # next scan cycle will pick it up again.
        return "skipped"
    except Exception as exc:
        log.exception("FAILED %s: %s", mp3.name, exc)
        dirs.bad.mkdir(parents=True, exist_ok=True)
        if mp3.exists():
            shutil.move(str(mp3), str(dirs.bad / mp3.name))
        # Drop any partial SRT so the bad/ copy is the only copy.
        if srt_dst.exists():
            try:
                shutil.move(str(srt_dst), str(dirs.bad / srt_dst.name))
            except OSError:
                pass
        return "bad"
    finally:
        if lock.exists():
            try:
                lock.unlink()
            except OSError:
                pass


@dataclass
class Dirs:
    src: Path
    srt: Path
    done: Path
    bad: Path

    @classmethod
    def from_source(cls, src: Path) -> "Dirs":
        return cls(src=src, srt=src / "srt",
                   done=src / "done", bad=src / "bad")


def cleanup_partials(dirs: Dirs, log: logging.Logger) -> None:
    """Best-effort: clear .uploading markers from a previous run."""
    for lock in dirs.src.glob("*.uploading"):
        try:
            lock.unlink()
            log.info("Removed stale lock: %s", lock.name)
        except OSError:
            pass


def list_pending(dirs: Dirs) -> list[Path]:
    return sorted(p for p in dirs.src.glob("*.mp3")
                  if not p.name.startswith("."))


def write_pid(pid_file: Path, log: logging.Logger) -> None:
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    log.info("Wrote PID %s to %s", os.getpid(), pid_file)


def remove_pid(pid_file: Path) -> None:
    try:
        if pid_file.exists() and pid_file.read_text().strip() == str(os.getpid()):
            pid_file.unlink()
    except OSError:
        pass


# ---------- main ----------------------------------------------------------- #

def run(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    cfg_path = Path(args.config).expanduser().resolve() if args.config else None

    if cfg_path and cfg_path.exists():
        cfg = Config.load(cfg_path)
    else:
        cfg = Config.load_from_dict(yaml.safe_load(DEFAULT_CONFIG)["whisper"])
        # Inline load to avoid coupling to a separate class method.

    dirs = Dirs.from_source(source)
    for d in (dirs.srt, dirs.done, dirs.bad):
        d.mkdir(parents=True, exist_ok=True)

    log = setup_logging(dirs.src / ".stt_uploader.log")
    log.info("=== stt_uploader start ===")
    log.info("Source: %s", source)
    log.info("API:    %s", cfg.api_url)
    log.info("Settings: %s", cfg.api_settings)

    state = State()
    state.install_signals()
    cleanup_partials(dirs, log)

    if args.watch:
        write_pid(dirs.src / ".stt_uploader.pid", log)
    try:
        while True:
            processed = {"ok": 0, "bad": 0, "skipped": 0}
            for mp3 in list_pending(dirs):
                if state.stop:
                    log.info("Stop requested — exiting scan")
                    break
                result = process_one(mp3, cfg, dirs, log)
                processed[result] = processed.get(result, 0) + 1
            log.info("Scan complete: %s", processed)

            if not args.watch or state.stop:
                break
            for _ in range(SCAN_INTERVAL):
                if state.stop:
                    break
                time.sleep(1)
        return 0 if processed["bad"] == 0 else 2
    finally:
        if args.watch:
            remove_pid(dirs.src / ".stt_uploader.pid")
        log.info("=== stt_uploader exit ===")


# Small shim so the fallback config path doesn't depend on a second method.
def _load_from_dict_shim(self, w: dict) -> "Config":
    host = w.pop("host", "localhost")
    port = w.pop("port", 8001)
    settings = {k: v for k, v in w.items() if v is not None}
    return Config(api_url=f"http://{host}:{port}", api_settings=settings)
Config.load_from_dict = classmethod(_load_from_dict_shim)  # type: ignore[attr-defined]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--watch", action="store_true",
                      help="Run continuously (default).")
    mode.add_argument("--once", action="store_true",
                      help="Process the current queue and exit.")
    p.add_argument("--source", default=DEFAULT_SOURCE_DIR,
                   help=f"Directory to watch (default: {DEFAULT_SOURCE_DIR})")
    p.add_argument("--config", default=None,
                   help="YAML config file (default: built-in).")
    args = p.parse_args()
    if not args.watch and not args.once:
        args.watch = True
    return args


if __name__ == "__main__":
    sys.exit(run(parse_args()))

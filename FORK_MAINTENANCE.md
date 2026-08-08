# Fork Maintenance — Whisper-WebUI-Swear-Removal

Maintenance notes for fork-specific changes and deviations from upstream
[Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI).

## Transcription Error Handling (2026-08-08)

`run_transcription` in `backend/routers/transcription/router.py` wraps the
pipeline execution in a try/except:

- On success: task transitions `QUEUED -> IN_PROGRESS -> COMPLETED` with the
  segment list stored in `result`.
- On any pipeline exception: the task is marked `FAILED` with the error message
  stored in `error` — no more tasks stuck forever in `IN_PROGRESS`.

The server config override (router.py:124-127) makes `model_size`,
`compute_type`, and `enable_offload` authoritative from
`backend/configs/config.yaml` regardless of client-supplied parameters. This
enables the dual-whisper deployment where separate services run different
models:

| Service | Port | Config mounted | Model |
|---------|------|----------------|-------|
| backend-app-1 | 8001 | `config.yaml` | `small` |
| backend-transcription-1 | 8002 | `config-largev2.yaml` | `large-v2` |

### Local GPU functional test procedure

Run the full local proof on a CUDA-capable host (tested on RTX 5070 Ti, 2026-08-08):

```bash
source venv/bin/activate
pip install sqlmodel jiwer python-dotenv

# Regression tests: pipeline failure -> FAILED status; corrupt upload -> clean error
python -m pytest backend/tests/test_transcription_failure.py -v

# Happy path: real jfk.wav through the full FastAPI stack, WER < 0.1 vs TEST_ANSWER
python -m pytest backend/tests/test_backend_transcription.py -v

# Ordering-independence check (failure + success in one run)
python -m pytest backend/tests/test_transcription_failure.py backend/tests/test_backend_transcription.py -v
```

DB evidence (SQLite `backend/records.db`, table `tasks`):

```bash
python -c "import sqlite3; c=sqlite3.connect('backend/records.db'); print(c.execute('select status, count(*) from tasks group by status').fetchall())"
```

### Live-service verification (containers-gpu)

The same byte-identical `router.py` (md5 `3a25be8f254de62c4e0a0fdaefa5a899`) is
bind-mounted into both backend containers. Verify the running uvicorn processes
started after the file mtime (no `--reload` in the entrypoint):

```bash
ssh root@containers-gpu 'stat -c "%y" /AIStuff/Whisper-WebUI/backend/routers/transcription/router.py'
ssh root@containers-gpu 'for c in backend-app-1 backend-transcription-1; do docker exec $c ps aux | grep uvicorn; done'
```

## Segment Merger Speaker Awareness (2026-08-08)

Diarized transcriptions (`is_diarize=True`) were producing mid-line `SPEAKER_XX`
labels — e.g. `SPEAKER_00|What are you doing? SPEAKER_01|I'm fixing a stat` —
because `SegmentMerger.merge_segments` (introduced in upstream commit `0efb138`)
merged consecutive segments without knowing they belonged to different speakers.
The fix adds structural speaker awareness:

- **`Segment.speaker` field** (`modules/whisper/data_classes.py`): new
  `Optional[str]` field (default `None`). Backward-compatible — existing
  construction sites and `model_dump()` calls automatically pick it up.
- **`Diarizer.run` populates `Segment.speaker`** (`modules/diarize/diarizer.py`):
  the segments_result loop passes `speaker=None if speaker == "None" else speaker`
  into the constructor. The legacy `"None"` sentinel string is preserved for the
  text-prefix concatenation (display compatibility — subtitle writer and WebUI
  read `segment["text"]`) while the structured field carries the real value.
- **`SegmentMerger` is speaker-aware** (`modules/whisper/segment_merger.py`):
  - `_should_merge` gained `current_speaker=None, next_speaker=None` params; the
    **first** check is `if current_speaker != next_speaker: return False` — a
    hard boundary that no merge may cross.
  - On a true merge, the redundant `SPEAKER_XX|` or `None|` prefix is stripped
    from the appended text via `SPEAKER_PREFIX_RE.sub('', nxt_text, count=1)`.
- **Diarization-off equivalence:** when both segments have `speaker=None`,
  `None == None` → True → merge allowed (existing behavior preserved). The 11
  pre-existing merger tests act as the regression suite for this.

### Local GPU functional test procedure

Run the full local proof on a CUDA-capable host (tested on RTX 5070 Ti, 2026-08-08):

```bash
# Stage 90s excerpt from a multi-speaker D&D session (replace with any multi-speaker WAV)
ffmpeg -y -ss 1440 -t 90 -i <source_flac> -ac 1 -ar 16000 tests/dnd_24aug_90s.wav

# Unit tests (16 cases: 11 pre-existing + 5 new speaker-aware cases)
source venv/bin/activate && python -m pytest tests/test_segment_merger.py -v

# Functional test (requires GPU + pyannote model cached + HF_TOKEN)
source venv/bin/activate
set -a && source backend/.env && set +a
# Pre-existing environment workaround: system cuDNN 9.25 ABI mismatch with PyTorch 2.8's
# bundled cuDNN 9.10 — force the bundled lib to be loaded first.
export LD_LIBRARY_PATH=venv/lib/python3.11/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH}
python -m pytest tests/test_merger_diarization_functional.py -v
```

The functional test asserts ≥1 speaker-labeled line exists (diarization ran)
AND zero mid-line `SPEAKER_XX|` labels. On the 24Aug2025 D&D session excerpt:
33 raw segments → 32 after merge (1 cross-speaker boundary respected),
31 speaker-prefixed lines, 0 mid-line speaker labels.

The staged `tests/dnd_24aug_90s.wav` is excluded from git via the existing
`*.wav` rule in `.gitignore` line 1.

## Adaptation Notes

Plan-vs-reality deviations recorded per the planning protocol (A13):

| Plan said | Actually did | Why |
|-----------|--------------|-----|
| Apply fix to remote file | No remote file modification — md5 verified byte-identical | Fix was already deployed (file mtime Jul 26; both uvicorn processes restarted after) |
| Restart/soft-restart to activate | None performed | Code already active; zero-disruption required |
| Test uses default TestClient | `raise_server_exceptions=False` added | Background-task exceptions re-raised by `run_transcription` surface in TestClient only |
| Happy-path test reads `result[0]` | Concatenates all segment texts before WER | Multi-segment output; `result[0]` undercounts the transcription |
| Commit 3 files | Commit 4 files (added `test_backend_transcription.py`) | Test patch required to fix WER assertion |
| Functional test on synthesized 2-speaker clip | Used real D&D session audio excerpt (`24Aug2025.flac`, 0:24:00–0:25:30) | Authentic multi-speaker recording available locally — better realism than synthesis |
| `.gitignore` needs new line for staged WAV | No `.gitignore` edit needed | Existing `*.wav` rule (line 1) already covers `tests/dnd_24aug_90s.wav` |
| `_hparams(merge_max_words=N)` forwards to model | Added `merge_max_words=merge_max_words` to `WhisperParams(...)` constructor call | Plan bug — original call dropped the parameter, making merge-on/merge-off comparison a false negative |
| Commit 7 files | Commit 6 files (3 production + 2 tests + 1 doc) | `.gitignore` excluded since no edit was needed |
| Code comment on `"None"` sentinel string | Documented here in maintenance doc instead | Repo follows zero-comment convention; ADVISORY #5 from code review |

## Testing

- Run unit/regression tests: `python -m pytest backend/tests/ -v` (requires local
  GPU for the happy-path transcription test; `test_backend_bgm_separation.py` and
  `test_backend_vad.py` require additional model downloads and are excluded from
  the quick check).
- Quality gates: `agent_planning/scripts/quality_gate.sh <paths>` (ruff
  complexity checks) and `agent_planning/scripts/secret_scan.sh <paths>`.

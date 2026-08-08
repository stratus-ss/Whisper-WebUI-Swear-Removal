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

## Adaptation Notes

Plan-vs-reality deviations recorded per the planning protocol (A13):

| Plan said | Actually did | Why |
|-----------|--------------|-----|
| Apply fix to remote file | No remote file modification — md5 verified byte-identical | Fix was already deployed (file mtime Jul 26; both uvicorn processes restarted after) |
| Restart/soft-restart to activate | None performed | Code already active; zero-disruption required |
| Test uses default TestClient | `raise_server_exceptions=False` added | Background-task exceptions re-raised by `run_transcription` surface in TestClient only |
| Happy-path test reads `result[0]` | Concatenates all segment texts before WER | Multi-segment output; `result[0]` undercounts the transcription |
| Commit 3 files | Commit 4 files (added `test_backend_transcription.py`) | Test patch required to fix WER assertion |

## Testing

- Run unit/regression tests: `python -m pytest backend/tests/ -v` (requires local
  GPU for the happy-path transcription test; `test_backend_bgm_separation.py` and
  `test_backend_vad.py` require additional model downloads and are excluded from
  the quick check).
- Quality gates: `agent_planning/scripts/quality_gate.sh <paths>` (ruff
  complexity checks) and `agent_planning/scripts/secret_scan.sh <paths>`.

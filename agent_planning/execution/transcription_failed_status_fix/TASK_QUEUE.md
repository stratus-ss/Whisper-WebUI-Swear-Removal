# Task Queue — transcription_failed_status_fix

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 1  | Local environment preflight | done | sqlmodel+jiwer+dotenv installed; jfk.wav 352KB/11.0s; backend import OK |
| 2  | Add regression tests for the FAILED-status path | done | 2 tests pass; added raise_server_exceptions=False (SCOPE-GAP deviation) |
| 3  | Local functional test run on the GPU with real audio | done | patched test_backend_transcription.py to concat segments; 3 tests pass; DB has 5 COMPLETED + 7 FAILED |
| 4  | Remote preflight + deployment verification (read-only) | done | md5 match 3a25be8f; uvicorn started Jul29/Jul31 (post mtime Jul26); /docs 200/200; jfk.wav staged |
| 5  | Remote functional verification (live services) | done | both services 500 on corrupt + survive; happy path COMPLETED on :8001 (small) and :8002 (large-v2) with full JFK quote |
| 6  | Code review — full quality gate (penultimate) | done | 13 findings: 10 PASS, 3 ADVISORY (deferred), 0 FAIL; no blockers for T7 |
| 7  | Doc update + commit (final) | done | FORK_MAINTENANCE.md created (81 lines); committed 969b16b (4 files, 179+/31-) |

<!-- Statuses: todo / doing / done / blocked / skipped -->

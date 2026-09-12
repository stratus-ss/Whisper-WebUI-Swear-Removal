# Task Queue — segment_merger_speaker_fix

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 1  | Add `speaker` field to the Segment model | done | data_classes.py — Optional[str] default None after `text` field |
| 2  | Set the speaker field in Diarizer.run | done | diarizer.py lines 73-83 — speaker= kwarg + "None"→None mapping |
| 3  | Make SegmentMerger speaker-aware (boundary + strip) | done | segment_merger.py — SPEAKER_PREFIX_RE, _should_merge param, strip in merge branch |
| 4  | Unit tests — speaker-aware merging | done | extend tests/test_segment_merger.py (5 new tests, _seg speaker param) |
| 5  | GPU functional test — real diarization + merge | done | tests/test_merger_diarization_functional.py + ffmpeg stage + .gitignore |
| 6  | Code review — full quality gate (penultimate) | done | CQ9.3 findings: 16 PASS, 3 ADVISORY, 0 FAIL |
| 7  | Doc update + commit (final) | done | commit da2e2e2 (6 files, 251+/5-) |

<!-- Statuses: todo / doing / done / blocked / skipped -->

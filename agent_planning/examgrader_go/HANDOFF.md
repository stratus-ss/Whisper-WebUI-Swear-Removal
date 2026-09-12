# Handoff — examgrader_go

**Written:** 2026-06-29 19:49

## Bootstrap
Read in order:
1. `zed_plans/examgrader_go_rewrite_2026-06-29.md` — OBJECTIVE + Task 14 section only
2. `agent_planning/execution/examgrader_go/SESSION_BRIEF.md`
3. `agent_planning/execution/examgrader_go/TASK_QUEUE.md`

## Where We Are
Tasks 1-13 complete. Binary works, deployed, validated. Task 14 is the wrapper generation + solve.sh fix + KB writeback.

## Next Action
1. Find all 42 grade.sh files: `find Perf_Course/exam_prep/scripts Perf_Course/exam_prep/MiniMax_scripts -name grade.sh -type f | wc -l` — expect 42.
2. For each, generate wrapper template:
   - `COMMON_DIR="${SCRIPT_DIR}/../common"` for normal labs (depth 2)
   - `COMMON_DIR="${SCRIPT_DIR}/../../common"` for course_labs/comprehensive_review (depth 3)
   - Determine LAB_ID = directory name + "_" + tree ("scripts" or "minimax")
3. Backup each grade.sh as grade.sh.bak.
4. Write wrapper that execs `${COMMON_DIR}/examgrader ${LAB_ID} --history-dir ${COMMON_DIR}/../.run_history --sync-config ${COMMON_DIR}/sync_config.sh "$@"`.
5. chmod +x each wrapper.
6. Find solve.sh files with fake data: `rg -l 'placeholder|evidence line|WARNING.*produced minimal' Perf_Course/exam_prep/`.
7. Replace fake data with `SOLVE_ERROR: <tool> produced no output` markers.
8. Verify: `find ... -name grade.sh -type f | wc -l` = 42; no fake-data rg matches.
9. On VM: ssh and run a wrapper to confirm it works.
10. KB writeback: update `knowledge/services/rhel10-exam.md` with examgrader location + wrapper template.

## Known Blockers / Gotchas
- Wrapper for course_labs: depth-3 path (e.g., `course_labs/ch02_perftools_review/grade.sh` → `../../common/examgrader`).
- Wrapper for normal labs: depth-2 (e.g., `lab01_monitoring/grade.sh` → `../common/examgrader`).
- Don't modify Go source, setup.sh, teardown.sh.
- Don't delete .bak files.
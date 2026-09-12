# Task Queue — image_rebuild_local_replica

| ID | Task | Status | Notes |
|----|------|--------|-------|
| 1  | Preflight — VRAM, disk, image pull policy | todo | Read-only probes; capture GPU+container+image state |
| 2  | Stage local replica orchestration files (committable artifacts) | todo | local-replica/docker-compose.local-replica.yaml + run-functional-test.sh |
| 3  | Build new image tag swear0.3.7 | todo | docker build -f backend/Dockerfile -t ...:swear0.3.7 .; verify md5 in image |
| 4  | Stop existing local backend-app-1 and launch dual-service replica | todo | docker stop old; cd local-replica && docker compose up -d |
| 5  | In-container functional test against :8001 | todo | bash local-replica/run-functional-test.sh backend-app-1 |
| 6  | Code review — scripts and compose file | todo | CQ9.3 findings table; model-switch pause gate |
| 7  | Doc update + commit (final) | todo | FORK_MAINTENANCE.md + 3-file commit |

<!-- Statuses: todo / doing / done / blocked / skipped -->

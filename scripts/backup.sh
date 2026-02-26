#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

docker compose exec -T postgres pg_dump -U leave leave > "backups/leave_${TS}.sql"
docker run --rm -v test_llm_pgdata:/volume -v "$(pwd)/backups:/backup" alpine tar czf "/backup/pgdata_${TS}.tar.gz" -C /volume .

echo "Backup done: $TS"

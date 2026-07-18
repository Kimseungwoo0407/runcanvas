#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="/app/storage/backups/app-${STAMP}.db"

cd "$ROOT_DIR"
docker compose exec -T backend python -m app.db_backup "$TARGET"
find storage/backups -maxdepth 1 -type f -name 'app-*.db' -printf '%T@ %p\n' \
  | sort -nr | awk 'NR>14 {print $2}' | xargs -r rm -f

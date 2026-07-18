#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 storage/backups/app-<timestamp>.db" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"

if [[ ! -f "$BACKUP" ]]; then
  echo "backup not found: $BACKUP" >&2
  exit 2
fi

cd "$ROOT_DIR"
docker compose stop backend worker
docker compose run --rm -v "$BACKUP:/restore/source.db:ro" backend \
  python -m app.db_restore /restore/source.db
docker compose up -d backend worker
docker compose exec -T backend python -m app.db_check

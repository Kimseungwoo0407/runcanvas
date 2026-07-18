from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from app.config import get_settings


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise RuntimeError("backup supports SQLite only")
    return Path(database_url.removeprefix(prefix))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m app.db_backup /app/storage/backups/app.db")
    settings = get_settings()
    source = sqlite_path(settings.DATABASE_URL)
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_db, sqlite3.connect(target) as target_db:
        source_db.backup(target_db)
    with sqlite3.connect(target) as check_db:
        result = check_db.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        target.unlink(missing_ok=True)
        raise RuntimeError("backup integrity check failed")
    print(target)


if __name__ == "__main__":
    main()

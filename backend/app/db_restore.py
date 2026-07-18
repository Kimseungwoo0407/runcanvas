from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from pathlib import Path

from app.config import get_settings
from app.db_backup import sqlite_path


def _integrity(path: Path) -> str:
    with sqlite3.connect(path) as database:
        row = database.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing result"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m app.db_restore /restore/source.db")
    source = Path(sys.argv[1]).resolve()
    if not source.is_file():
        raise RuntimeError("source backup does not exist")
    if _integrity(source) != "ok":
        raise RuntimeError("source backup integrity check failed")

    target = sqlite_path(get_settings().DATABASE_URL).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.restore.tmp")
    temporary.unlink(missing_ok=True)
    shutil.copy2(source, temporary)
    if _integrity(temporary) != "ok":
        temporary.unlink(missing_ok=True)
        raise RuntimeError("copied backup integrity check failed")

    Path(f"{target}-wal").unlink(missing_ok=True)
    Path(f"{target}-shm").unlink(missing_ok=True)
    os.replace(temporary, target)
    print(target)


if __name__ == "__main__":
    main()

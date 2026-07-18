from __future__ import annotations

import sqlite3

from app.config import get_settings
from app.db_backup import sqlite_path


def main() -> None:
    path = sqlite_path(get_settings().DATABASE_URL)
    with sqlite3.connect(path) as db:
        result = db.execute("PRAGMA integrity_check").fetchone()
        users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        courses = db.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if not result or result[0] != "ok":
        raise RuntimeError("database integrity check failed")
    print({"integrity": "ok", "users": users, "courses": courses})


if __name__ == "__main__":
    main()

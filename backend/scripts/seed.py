#!/usr/bin/env python
"""Create / reset the SQLite database with the fictional seed data.

Usage (from backend/):
    python scripts/seed.py            # seed only if the database is empty
    python scripts/seed.py --reset    # wipe all tables and re-seed (deterministic)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.db import connect, init_db  # noqa: E402
from app.seeding import reset_database, seed_if_empty  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete all rows first")
    parser.add_argument("--db", type=Path, default=None, help="override database path")
    args = parser.parse_args()

    settings = Settings.from_env()
    db_path = args.db or settings.db_path
    conn = connect(db_path)
    init_db(conn)
    if args.reset:
        print("Reset and seeded:", reset_database(conn))
    else:
        print("Seeded fresh database." if seed_if_empty(conn) else "Database already has data; use --reset to rebuild.")
    print(f"Database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

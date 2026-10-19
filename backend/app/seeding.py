"""Reproducible seeding. The seed lists are static Python data, so every run produces identical rows."""
from __future__ import annotations

import sqlite3

from . import repository as repo
from .data.candidates import DEMO_PROFILE, SEED_CANDIDATES
from .data.jobs import SEED_JOBS

SEED_TIMESTAMP = "2026-01-15T09:00:00+00:00"  # fixed so seeded rows are byte-for-byte reproducible


def seed_database(conn: sqlite3.Connection) -> dict[str, int]:
    for job in SEED_JOBS:
        repo.insert_job(conn, job, synthetic=True, created_at=SEED_TIMESTAMP)
    for cand in SEED_CANDIDATES:
        repo.insert_candidate(conn, cand, synthetic=True)  # ids 1..N, in seed order
    repo.insert_candidate(conn, DEMO_PROFILE, user_profile=True, synthetic=True)
    return {"jobs": len(SEED_JOBS), "candidates": len(SEED_CANDIDATES), "profiles": 1}


def seed_if_empty(conn: sqlite3.Connection) -> bool:
    if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0 and conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0:
        seed_database(conn)
        return True
    return False


def reset_database(conn: sqlite3.Connection) -> dict[str, int]:
    for table in ("applications", "jobs", "candidates", "meta"):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('jobs','candidates')")
    conn.commit()
    return seed_database(conn)

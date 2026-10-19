"""SQLite connection helpers and schema."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    work_mode TEXT NOT NULL CHECK (work_mode IN ('remote','hybrid','onsite')),
    employment_type TEXT NOT NULL DEFAULT 'full-time',
    seniority TEXT CHECK (seniority IS NULL OR seniority IN ('junior','mid','senior','lead')),
    min_years REAL,
    max_years REAL,
    salary_min INTEGER,
    salary_max INTEGER,
    role_family TEXT,
    description TEXT NOT NULL,
    required_skills TEXT NOT NULL DEFAULT '[]',
    preferred_skills TEXT NOT NULL DEFAULT '[]',
    is_synthetic INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    headline TEXT NOT NULL,
    location TEXT,
    years_experience REAL,
    skills TEXT NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    desired_titles TEXT NOT NULL DEFAULT '[]',
    preferred_locations TEXT NOT NULL DEFAULT '[]',
    preferred_work_modes TEXT NOT NULL DEFAULT '[]',
    open_to_relocation INTEGER NOT NULL DEFAULT 0,
    is_user_profile INTEGER NOT NULL DEFAULT 0,
    is_synthetic INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    job_id INTEGER PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('saved','applied','interviewing','offer','rejected','withdrawn')),
    notes TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    if str(db_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

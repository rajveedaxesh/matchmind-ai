"""Data-access layer (plain SQL over sqlite3). Returns plain dicts with JSON columns decoded."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

from .ml.skills import normalize_skill, normalize_skills

JOB_JSON = ("required_skills", "preferred_skills")
CAND_JSON = ("skills", "desired_titles", "preferred_locations", "preferred_work_modes")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row, json_cols: Iterable[str]) -> dict[str, Any]:
    d = dict(row)
    for col in json_cols:
        d[col] = json.loads(d[col]) if d.get(col) else []
    if "is_synthetic" in d:
        d["is_synthetic"] = bool(d["is_synthetic"])
    if "open_to_relocation" in d:
        d["open_to_relocation"] = bool(d["open_to_relocation"])
    return d


# ------------------------------------------------------------------- data version
def get_data_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM meta WHERE key = 'data_version'").fetchone()
    return int(row["value"]) if row else 0


def bump_data_version(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('data_version', '1') "
        "ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1"
    )


# ------------------------------------------------------------------------- jobs
_JOB_COLS = (
    "title", "company", "location", "work_mode", "employment_type", "seniority", "min_years", "max_years",
    "salary_min", "salary_max", "role_family", "description", "required_skills", "preferred_skills",
)


def insert_job(conn: sqlite3.Connection, data: dict[str, Any], synthetic: bool = False, created_at: str | None = None) -> int:
    values = [json.dumps(data.get(c) or []) if c in JOB_JSON else data.get(c) for c in _JOB_COLS]
    cur = conn.execute(
        f"INSERT INTO jobs ({', '.join(_JOB_COLS)}, is_synthetic, created_at) VALUES ({', '.join('?' * (len(_JOB_COLS) + 2))})",
        (*values, 1 if synthetic else 0, created_at or now_iso()),
    )
    bump_data_version(conn)
    conn.commit()
    return int(cur.lastrowid)


def get_job(conn: sqlite3.Connection, job_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row, JOB_JSON) if row else None


def all_jobs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [_row_to_dict(r, JOB_JSON) for r in conn.execute("SELECT * FROM jobs ORDER BY id")]


def list_jobs(
    conn: sqlite3.Connection,
    q: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    seniority: str | None = None,
    employment_type: str | None = None,
    role_family: str | None = None,
    skill: str | None = None,
    min_salary: int | None = None,
    sort: str = "id",
) -> list[dict[str, Any]]:
    where, params = [], []
    for col, val in (("work_mode", work_mode), ("seniority", seniority), ("employment_type", employment_type), ("role_family", role_family)):
        if val:
            where.append(f"{col} = ?")
            params.append(val)
    if location:
        where.append("LOWER(location) LIKE ?")
        params.append(f"%{location.strip().lower()}%")
    if min_salary is not None:
        where.append("salary_max IS NOT NULL AND salary_max >= ?")
        params.append(min_salary)
    order = {"id": "id ASC", "title": "title COLLATE NOCASE ASC", "salary_desc": "COALESCE(salary_max, 0) DESC, id ASC", "newest": "created_at DESC, id DESC"}.get(sort, "id ASC")
    sql = "SELECT * FROM jobs" + (" WHERE " + " AND ".join(where) if where else "") + f" ORDER BY {order}"
    rows = [_row_to_dict(r, JOB_JSON) for r in conn.execute(sql, params)]

    if q and q.strip():
        needle = q.strip().lower()
        rows = [
            r for r in rows
            if needle in " ".join([r["title"], r["company"], r["description"], r["location"], *r["required_skills"], *r["preferred_skills"]]).lower()
        ]
    if skill and skill.strip():
        wanted = normalize_skill(skill)
        rows = [r for r in rows if wanted in normalize_skills(r["required_skills"] + r["preferred_skills"])]
    return rows


# -------------------------------------------------------------------- candidates
_CAND_COLS = (
    "display_name", "headline", "location", "years_experience", "skills", "summary", "desired_titles",
    "preferred_locations", "preferred_work_modes", "open_to_relocation",
)


def insert_candidate(conn: sqlite3.Connection, data: dict[str, Any], user_profile: bool = False, synthetic: bool = True) -> int:
    values = [json.dumps(data.get(c) or []) if c in CAND_JSON else data.get(c) for c in _CAND_COLS]
    values[_CAND_COLS.index("open_to_relocation")] = 1 if data.get("open_to_relocation") else 0
    values[_CAND_COLS.index("summary")] = data.get("summary") or ""
    cur = conn.execute(
        f"INSERT INTO candidates ({', '.join(_CAND_COLS)}, is_user_profile, is_synthetic, updated_at) "
        f"VALUES ({', '.join('?' * (len(_CAND_COLS) + 3))})",
        (*values, 1 if user_profile else 0, 1 if synthetic else 0, now_iso()),
    )
    bump_data_version(conn)
    conn.commit()
    return int(cur.lastrowid)


def get_candidate(conn: sqlite3.Connection, candidate_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM candidates WHERE id = ? AND is_user_profile = 0", (candidate_id,)).fetchone()
    return _row_to_dict(row, CAND_JSON) if row else None


def all_candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every candidate row including the user's own profile (used to fit the text models)."""
    return [_row_to_dict(r, CAND_JSON) for r in conn.execute("SELECT * FROM candidates ORDER BY id")]


def candidate_pool(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [_row_to_dict(r, CAND_JSON) for r in conn.execute("SELECT * FROM candidates WHERE is_user_profile = 0 ORDER BY id")]


def get_profile(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM candidates WHERE is_user_profile = 1 ORDER BY id LIMIT 1").fetchone()
    return _row_to_dict(row, CAND_JSON) if row else None


def update_profile(conn: sqlite3.Connection, data: dict[str, Any]) -> dict[str, Any]:
    current = get_profile(conn)
    if current is None:
        pid = insert_candidate(conn, {**data, "display_name": data.get("display_name") or "My profile"}, user_profile=True)
        return get_profile(conn)  # type: ignore[return-value]
    merged = {**current, **{k: v for k, v in data.items() if k in _CAND_COLS and (k != "display_name" or v)}}
    sets = ", ".join(f"{c} = ?" for c in _CAND_COLS)
    values = [json.dumps(merged.get(c) or []) if c in CAND_JSON else merged.get(c) for c in _CAND_COLS]
    values[_CAND_COLS.index("open_to_relocation")] = 1 if merged.get("open_to_relocation") else 0
    values[_CAND_COLS.index("summary")] = merged.get("summary") or ""
    conn.execute(f"UPDATE candidates SET {sets}, updated_at = ? WHERE id = ?", (*values, now_iso(), current["id"]))
    bump_data_version(conn)
    conn.commit()
    return get_profile(conn)  # type: ignore[return-value]


# ------------------------------------------------------------------ applications
def application_statuses(conn: sqlite3.Connection) -> dict[int, str]:
    return {r["job_id"]: r["status"] for r in conn.execute("SELECT job_id, status FROM applications")}


def list_applications(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute("SELECT * FROM applications ORDER BY updated_at DESC, job_id")]


def get_application(conn: sqlite3.Connection, job_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def upsert_application(conn: sqlite3.Connection, job_id: int, status: str, notes: str | None) -> dict[str, Any]:
    conn.execute(
        "INSERT INTO applications(job_id, status, notes, updated_at) VALUES(?, ?, ?, ?) "
        "ON CONFLICT(job_id) DO UPDATE SET status = excluded.status, "
        "notes = COALESCE(excluded.notes, applications.notes), updated_at = excluded.updated_at",
        (job_id, status, notes, now_iso()),
    )
    conn.commit()
    return get_application(conn, job_id)  # type: ignore[return-value]


def delete_application(conn: sqlite3.Connection, job_id: int) -> bool:
    cur = conn.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
    conn.commit()
    return cur.rowcount > 0


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "candidates": conn.execute("SELECT COUNT(*) FROM candidates WHERE is_user_profile = 0").fetchone()[0],
        "applications": conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
    }

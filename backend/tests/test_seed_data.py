"""Seed data volume, quality, reproducibility and synthetic labelling."""
import re
import sqlite3

from app.data.candidates import DEMO_PROFILE, SEED_CANDIDATES
from app.data.jobs import SEED_JOBS
from app.data.families import FAMILIES
from app.db import connect, init_db
from app.ml.skills import is_known_skill
from app.ml.types import PROTECTED_ATTRIBUTE_TERMS
from app.seeding import reset_database, seed_database


def test_minimum_volume():
    assert len(SEED_JOBS) >= 25
    assert len(SEED_CANDIDATES) >= 15


def test_jobs_are_well_formed():
    for j in SEED_JOBS:
        assert j["required_skills"] and j["description"] and j["title"]
        assert j["role_family"] in FAMILIES
        assert j["min_years"] <= j["max_years"] and j["salary_min"] <= j["salary_max"]
        for s in j["required_skills"] + j["preferred_skills"]:
            assert is_known_skill(s), f"unknown skill in taxonomy: {s}"
    assert len({(j["title"], j["company"], j["location"]) for j in SEED_JOBS}) == len(SEED_JOBS)


def test_candidates_are_well_formed_and_fictional():
    for c in SEED_CANDIDATES:
        assert c["display_name"].startswith("Candidate ")  # neutral code names, no personal names
        assert c["family"] in FAMILIES
        assert len(c["skills"]) >= 4
        assert not (set(c) & set(PROTECTED_ATTRIBUTE_TERMS))
        for s in c["skills"]:
            assert is_known_skill(s), f"unknown skill in taxonomy: {s}"
        assert not re.search(r"@|\d{3}[- ]\d{3}", c["summary"])  # no emails / phone numbers
    assert not (set(DEMO_PROFILE) & set(PROTECTED_ATTRIBUTE_TERMS))


def test_seeding_is_reproducible(tmp_path):
    def snapshot(path):
        conn = connect(path)
        init_db(conn)
        seed_database(conn)
        data = [tuple(r) for r in conn.execute("SELECT * FROM jobs ORDER BY id")]
        data += [tuple(r)[:-1] for r in conn.execute("SELECT * FROM candidates ORDER BY id")]  # drop updated_at timestamp
        conn.close()
        return data

    assert snapshot(tmp_path / "a.db") == snapshot(tmp_path / "b.db")


def test_reset_rebuilds_identical_counts(tmp_path):
    conn = connect(tmp_path / "r.db")
    init_db(conn)
    seed_database(conn)
    conn.execute("DELETE FROM jobs WHERE id <= 5")
    conn.commit()
    result = reset_database(conn)
    assert result == {"jobs": len(SEED_JOBS), "candidates": len(SEED_CANDIDATES), "profiles": 1}
    assert conn.execute("SELECT MIN(id) FROM jobs").fetchone()[0] == 1
    conn.close()


def test_all_seed_rows_flagged_synthetic(client):
    jobs = client.get("/api/jobs?limit=100").json()["items"]
    assert jobs and all(j["is_synthetic"] for j in jobs)
    cands = client.get("/api/candidates").json()
    assert cands and all(c["is_synthetic"] for c in cands)

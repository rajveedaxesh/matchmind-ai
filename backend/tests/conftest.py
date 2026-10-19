from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore", message=".*httpx.*")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.data.adapters import to_candidate_profile, to_job_posting  # noqa: E402
from app.data.candidates import SEED_CANDIDATES  # noqa: E402
from app.data.jobs import SEED_JOBS  # noqa: E402
from app.main import create_app  # noqa: E402
from app.ml import HybridMatcher  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    settings = Settings(db_path=tmp_path / "test.db", frontend_dist=tmp_path / "no-dist")
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture(scope="session")
def seed_jobs():
    return [to_job_posting(d, job_id=i + 1) for i, d in enumerate(SEED_JOBS)]


@pytest.fixture(scope="session")
def seed_candidates():
    return [to_candidate_profile(d, candidate_id=i + 1) for i, d in enumerate(SEED_CANDIDATES)]


@pytest.fixture(scope="session")
def matcher(seed_jobs, seed_candidates):
    return HybridMatcher.from_entities(seed_jobs, seed_candidates)

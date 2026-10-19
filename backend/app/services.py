"""Application services shared by the routers: matcher lifecycle and small helpers."""
from __future__ import annotations

import sqlite3
import threading
from typing import Any

from . import repository as repo
from .config import Settings
from .data.adapters import to_candidate_profile, to_job_posting
from .ml import HybridMatcher, TfidfBaseline


class MatchingService:
    """Builds the fitted matcher from the database and rebuilds it only when the data changed."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._version: int | None = None
        self._matcher: HybridMatcher | None = None
        self._baseline: TfidfBaseline | None = None

    def get(self, conn: sqlite3.Connection) -> tuple[HybridMatcher, TfidfBaseline]:
        version = repo.get_data_version(conn)
        with self._lock:
            if self._matcher is None or version != self._version:
                jobs = [to_job_posting(j) for j in repo.all_jobs(conn)]
                cands = [to_candidate_profile(c) for c in repo.all_candidates(conn)]
                self._matcher = HybridMatcher.from_entities(
                    jobs, cands, encoder_backend=self._settings.embedding_backend, st_model=self._settings.st_model
                )
                self._baseline = TfidfBaseline(self._matcher)
                self._version = version
            assert self._baseline is not None
            return self._matcher, self._baseline


def profile_completeness(profile: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "Add at least 3 skills": len(profile.get("skills") or []) >= 3,
        "Write a short summary (40+ characters)": len((profile.get("summary") or "").strip()) >= 40,
        "Enter your years of experience": profile.get("years_experience") is not None,
        "Add at least one desired job title": bool(profile.get("desired_titles")),
        "Set a location or work-mode preference": bool(profile.get("preferred_locations") or profile.get("preferred_work_modes")),
    }
    done = sum(checks.values())
    return {"percent": round(100 * done / len(checks)), "missing": [k for k, ok in checks.items() if not ok]}


def profile_warnings(profile: dict[str, Any]) -> list[str]:
    warnings = []
    if not profile.get("skills"):
        warnings.append("Your profile lists no skills, so skill matching is scored as 0. Add skills for better recommendations.")
    if profile.get("years_experience") is None:
        warnings.append("Years of experience not set: experience fit is left out of your scores.")
    if not (profile.get("preferred_locations") or profile.get("preferred_work_modes")):
        warnings.append("No location or work-mode preference set: location is left out of your scores.")
    return warnings

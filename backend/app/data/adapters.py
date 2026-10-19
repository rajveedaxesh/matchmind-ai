"""Map plain dicts / DB rows onto the framework-free engine types.

This is the single choke-point where data enters the matcher, and it only copies job-relevant
fields. Names, ids-as-labels, synthetic flags and any other column are deliberately dropped.
"""
from __future__ import annotations

from typing import Any, Mapping

from ..ml.types import CandidateProfile, JobPosting


def to_job_posting(row: Mapping[str, Any], job_id: Any = None) -> JobPosting:
    return JobPosting(
        id=row.get("id") if job_id is None else job_id,
        title=row.get("title") or "",
        description=row.get("description") or "",
        required_skills=tuple(row.get("required_skills") or ()),
        preferred_skills=tuple(row.get("preferred_skills") or ()),
        min_years=row.get("min_years"),
        max_years=row.get("max_years"),
        seniority=row.get("seniority"),
        location=row.get("location"),
        work_mode=row.get("work_mode"),
    )


def to_candidate_profile(row: Mapping[str, Any], candidate_id: Any = None) -> CandidateProfile:
    return CandidateProfile(
        id=row.get("id") if candidate_id is None else candidate_id,
        headline=row.get("headline") or "",
        summary=row.get("summary") or "",
        skills=tuple(row.get("skills") or ()),
        years_experience=row.get("years_experience"),
        desired_titles=tuple(row.get("desired_titles") or ()),
        preferred_locations=tuple(row.get("preferred_locations") or ()),
        preferred_work_modes=tuple(row.get("preferred_work_modes") or ()),
        open_to_relocation=bool(row.get("open_to_relocation")),
    )

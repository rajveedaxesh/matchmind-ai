from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from .. import repository as repo
from ..data.adapters import to_candidate_profile, to_job_posting
from ..dependencies import get_conn, get_matchers
from ..ml.skills import extract_skills, normalize_skills
from ..ml.types import JobPosting
from ..schemas import (
    CandidateOut,
    CandidateRanking,
    JobSummary,
    MatchOut,
    RecruiterMatchRequest,
    RecruiterMatchResponse,
)

router = APIRouter(prefix="/api/recruiter", tags=["recruiter"])


@router.post("/match", response_model=RecruiterMatchResponse)
def match_candidates(
    req: RecruiterMatchRequest,
    conn: sqlite3.Connection = Depends(get_conn),
    matchers=Depends(get_matchers),
) -> RecruiterMatchResponse:
    """Rank the fictional candidate pool for a stored job (job_id) or an ad-hoc description (job)."""
    matcher, baseline = matchers
    company: str | None
    if req.job_id is not None:
        row = repo.get_job(conn, req.job_id)
        if row is None:
            raise HTTPException(404, f"Job {req.job_id} not found")
        posting = to_job_posting(row)
        company, job_id = row["company"], row["id"]
    else:
        ad = req.job
        assert ad is not None
        posting = JobPosting(
            id=-1,
            title=ad.title,
            description=ad.description,
            required_skills=tuple(ad.required_skills),
            preferred_skills=tuple(ad.preferred_skills),
            min_years=ad.min_years,
            max_years=ad.max_years,
            seniority=ad.seniority,
            location=ad.location,
            work_mode=ad.work_mode,
        )
        company, job_id = ad.company, None

    required = normalize_skills(posting.required_skills)
    inferred = False
    if not required:
        required = extract_skills(f"{posting.title}. {posting.description}")
        inferred = bool(required)

    pool_rows = repo.candidate_pool(conn)
    by_id = {r["id"]: r for r in pool_rows}
    profiles = [to_candidate_profile(r) for r in pool_rows]
    if req.method == "tfidf":
        ranked = baseline.rank_candidates(posting, profiles)
    else:
        ranked = matcher.rank_candidates(posting, profiles, infer_job_skills=True)
    kept = [item for item in ranked if item.result.score >= req.min_score]
    items = [
        CandidateRanking(rank=i + 1, candidate=CandidateOut(**by_id[item.id]), match=MatchOut.from_result(item.result))
        for i, item in enumerate(kept[: req.limit])
    ]
    return RecruiterMatchResponse(
        job=JobSummary(
            id=job_id,
            title=posting.title,
            company=company,
            required_skills=required,
            preferred_skills=normalize_skills(posting.preferred_skills),
            skills_inferred_from_text=inferred,
        ),
        method=req.method,
        total_candidates=len(profiles),
        total_returned=len(items),
        items=items,
        weights=matcher.weights,
    )

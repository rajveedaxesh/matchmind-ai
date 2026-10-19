from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repository as repo
from ..data.adapters import to_candidate_profile, to_job_posting
from ..dependencies import get_conn, get_matchers
from ..schemas import JobOut, JobRecommendation, Method, RecommendationList, MatchOut, WorkMode
from ..services import profile_warnings

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _profile_or_404(conn: sqlite3.Connection) -> dict:
    profile = repo.get_profile(conn)
    if profile is None:
        raise HTTPException(404, "No job-seeker profile exists yet. Create one with PUT /api/profile.")
    return profile


@router.get("", response_model=RecommendationList)
def recommend_jobs(
    limit: int = Query(10, ge=1, le=50),
    method: Method = "hybrid",
    work_mode: WorkMode | None = None,
    location: str | None = Query(None, max_length=100),
    min_score: float = Query(0, ge=0, le=100),
    conn: sqlite3.Connection = Depends(get_conn),
    matchers=Depends(get_matchers),
) -> RecommendationList:
    matcher, baseline = matchers
    profile_row = _profile_or_404(conn)
    profile = to_candidate_profile(profile_row)

    rows = repo.all_jobs(conn)
    if work_mode:
        rows = [r for r in rows if r["work_mode"] == work_mode]
    if location:
        rows = [r for r in rows if location.strip().lower() in r["location"].lower()]
    by_id = {r["id"]: r for r in rows}
    postings = [to_job_posting(r) for r in rows]

    ranked = baseline.rank_jobs(profile, postings) if method == "tfidf" else matcher.rank_jobs(profile, postings)
    kept = [item for item in ranked if item.result.score >= min_score]
    statuses = repo.application_statuses(conn)
    items = [
        JobRecommendation(
            rank=i + 1,
            job=JobOut(**by_id[item.id], application_status=statuses.get(item.id)),
            match=MatchOut.from_result(item.result),
        )
        for i, item in enumerate(kept[:limit])
    ]
    return RecommendationList(
        method=method,
        total_scored=len(ranked),
        total_returned=len(items),
        items=items,
        weights=matcher.weights,
        warnings=profile_warnings(profile_row),
    )


@router.get("/{job_id}", response_model=JobRecommendation)
def explain_match(
    job_id: int,
    method: Method = "hybrid",
    conn: sqlite3.Connection = Depends(get_conn),
    matchers=Depends(get_matchers),
) -> JobRecommendation:
    """Detailed explanation of how the current profile matches one job (rank is among ALL jobs)."""
    matcher, baseline = matchers
    profile = to_candidate_profile(_profile_or_404(conn))
    rows = repo.all_jobs(conn)
    by_id = {r["id"]: r for r in rows}
    if job_id not in by_id:
        raise HTTPException(404, f"Job {job_id} not found")
    postings = [to_job_posting(r) for r in rows]
    ranked = baseline.rank_jobs(profile, postings) if method == "tfidf" else matcher.rank_jobs(profile, postings)
    item = next(i for i in ranked if i.id == job_id)
    return JobRecommendation(
        rank=item.rank,
        job=JobOut(**by_id[job_id], application_status=repo.application_statuses(conn).get(job_id)),
        match=MatchOut.from_result(item.result),
    )

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response

from .. import repository as repo
from ..data.adapters import to_candidate_profile, to_job_posting
from ..dependencies import get_conn, get_matchers
from ..schemas import ApplicationList, ApplicationOut, ApplicationUpdate, JobOut, MatchOut

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _build(conn: sqlite3.Connection, app_row: dict, matchers) -> ApplicationOut:
    job = repo.get_job(conn, app_row["job_id"])
    assert job is not None
    match = None
    profile = repo.get_profile(conn)
    if profile is not None:
        matcher, _ = matchers
        match = MatchOut.from_result(matcher.score(to_candidate_profile(profile), to_job_posting(job)))
    return ApplicationOut(
        job=JobOut(**job, application_status=app_row["status"]),
        status=app_row["status"],
        notes=app_row["notes"],
        updated_at=app_row["updated_at"],
        match=match,
    )


@router.get("", response_model=ApplicationList)
def list_applications(conn: sqlite3.Connection = Depends(get_conn), matchers=Depends(get_matchers)) -> ApplicationList:
    rows = repo.list_applications(conn)
    items = [_build(conn, r, matchers) for r in rows]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return ApplicationList(items=items, counts=counts)


@router.put("/{job_id}", response_model=ApplicationOut)
def save_or_update(
    job_id: int,
    payload: ApplicationUpdate,
    conn: sqlite3.Connection = Depends(get_conn),
    matchers=Depends(get_matchers),
) -> ApplicationOut:
    if repo.get_job(conn, job_id) is None:
        raise HTTPException(404, f"Job {job_id} not found")
    row = repo.upsert_application(conn, job_id, payload.status, payload.notes)
    return _build(conn, row, matchers)


@router.delete("/{job_id}", status_code=204)
def remove(job_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> Response:
    if not repo.delete_application(conn, job_id):
        raise HTTPException(404, f"No saved application for job {job_id}")
    return Response(status_code=204)

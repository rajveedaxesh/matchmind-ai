from __future__ import annotations

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repository as repo
from ..dependencies import get_conn
from ..schemas import EmploymentType, JobCreate, JobList, JobOut, Seniority, WorkMode

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobList)
def list_jobs(
    q: str | None = Query(None, max_length=100, description="Search title, company, description, skills"),
    location: str | None = Query(None, max_length=100),
    work_mode: WorkMode | None = None,
    seniority: Seniority | None = None,
    employment_type: EmploymentType | None = None,
    role_family: str | None = Query(None, max_length=40),
    skill: str | None = Query(None, max_length=60),
    min_salary: int | None = Query(None, ge=0),
    sort: Literal["id", "title", "salary_desc", "newest"] = "id",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_conn),
) -> JobList:
    rows = repo.list_jobs(conn, q, location, work_mode, seniority, employment_type, role_family, skill, min_salary, sort)
    statuses = repo.application_statuses(conn)
    page = rows[offset : offset + limit]
    return JobList(
        items=[JobOut(**r, application_status=statuses.get(r["id"])) for r in page],
        total=len(rows),
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> JobOut:
    row = repo.get_job(conn, job_id)
    if row is None:
        raise HTTPException(404, f"Job {job_id} not found")
    return JobOut(**row, application_status=repo.application_statuses(conn).get(job_id))


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, conn: sqlite3.Connection = Depends(get_conn)) -> JobOut:
    job_id = repo.insert_job(conn, payload.model_dump(), synthetic=False)
    return JobOut(**repo.get_job(conn, job_id))  # type: ignore[arg-type]

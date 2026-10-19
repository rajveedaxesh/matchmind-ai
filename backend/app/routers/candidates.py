from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repository as repo
from ..dependencies import get_conn
from ..schemas import CandidateOut

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("", response_model=list[CandidateOut])
def list_candidates(
    q: str | None = Query(None, max_length=100),
    conn: sqlite3.Connection = Depends(get_conn),
) -> list[CandidateOut]:
    rows = repo.candidate_pool(conn)
    if q and q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows if needle in " ".join([r["headline"], r["summary"], *r["skills"]]).lower()]
    return [CandidateOut(**r) for r in rows]


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> CandidateOut:
    row = repo.get_candidate(conn, candidate_id)
    if row is None:
        raise HTTPException(404, f"Candidate {candidate_id} not found")
    return CandidateOut(**row)

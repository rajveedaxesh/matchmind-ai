from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from .. import repository as repo
from ..dependencies import get_conn
from ..schemas import ProfileIn, ProfileOut
from ..services import profile_completeness

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _out(row: dict) -> ProfileOut:
    return ProfileOut(**row, completeness=profile_completeness(row))


@router.get("", response_model=ProfileOut)
def get_profile(conn: sqlite3.Connection = Depends(get_conn)) -> ProfileOut:
    row = repo.get_profile(conn)
    if row is None:  # fresh install without seed data: create an empty profile on first read
        row = repo.update_profile(conn, {"display_name": "My profile", "headline": "New job seeker"})
    return _out(row)


@router.put("", response_model=ProfileOut)
def put_profile(payload: ProfileIn, conn: sqlite3.Connection = Depends(get_conn)) -> ProfileOut:
    row = repo.update_profile(conn, payload.model_dump())
    return _out(row)

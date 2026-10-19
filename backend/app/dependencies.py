from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, Request

from .db import connect
from .ml import HybridMatcher, TfidfBaseline
from .services import MatchingService


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_matchers(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> tuple[HybridMatcher, TfidfBaseline]:
    service: MatchingService = request.app.state.matching
    return service.get(conn)

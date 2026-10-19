from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from .. import repository as repo
from ..dependencies import get_conn, get_matchers
from ..ml.explain import FIT_BANDS
from ..ml.matcher import COMPONENT_LABELS
from ..ml.skills import all_known_skills
from ..ml.types import DISCLAIMER

router = APIRouter(prefix="/api", tags=["meta"])

DATA_NOTICE = (
    "All jobs, companies, candidates and relevance labels in this app are FICTIONAL, synthetic demonstration data."
)


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/meta")
def meta(conn: sqlite3.Connection = Depends(get_conn), matchers=Depends(get_matchers)) -> dict:
    matcher, _ = matchers
    return {
        "app": "MatchMind AI",
        "version": "1.0.0",
        "synthetic_data": True,
        "data_notice": DATA_NOTICE,
        "disclaimer": DISCLAIMER,
        "counts": repo.counts(conn),
        "weights": matcher.weights,
        "component_labels": COMPONENT_LABELS,
        "fit_bands": [{"min_score": t, "label": label} for t, label in FIT_BANDS],
        "embedding_backend": matcher.text.backend_name,
        "embedding_fallback_reason": matcher.text.fallback_reason,
    }


@router.get("/skills")
def skills() -> dict:
    return {"skills": all_known_skills()}

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Query

from ..evaluation.runner import run_evaluation

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@lru_cache(maxsize=8)
def _cached(seed: int, generated_per_family: int) -> dict:
    return run_evaluation(seed=seed, generated_per_family=generated_per_family)


@router.get("")
def evaluation(
    seed: int = Query(42, ge=0, le=100_000),
    generated_per_family: int = Query(8, ge=0, le=15, description="extra synthetic candidates per role family"),
) -> dict:
    """Runs the real evaluation code (cached per parameter set). Same code path as scripts/evaluate.py."""
    return _cached(seed, generated_per_family)

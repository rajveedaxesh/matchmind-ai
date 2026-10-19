"""Ranking metrics, implemented from scratch so they can be unit-tested against hand calculations.

Every function takes ``grades``: the graded relevance labels (0, 1, 2, 3 ...) of ALL candidate items
in the order the system ranked them (best first). A grade >= ``threshold`` counts as "relevant" for
the binary metrics (Precision@K, Recall@K, MRR); NDCG uses the graded gains (2^g - 1).

Metrics that are undefined for a query (no relevant items) return ``None``; the runner skips those
queries and reports how many were skipped.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

DEFAULT_THRESHOLD = 2


def _check_k(k: int) -> None:
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def precision_at_k(grades: Sequence[int], k: int, threshold: int = DEFAULT_THRESHOLD) -> float:
    """Fraction of the top-k that is relevant (denominator is always k)."""
    _check_k(k)
    return sum(1 for g in grades[:k] if g >= threshold) / k


def recall_at_k(grades: Sequence[int], k: int, threshold: int = DEFAULT_THRESHOLD) -> float | None:
    """Fraction of ALL relevant items that appear in the top-k. None if there are no relevant items."""
    _check_k(k)
    total = sum(1 for g in grades if g >= threshold)
    if total == 0:
        return None
    return sum(1 for g in grades[:k] if g >= threshold) / total


def reciprocal_rank(grades: Sequence[int], threshold: int = DEFAULT_THRESHOLD) -> float | None:
    """1 / rank of the first relevant item. None if there is none."""
    for i, g in enumerate(grades):
        if g >= threshold:
            return 1.0 / (i + 1)
    return None


def dcg_at_k(grades: Sequence[int], k: int) -> float:
    _check_k(k)
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))


def ndcg_at_k(grades: Sequence[int], k: int) -> float | None:
    """DCG@k divided by the best achievable DCG@k for the same items. None if no item has gain."""
    _check_k(k)
    ideal = dcg_at_k(sorted(grades, reverse=True), k)
    if ideal == 0:
        return None
    return dcg_at_k(grades, k) / ideal


def evaluate_ranking(
    grades: Sequence[int], ks: Sequence[int] = (3, 5, 10), threshold: int = DEFAULT_THRESHOLD
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for k in ks:
        out[f"precision@{k}"] = precision_at_k(grades, k, threshold)
        out[f"recall@{k}"] = recall_at_k(grades, k, threshold)
        out[f"ndcg@{k}"] = ndcg_at_k(grades, k)
    out["mrr"] = reciprocal_rank(grades, threshold)
    return out


def bootstrap_ci(values: Sequence[float], n_boot: int = 1000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float, float]:
    """Mean and percentile-bootstrap confidence interval over per-query values."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    means = arr[idx].mean(axis=1)
    return float(arr.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))

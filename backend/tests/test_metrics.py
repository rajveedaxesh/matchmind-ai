"""Ranking metrics checked against hand-computed values."""
import math

import pytest

from app.evaluation.metrics import (
    bootstrap_ci,
    dcg_at_k,
    evaluate_ranking,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

# ranked grades, threshold 2 -> relevant at positions 1, 3 and 6 (of 3 relevant total)
GRADES = [3, 0, 2, 1, 0, 2]


def test_precision_at_k_hand_computed():
    assert precision_at_k(GRADES, 1) == 1.0
    assert precision_at_k(GRADES, 3) == pytest.approx(2 / 3)
    assert precision_at_k(GRADES, 6) == pytest.approx(3 / 6)


def test_precision_denominator_is_k_even_when_list_shorter():
    assert precision_at_k([3, 3], 5) == pytest.approx(2 / 5)


def test_recall_at_k_hand_computed():
    assert recall_at_k(GRADES, 1) == pytest.approx(1 / 3)
    assert recall_at_k(GRADES, 3) == pytest.approx(2 / 3)
    assert recall_at_k(GRADES, 6) == 1.0


def test_recall_undefined_without_relevant_items():
    assert recall_at_k([0, 1, 1], 3) is None


def test_reciprocal_rank():
    assert reciprocal_rank([0, 0, 2, 3]) == pytest.approx(1 / 3)
    assert reciprocal_rank([3]) == 1.0
    assert reciprocal_rank([0, 1, 1]) is None


def test_threshold_changes_what_counts_as_relevant():
    assert reciprocal_rank([1, 0, 3], threshold=1) == 1.0
    assert reciprocal_rank([1, 0, 3], threshold=2) == pytest.approx(1 / 3)


def test_dcg_hand_computed():
    # gains 2^g-1: [7, 0, 3]; discounts 1, 1/log2(3), 1/2
    expected = 7 + 0 + 3 / math.log2(4)
    assert dcg_at_k([3, 0, 2], 3) == pytest.approx(expected)


def test_ndcg_is_one_for_ideal_order_and_lower_otherwise():
    assert ndcg_at_k([3, 2, 1, 0], 4) == pytest.approx(1.0)
    worse = ndcg_at_k([0, 1, 2, 3], 4)
    assert 0 < worse < 1


def test_ndcg_hand_computed():
    grades = [1, 3]  # ideal order is [3, 1]
    dcg = 1 / 1 + 7 / math.log2(3)
    ideal = 7 / 1 + 1 / math.log2(3)
    assert ndcg_at_k(grades, 2) == pytest.approx(dcg / ideal)


def test_ndcg_undefined_when_all_zero():
    assert ndcg_at_k([0, 0, 0], 3) is None


@pytest.mark.parametrize("fn", [precision_at_k, recall_at_k, ndcg_at_k, dcg_at_k])
@pytest.mark.parametrize("bad_k", [0, -1])
def test_invalid_k_rejected(fn, bad_k):
    with pytest.raises(ValueError):
        fn([1, 2, 3], bad_k)


def test_metrics_stay_within_unit_interval():
    for grades in ([0, 0, 3, 2, 1], [3, 3, 3], [2], [1, 0, 0, 2]):
        out = evaluate_ranking(grades, ks=(1, 3, 5))
        for value in out.values():
            assert value is None or 0.0 <= value <= 1.0


def test_evaluate_ranking_keys():
    out = evaluate_ranking(GRADES, ks=(3, 5))
    assert set(out) == {"precision@3", "recall@3", "ndcg@3", "precision@5", "recall@5", "ndcg@5", "mrr"}


def test_bootstrap_ci_contains_mean_and_is_deterministic():
    values = [0.2, 0.4, 0.6, 0.8, 1.0]
    mean, lo, hi = bootstrap_ci(values, n_boot=500, seed=1)
    assert mean == pytest.approx(0.6)
    assert lo <= mean <= hi
    assert bootstrap_ci(values, n_boot=500, seed=1) == (mean, lo, hi)


def test_bootstrap_ci_empty_is_nan():
    assert all(math.isnan(v) for v in bootstrap_ci([]))

"""Runs every ranking method over the synthetic benchmark and aggregates real metrics."""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Callable, Sequence

from ..ml import HybridMatcher, TfidfBaseline
from ..ml.types import CandidateProfile, JobPosting
from .metrics import DEFAULT_THRESHOLD, bootstrap_ci, evaluate_ranking
from .synthetic import LABEL_DEFINITION, EvalPopulation, build_population

Scorer = Callable[[CandidateProfile, JobPosting], float]

METHOD_INFO = {
    "random": ("Random (seeded)", "Pseudo-random order; the floor every real method should beat."),
    "tfidf": ("TF-IDF baseline", "Cosine similarity of TF-IDF vectors of profile text vs job text only."),
    "text_semantic": ("TF-IDF + semantic (LSA)", "Text-only: blends TF-IDF cosine with a local LSA embedding cosine."),
    "skills_only": ("Skills only", "75% required-skill coverage + 25% preferred-skill overlap; no text."),
    "hybrid": ("Hybrid (MatchMind)", "Required + preferred skills, text (TF-IDF+semantic), role, experience and location."),
}
DIRECTIONS = {
    "recruiter": "Recruiter task: for each job, rank all candidates.",
    "seeker": "Job-seeker task: for each candidate, rank all jobs.",
}


def _build_scorers(pop: EvalPopulation, seed: int) -> dict[str, Scorer]:
    jobs = [j.posting for j in pop.jobs]
    cands = [c.profile for c in pop.candidates]
    hybrid = HybridMatcher.from_entities(jobs, cands)
    baseline = TfidfBaseline(hybrid)
    text_only = hybrid.with_weights({"text_similarity": 1.0})
    skills_only = hybrid.with_weights({"required_skills": 0.75, "preferred_skills": 0.25})
    scorers: dict[str, Scorer] = {
        "random": lambda c, j: random.Random(f"{seed}:{c.id}:{j.id}").random(),
        "tfidf": baseline.raw_score,
        "text_semantic": lambda c, j: text_only.score(c, j, explain=False).score,
        "skills_only": lambda c, j: skills_only.score(c, j, explain=False).score,
        "hybrid": lambda c, j: hybrid.score(c, j, explain=False).score,
    }
    return {k: _memoise(fn) for k, fn in scorers.items()}


def _per_query_metrics(
    queries: Sequence, items: Sequence, score_fn: Callable, grade_fn: Callable, ks: Sequence[int], threshold: int
) -> list[dict[str, float | None]]:
    rows = []
    for q in queries:
        scored = sorted(((score_fn(q, it), str(it.id), it) for it in items), key=lambda t: (-t[0], t[1]))
        grades = [grade_fn(q, it) for _, _, it in scored]
        rows.append(evaluate_ranking(grades, ks, threshold))
    return rows


def _memoise(fn: Scorer) -> Scorer:
    """Each (candidate, job) pair is scored once per method and reused by both ranking directions."""
    cache: dict[tuple, float] = {}

    def wrapped(c: CandidateProfile, j: JobPosting) -> float:
        key = (c.id, j.id)
        if key not in cache:
            cache[key] = fn(c, j)
        return cache[key]

    return wrapped


def run_evaluation(
    seed: int = 42,
    generated_per_family: int = 8,
    ks: Sequence[int] = (3, 5, 10),
    threshold: int = DEFAULT_THRESHOLD,
    n_boot: int = 1000,
) -> dict:
    started = time.perf_counter()
    pop = build_population(seed, generated_per_family)
    scorers = _build_scorers(pop, seed)
    jobs = [j.posting for j in pop.jobs]
    cands = [c.profile for c in pop.candidates]
    labels = pop.labels

    grade_counts = {g: 0 for g in range(4)}
    for g in labels.values():
        grade_counts[g] += 1

    directions: dict[str, dict] = {}
    for direction, description in DIRECTIONS.items():
        per_method_rows: dict[str, list[dict]] = {}
        for key, fn in scorers.items():
            if direction == "recruiter":
                rows = _per_query_metrics(jobs, cands, lambda q, it, fn=fn: fn(it, q), lambda q, it: labels[(q.id, it.id)], ks, threshold)
            else:
                rows = _per_query_metrics(cands, jobs, lambda q, it, fn=fn: fn(q, it), lambda q, it: labels[(it.id, q.id)], ks, threshold)
            per_method_rows[key] = rows
        n_queries = len(next(iter(per_method_rows.values())))
        # queries with no relevant item have undefined recall/MRR/NDCG -> skipped identically for every method
        keep = [i for i in range(n_queries) if per_method_rows["hybrid"][i]["mrr"] is not None]
        metric_names = list(per_method_rows["hybrid"][0].keys())
        methods_out = {}
        for key, rows in per_method_rows.items():
            metrics_out = {}
            for name in metric_names:
                vals = [rows[i][name] for i in keep]
                mean, lo, hi = bootstrap_ci(vals, n_boot=n_boot, seed=seed)
                metrics_out[name] = {"mean": round(mean, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4)}
            methods_out[key] = {"label": METHOD_INFO[key][0], "description": METHOD_INFO[key][1], "metrics": metrics_out}
        comparisons = []
        for name in [m for m in metric_names if m.startswith("ndcg") or m == "mrr"]:
            diffs = [per_method_rows["hybrid"][i][name] - per_method_rows["tfidf"][i][name] for i in keep]
            mean, lo, hi = bootstrap_ci(diffs, n_boot=n_boot, seed=seed + 1)
            comparisons.append({
                "metric": name, "a": "hybrid", "b": "tfidf",
                "mean_difference": round(mean, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                "ci_excludes_zero": bool(lo > 0 or hi < 0),
            })
        directions[direction] = {
            "description": description,
            "n_queries": n_queries,
            "n_queries_evaluated": len(keep),
            "n_queries_skipped_no_relevant": n_queries - len(keep),
            "ks": list(ks),
            "methods": methods_out,
            "paired_comparisons": comparisons,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_seconds": round(time.perf_counter() - started, 2),
        "synthetic": True,
        "config": {"seed": seed, "generated_per_family": generated_per_family, "ks": list(ks),
                   "relevance_threshold": threshold, "bootstrap_resamples": n_boot},
        "dataset": {
            "n_jobs": len(jobs),
            "n_candidates": len(cands),
            "n_hand_written_candidates": sum(1 for c in pop.candidates if not c.synthetic_generated),
            "n_generated_candidates": sum(1 for c in pop.candidates if c.synthetic_generated),
            "n_labelled_pairs": len(labels),
            "grade_distribution": {str(k): v for k, v in grade_counts.items()},
            "label_definition": LABEL_DEFINITION,
        },
        "directions": directions,
        "caveats": [
            "All jobs, candidates and relevance labels are synthetic and rule-generated. Results show how the pipeline works, not real hiring accuracy.",
            "Labels use concepts (skills, role family, experience) that the hybrid scorer also uses, so it has a structural advantage over the text-only baseline.",
            "Candidate profiles are small (tens to ~120), so confidence intervals are wide; read differences together with the CIs.",
            "No protected attributes (age, gender, ethnicity, photo, ...) exist in the data or are used by any method.",
        ],
    }


def to_markdown(results: dict) -> str:
    lines = [
        "# MatchMind AI - Evaluation report (synthetic data)",
        "",
        f"Generated {results['generated_at']} by `scripts/evaluate.py` in {results['runtime_seconds']}s. "
        f"Seed {results['config']['seed']}.",
        "",
        "> " + results["caveats"][0],
        "",
        f"**Dataset:** {results['dataset']['n_jobs']} jobs x {results['dataset']['n_candidates']} candidates "
        f"({results['dataset']['n_hand_written_candidates']} hand-written + {results['dataset']['n_generated_candidates']} generated), "
        f"{results['dataset']['n_labelled_pairs']} labelled pairs. Grade distribution: {results['dataset']['grade_distribution']}.",
        "",
        f"**Labels:** {results['dataset']['label_definition']}",
        "",
    ]
    for direction, d in results["directions"].items():
        ks = d["ks"]
        cols = [f"precision@{k}" for k in ks] + [f"recall@{k}" for k in ks] + [f"ndcg@{k}" for k in ks] + ["mrr"]
        lines += [f"## {direction.capitalize()} direction", "", d["description"],
                  f"Queries evaluated: {d['n_queries_evaluated']} (skipped, no relevant item: {d['n_queries_skipped_no_relevant']}).", "",
                  "| Method | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        for key, m in d["methods"].items():
            lines.append(f"| {m['label']} | " + " | ".join(f"{m['metrics'][c]['mean']:.3f}" for c in cols) + " |")
        lines += ["", "Paired difference, Hybrid minus TF-IDF baseline (95% bootstrap CI):", ""]
        for c in d["paired_comparisons"]:
            flag = "CI excludes 0" if c["ci_excludes_zero"] else "CI includes 0"
            lines.append(f"- {c['metric']}: {c['mean_difference']:+.3f} [{c['ci_low']:+.3f}, {c['ci_high']:+.3f}] ({flag})")
        lines.append("")
    lines += ["## Caveats", ""] + [f"- {c}" for c in results["caveats"]] + [""]
    return "\n".join(lines)

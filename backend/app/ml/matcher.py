"""HybridMatcher: reusable, framework-free ranking engine.

score = 100 * sum(w_i * c_i) / sum(w_i)   over the components that are *applicable*.

Components that cannot be evaluated (no location preference, job lists no preferred skills ...)
are excluded and the remaining weights are re-normalised, so missing data never silently
counts as a zero or as a perfect score. Every component and its effective weight is returned.
"""
from __future__ import annotations

import math
from typing import Hashable, Iterable, Mapping, Sequence

from .explain import build_explanations, fit_label
from .scoring import (
    Raw,
    experience_score,
    location_score,
    preferred_skills_score,
    required_skills_score,
    role_alignment_score,
)
from .similarity import TextSimilarity
from .skills import extract_skills, normalize_skills
from .types import ComponentScore, DISCLAIMER, CandidateProfile, JobPosting, MatchResult, RankedItem

COMPONENT_KEYS = (
    "required_skills",
    "preferred_skills",
    "text_similarity",
    "role_alignment",
    "experience",
    "location",
)
COMPONENT_LABELS = {
    "required_skills": "Required skills",
    "preferred_skills": "Preferred skills",
    "text_similarity": "Text similarity",
    "role_alignment": "Role alignment",
    "experience": "Experience fit",
    "location": "Location & work mode",
}
DEFAULT_WEIGHTS: dict[str, float] = {
    "required_skills": 0.30,
    "text_similarity": 0.25,
    "role_alignment": 0.15,
    "preferred_skills": 0.10,
    "experience": 0.10,
    "location": 0.10,
}


def candidate_document(c: CandidateProfile) -> str:
    """Text used for similarity. Contains only job-relevant fields (never a name)."""
    return " . ".join(p for p in (c.headline, " ".join(c.desired_titles), c.summary, " ".join(c.skills)) if p)


def job_document(j: JobPosting) -> str:
    return " . ".join(
        p for p in (j.title, j.description, " ".join(j.required_skills), " ".join(j.preferred_skills)) if p
    )


def validate_weights(weights: Mapping[str, float] | None) -> dict[str, float]:
    if weights is None:
        return dict(DEFAULT_WEIGHTS)
    unknown = set(weights) - set(COMPONENT_KEYS)
    if unknown:
        raise ValueError(f"Unknown weight keys: {sorted(unknown)}")
    cleaned = {k: float(weights.get(k, 0.0)) for k in COMPONENT_KEYS}
    if any(v < 0 or math.isnan(v) for v in cleaned.values()):
        raise ValueError("Weights must be non-negative numbers")
    if sum(cleaned.values()) <= 0:
        raise ValueError("At least one weight must be positive")
    return cleaned


class HybridMatcher:
    def __init__(
        self,
        corpus: Iterable[str] | None = None,
        weights: Mapping[str, float] | None = None,
        encoder_backend: str = "lsa",
        semantic_weight: float = 0.35,
        saturation: float = 0.40,
        st_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.weights = validate_weights(weights)
        self.text = TextSimilarity(encoder_backend, semantic_weight, saturation, st_model)
        if corpus is not None:
            self.text.fit(list(corpus))

    def with_weights(self, weights: Mapping[str, float]) -> "HybridMatcher":
        """A matcher sharing this one's fitted text models but using different component weights."""
        clone = HybridMatcher.__new__(HybridMatcher)
        clone.weights = validate_weights(weights)
        clone.text = self.text
        return clone

    @classmethod
    def from_entities(
        cls, jobs: Sequence[JobPosting], candidates: Sequence[CandidateProfile], **kwargs
    ) -> "HybridMatcher":
        corpus = [job_document(j) for j in jobs] + [candidate_document(c) for c in candidates]
        return cls(corpus, **kwargs)

    # ------------------------------------------------------------------ scoring
    def score(
        self,
        candidate: CandidateProfile,
        job: JobPosting,
        explain: bool = True,
        infer_job_skills: bool = False,
    ) -> MatchResult:
        required = normalize_skills(job.required_skills)
        preferred = [s for s in normalize_skills(job.preferred_skills) if s not in required]
        inferred = False
        if infer_job_skills and not required:
            required = extract_skills(f"{job.title}. {job.description}")
            inferred = bool(required)

        raws: dict[str, Raw] = {
            "required_skills": required_skills_score(candidate, required, inferred),
            "preferred_skills": preferred_skills_score(candidate, preferred),
            "role_alignment": role_alignment_score(candidate, job),
            "experience": experience_score(candidate, job),
            "location": location_score(candidate, job),
        }
        cdoc, jdoc = candidate_document(candidate), job_document(job)
        if cdoc.strip() and jdoc.strip():
            sim = self.text.similarity(cdoc, jdoc)
            sem = "n/a" if sim["semantic"] is None else f"{sim['semantic']:.2f}"
            raws["text_similarity"] = Raw(
                sim["score"],
                f"TF-IDF cosine {sim['tfidf']:.2f}, semantic ({self.text.backend_name}) {sem}.",
                {"sim": sim},
            )
        else:
            raws["text_similarity"] = Raw(None, "Not scored: one of the documents is empty.")

        active = {k: self.weights[k] for k in COMPONENT_KEYS if raws[k].score is not None and self.weights[k] > 0}
        total_w = sum(active.values())
        components: dict[str, ComponentScore] = {}
        total = 0.0
        for key in COMPONENT_KEYS:
            raw = raws[key]
            applicable = key in active
            eff = active[key] / total_w if applicable else 0.0
            value = float(min(1.0, max(0.0, raw.score))) if raw.score is not None else 0.0
            contribution = 100.0 * eff * value
            total += contribution
            detail = raw.detail if (applicable or raw.score is None) else "Weight set to 0 for this run."
            components[key] = ComponentScore(
                key=key,
                label=COMPONENT_LABELS[key],
                score=round(100.0 * value, 1),
                weight=round(eff, 4),
                contribution=round(contribution, 1),
                applicable=applicable,
                detail=detail,
            )
        final = round(min(100.0, max(0.0, total)), 1)

        req, pref = raws["required_skills"].extra, raws["preferred_skills"].extra
        result = MatchResult(
            score=final,
            label=fit_label(final),
            summary="",
            method="hybrid",
            components=components,
            matched_required=req.get("matched", []),
            partial_required=[{"required": p["skill"], "via": p["via"]} for p in req.get("partial", [])],
            missing_required=req.get("missing", []),
            matched_preferred=pref.get("matched", []),
            partial_preferred=[{"required": p["skill"], "via": p["via"]} for p in pref.get("partial", [])],
            missing_preferred=pref.get("missing", []),
            disclaimer=DISCLAIMER,
        )
        if explain:
            result.top_shared_terms = self.text.shared_terms(cdoc, jdoc)
            result.summary, result.explanations = build_explanations(result, job, inferred)
        return result

    # ------------------------------------------------------------------ ranking
    @staticmethod
    def _sort_key(item: tuple[Hashable, MatchResult]):
        ident, res = item
        return (-res.score, -res.components["required_skills"].score, str(ident))

    def rank_jobs(
        self, candidate: CandidateProfile, jobs: Sequence[JobPosting], limit: int | None = None, explain: bool = True
    ) -> list[RankedItem]:
        scored = [(j.id, self.score(candidate, j, explain=explain)) for j in jobs]
        scored.sort(key=self._sort_key)
        return [RankedItem(rank=i + 1, id=ident, result=res) for i, (ident, res) in enumerate(scored[:limit])]

    def rank_candidates(
        self,
        job: JobPosting,
        candidates: Sequence[CandidateProfile],
        limit: int | None = None,
        explain: bool = True,
        infer_job_skills: bool = False,
    ) -> list[RankedItem]:
        scored = [(c.id, self.score(c, job, explain=explain, infer_job_skills=infer_job_skills)) for c in candidates]
        scored.sort(key=self._sort_key)
        return [RankedItem(rank=i + 1, id=ident, result=res) for i, (ident, res) in enumerate(scored[:limit])]

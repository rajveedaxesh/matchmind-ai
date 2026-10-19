"""TF-IDF cosine-similarity baseline (the model the hybrid engine is compared against)."""
from __future__ import annotations

from typing import Sequence

from .explain import fit_label
from .matcher import COMPONENT_KEYS, COMPONENT_LABELS, HybridMatcher, candidate_document, job_document
from .types import ComponentScore, DISCLAIMER, CandidateProfile, JobPosting, MatchResult, RankedItem


class TfidfBaseline:
    """Ranks purely by TF-IDF cosine similarity between the profile text and the job text."""

    def __init__(self, matcher: HybridMatcher) -> None:
        self._text = matcher.text  # shares the fitted vectoriser so the comparison is apples-to-apples

    def raw_score(self, candidate: CandidateProfile, job: JobPosting) -> float:
        return self._text.tfidf_cosine(candidate_document(candidate), job_document(job))

    def match(self, candidate: CandidateProfile, job: JobPosting, explain: bool = True) -> MatchResult:
        cdoc, jdoc = candidate_document(candidate), job_document(job)
        raw = self._text.tfidf_cosine(cdoc, jdoc)
        value = min(1.0, raw / self._text.saturation)
        score = round(100 * value, 1)
        components = {
            key: ComponentScore(
                key=key,
                label=COMPONENT_LABELS[key],
                score=score if key == "text_similarity" else 0.0,
                weight=1.0 if key == "text_similarity" else 0.0,
                contribution=score if key == "text_similarity" else 0.0,
                applicable=key == "text_similarity",
                detail=(f"TF-IDF cosine {raw:.2f} (baseline uses text similarity only)."
                        if key == "text_similarity" else "Not used by the TF-IDF baseline."),
            )
            for key in COMPONENT_KEYS
        }
        shared = self._text.shared_terms(cdoc, jdoc) if explain else []
        return MatchResult(
            score=score,
            label=fit_label(score),
            summary=f"TF-IDF baseline: {score:.0f}/100 based only on word overlap.",
            method="tfidf",
            components=components,
            top_shared_terms=shared,
            explanations=[
                "The TF-IDF baseline ignores skills lists, experience, role and location.",
                f"Shared key terms: {', '.join(shared)}." if shared else "No significant shared terms.",
            ],
            disclaimer=DISCLAIMER,
        )

    def rank_jobs(self, candidate: CandidateProfile, jobs: Sequence[JobPosting], limit: int | None = None) -> list[RankedItem]:
        scored = [(j.id, self.match(candidate, j)) for j in jobs]
        scored.sort(key=lambda t: (-t[1].score, str(t[0])))
        return [RankedItem(i + 1, ident, res) for i, (ident, res) in enumerate(scored[:limit])]

    def rank_candidates(self, job: JobPosting, candidates: Sequence[CandidateProfile], limit: int | None = None) -> list[RankedItem]:
        scored = [(c.id, self.match(c, job)) for c in candidates]
        scored.sort(key=lambda t: (-t[1].score, str(t[0])))
        return [RankedItem(i + 1, ident, res) for i, (ident, res) in enumerate(scored[:limit])]

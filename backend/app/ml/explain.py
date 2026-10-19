"""Turns component scores into short, human-readable explanations."""
from __future__ import annotations

from .types import JobPosting, MatchResult

FIT_BANDS = ((80.0, "Strong fit"), (65.0, "Good fit"), (45.0, "Partial fit"), (0.0, "Low fit"))


def fit_label(score: float) -> str:
    for threshold, label in FIT_BANDS:
        if score >= threshold:
            return label
    return "Low fit"


def _join(items: list[str], limit: int = 6) -> str:
    shown = items[:limit]
    more = len(items) - len(shown)
    return ", ".join(shown) + (f" (+{more} more)" if more > 0 else "")


def build_explanations(result: MatchResult, job: JobPosting, inferred: bool = False) -> tuple[str, list[str]]:
    c = result.components
    lines: list[str] = []

    req = c["required_skills"]
    if req.applicable:
        total = len(result.matched_required) + len(result.partial_required) + len(result.missing_required)
        if not result.missing_required and not result.partial_required:
            lines.append(f"Covers all {total} required skills ({_join(result.matched_required)}).")
        else:
            parts = [f"Matches {len(result.matched_required)} of {total} required skills"]
            if result.matched_required:
                parts[0] += f" ({_join(result.matched_required)})"
            lines.append(parts[0] + ".")
            if result.partial_required:
                lines.append(
                    "Partial credit via related skills: "
                    + _join([f"{p['required']} (has {p['via']})" for p in result.partial_required])
                    + "."
                )
            if result.missing_required:
                lines.append(f"Missing required skills: {_join(result.missing_required)}.")
        if inferred:
            lines.append("Required skills were inferred from the job description text because none were listed.")
    pref = c["preferred_skills"]
    if pref.applicable:
        if result.matched_preferred:
            lines.append(f"Preferred skills present: {_join(result.matched_preferred)}.")
        else:
            lines.append("No preferred skills matched.")

    for key in ("role_alignment", "experience", "location"):
        comp = c[key]
        if comp.applicable:
            lines.append(comp.detail)
        else:
            lines.append(f"{comp.label} left out of the score. {comp.detail}")

    text = c["text_similarity"]
    if text.applicable:
        shared = f" Shared key terms: {_join(result.top_shared_terms, 5)}." if result.top_shared_terms else ""
        lines.append(f"Profile and job text similarity scores {text.score:.0f}/100.{shared}")

    applicable = [comp for comp in c.values() if comp.applicable]
    summary = f"{result.label} ({result.score:.1f}/100)."
    if len(applicable) >= 2:
        best = max(applicable, key=lambda x: x.score)
        worst = min(applicable, key=lambda x: x.score)
        if best.key != worst.key:
            summary += f" Strongest on {best.label.lower()} ({best.score:.0f}); weakest on {worst.label.lower()} ({worst.score:.0f})."
    return summary, lines

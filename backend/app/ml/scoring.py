"""Individual scoring components. Each returns a ``Raw`` with ``score=None`` when not applicable."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Sequence

from .skills import RELATED_CREDIT, normalize_skills, related_skills
from .types import CandidateProfile, JobPosting


@dataclass
class Raw:
    score: float | None            # 0-1, or None when the component cannot be evaluated
    detail: str
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- skills
def skill_overlap(wanted: Sequence[str], have: Sequence[str]) -> dict:
    """Exact matches earn full credit; related skills (e.g. PyTorch for TensorFlow) earn partial credit."""
    have_set = set(have)
    matched: list[str] = []
    partial: list[dict[str, str]] = []
    missing: list[str] = []
    for skill in wanted:
        if skill in have_set:
            matched.append(skill)
            continue
        via = sorted(related_skills(skill) & have_set)
        if via:
            partial.append({"skill": skill, "via": via[0]})
        else:
            missing.append(skill)
    credit = len(matched) + RELATED_CREDIT * len(partial)
    coverage = credit / len(wanted) if wanted else 0.0
    return {"matched": matched, "partial": partial, "missing": missing, "coverage": coverage}


def required_skills_score(candidate: CandidateProfile, job_required: list[str], inferred: bool = False) -> Raw:
    if not job_required:
        return Raw(None, "Not scored: the job lists no required skills.")
    res = skill_overlap(job_required, normalize_skills(candidate.skills))
    n = len(job_required)
    detail = f"{len(res['matched'])} of {n} required skills matched"
    if res["partial"]:
        detail += f", {len(res['partial'])} partially via related skills"
    if inferred:
        detail += " (skills were inferred from the job text)"
    return Raw(res["coverage"], detail + ".", res)


def preferred_skills_score(candidate: CandidateProfile, job_preferred: list[str]) -> Raw:
    if not job_preferred:
        return Raw(None, "Not scored: the job lists no preferred skills.")
    res = skill_overlap(job_preferred, normalize_skills(candidate.skills))
    n = len(job_preferred)
    detail = f"{len(res['matched'])} of {n} preferred skills matched"
    if res["partial"]:
        detail += f", {len(res['partial'])} partially via related skills"
    return Raw(res["coverage"], detail + ".", res)


# ------------------------------------------------------------------------- experience
SENIORITY_RANGES: dict[str, tuple[float, float | None]] = {
    "junior": (0, 2),
    "mid": (2, 5),
    "senior": (5, 10),
    "lead": (8, None),
}


def experience_score(candidate: CandidateProfile, job: JobPosting) -> Raw:
    years = candidate.years_experience
    lo, hi = job.min_years, job.max_years
    if lo is None and hi is None and job.seniority in SENIORITY_RANGES:
        lo, hi = SENIORITY_RANGES[job.seniority]
    if years is None:
        return Raw(None, "Not scored: the candidate has not stated years of experience.")
    if lo is None and hi is None:
        return Raw(None, "Not scored: the job states no experience range or seniority.")
    lo_v = 0.0 if lo is None else float(lo)
    hi_v = float("inf") if hi is None else float(hi)
    rng = f"{lo_v:g}+" if hi is None else f"{lo_v:g}-{hi_v:g}"
    if lo_v <= years <= hi_v:
        return Raw(1.0, f"{years:g} yrs is within the requested {rng} yrs.", {"years": years, "range": rng})
    if years < lo_v:
        score = max(0.0, 1.0 - (lo_v - years) / max(lo_v, 1.0))
        return Raw(score, f"{years:g} yrs is {lo_v - years:g} below the requested {rng} yrs.", {"years": years, "range": rng})
    score = max(0.6, 1.0 - 0.08 * (years - hi_v))
    return Raw(score, f"{years:g} yrs is above the requested {rng} yrs (mild over-qualification penalty).", {"years": years, "range": rng})


# ----------------------------------------------------------------------- role alignment
_SENIORITY_WORDS = {"senior", "sr", "junior", "jr", "lead", "principal", "staff", "associate", "intern",
                    "head", "founding", "applied", "i", "ii", "iii"}
_STOP = {"and", "of", "the", "for", "a", "in", "at", "to", "with"}

_CONCEPT_PHRASES: dict[str, tuple[str, ...]] = {
    "backend": ("backend", "back end", "server side", "api developer", "python developer", "java developer"),
    "frontend": ("frontend", "front end", "ui engineer", "ui developer", "web developer", "javascript developer"),
    "data_science": ("data scientist", "data science", "applied scientist", "research scientist", "statistician"),
    "ml": ("machine learning", "ml engineer", "nlp", "ai engineer", "deep learning", "computer vision", "mlops"),
    "data_eng": ("data engineer", "analytics engineer", "etl", "data platform"),
    "analytics": ("data analyst", "business intelligence", "bi analyst", "product analyst", "analytics", "reporting analyst"),
    "devops": ("devops", "site reliability", "sre", "cloud engineer", "cloud platform", "infrastructure engineer", "platform engineer"),
    "product": ("product manager", "product owner", "program manager", "product lead"),
    "design": ("designer", "ux", "ui/ux", "user experience", "ux researcher", "design researcher"),
    "security": ("security", "appsec", "soc analyst", "penetration"),
    "qa": ("qa", "quality assurance", "test engineer", "sdet", "automation engineer", "test automation"),
    "mobile": ("mobile", "ios", "android", "react native", "flutter"),
}
_FULLSTACK = ("full stack", "fullstack")

_CONCEPT_ADJACENCY: dict[frozenset, float] = {
    frozenset(p[:2]): p[2]
    for p in (
        ("data_science", "ml", 0.6), ("data_science", "analytics", 0.5), ("data_science", "data_eng", 0.3),
        ("ml", "data_eng", 0.4), ("ml", "backend", 0.3), ("data_eng", "backend", 0.4),
        ("data_eng", "analytics", 0.4), ("backend", "devops", 0.3), ("backend", "qa", 0.3),
        ("frontend", "design", 0.3), ("frontend", "mobile", 0.4), ("frontend", "qa", 0.3),
        ("mobile", "qa", 0.3), ("devops", "security", 0.3), ("backend", "security", 0.3),
        ("product", "analytics", 0.3), ("product", "design", 0.3),
    )
}


def _norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/+# ]", " ", title.lower().replace("-", " "))).strip()


_CONCEPT_REGEXES: dict[str, re.Pattern[str]] = {
    concept: re.compile(r"\b(?:" + "|".join(re.escape(p) for p in phrases) + r")\b")
    for concept, phrases in _CONCEPT_PHRASES.items()
}


@lru_cache(maxsize=4096)
def _title_concepts_cached(title: str) -> frozenset[str]:
    t = _norm_title(title)
    found = {c for c, rx in _CONCEPT_REGEXES.items() if rx.search(t)}
    if any(p in t for p in _FULLSTACK):
        found |= {"backend", "frontend"}
    return frozenset(found)


def title_concepts(title: str) -> set[str]:
    return set(_title_concepts_cached(title))


@lru_cache(maxsize=4096)
def _title_tokens_cached(title: str) -> frozenset[str]:
    return frozenset(w for w in _norm_title(title).split() if w not in _SENIORITY_WORDS and w not in _STOP)


def _title_tokens(title: str) -> set[str]:
    return set(_title_tokens_cached(title))


def _concept_similarity(job_c: set[str], cand_c: set[str]) -> float:
    if not job_c or not cand_c:
        return 0.0
    total = 0.0
    for j in job_c:
        if j in cand_c:
            total += 1.0
        else:
            total += max((_CONCEPT_ADJACENCY.get(frozenset((j, c)), 0.0) for c in cand_c), default=0.0)
    return total / len(job_c)


def role_alignment_score(candidate: CandidateProfile, job: JobPosting) -> Raw:
    titles = [t for t in (candidate.headline, *candidate.desired_titles) if t and t.strip()]
    if not job.title.strip() or not titles:
        return Raw(None, "Not scored: missing job title or candidate headline/desired titles.")
    job_c, job_t = title_concepts(job.title), _title_tokens(job.title)
    best, best_title = -1.0, titles[0]
    for title in titles:
        cand_c, cand_t = title_concepts(title), _title_tokens(title)
        jaccard = len(job_t & cand_t) / len(job_t | cand_t) if (job_t | cand_t) else 0.0
        if job_c and cand_c:
            score = 0.75 * _concept_similarity(job_c, cand_c) + 0.25 * jaccard
        else:
            score = jaccard
        if score > best:
            best, best_title = score, title
    score = min(1.0, best)
    if score >= 0.75:
        verdict = "closely aligned"
    elif score >= 0.35:
        verdict = "partly aligned"
    else:
        verdict = "weakly aligned"
    return Raw(score, f"'{job.title}' is {verdict} with '{best_title}'.", {"best_title": best_title})


# ---------------------------------------------------------------------------- location
def _city(value: str | None) -> str:
    return (value or "").split(",")[0].strip().lower()


def location_score(candidate: CandidateProfile, job: JobPosting) -> Raw:
    modes = {m.strip().lower() for m in candidate.preferred_work_modes if m.strip()}
    locs = [_city(x) for x in candidate.preferred_locations if x.strip()]
    wants_remote_loc = "remote" in locs
    cities = [c for c in locs if c != "remote"]
    if not modes and not locs:
        return Raw(None, "Not scored: the candidate has stated no location or work-mode preference.")
    job_mode = (job.work_mode or "").lower() or None
    job_city = _city(job.location)
    if job_mode is None and not job_city:
        return Raw(None, "Not scored: the job states no location or work mode.")

    if job_mode == "remote" or job_city == "remote":
        if "remote" in modes or wants_remote_loc:
            return Raw(1.0, "Remote role matches the stated remote preference.")
        if modes:
            return Raw(0.5, f"Remote role, but the candidate prefers {', '.join(sorted(modes))} work.")
        return Raw(0.8, "Remote role; the candidate named locations but did not rule out remote work.")

    if cities:
        if job_city in cities:
            base, note = 1.0, f"Job location {job.location} is a preferred location."
        elif candidate.open_to_relocation:
            base, note = 0.5, f"{job.location} is not a preferred location, but the candidate is open to relocation."
        else:
            base, note = 0.0, f"{job.location} is not among the preferred locations ({', '.join(cities)})."
    else:
        base, note = 0.8, "No city preference stated."
    if modes and job_mode and job_mode not in modes:
        base *= 0.6
        note += f" Work mode '{job_mode}' is not among the preferred modes."
    return Raw(base, note)

"""Plain data types for the matching engine.

Design note on fairness: ``CandidateProfile`` intentionally contains ONLY job-relevant fields.
There is no name, age, gender, ethnicity, photo, marital status, etc., so the scorer cannot use
them even by accident. ``PROTECTED_ATTRIBUTE_TERMS`` is also used by the API layer to reject
such fields outright.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Hashable

PROTECTED_ATTRIBUTE_TERMS: tuple[str, ...] = (
    "gender", "sex", "age", "date_of_birth", "dob", "birth_date", "race", "ethnicity",
    "religion", "nationality", "caste", "marital_status", "disability", "pregnancy",
    "sexual_orientation", "photo", "picture", "political_affiliation", "citizenship",
)

DISCLAIMER = (
    "Match scores are heuristic fit indicators computed from skills, text, experience, role and "
    "stated preferences. They are NOT probabilities of being hired or of job performance."
)


@dataclass(frozen=True)
class CandidateProfile:
    id: Hashable
    headline: str
    summary: str = ""
    skills: tuple[str, ...] = ()
    years_experience: float | None = None
    desired_titles: tuple[str, ...] = ()
    preferred_locations: tuple[str, ...] = ()
    preferred_work_modes: tuple[str, ...] = ()
    open_to_relocation: bool = False


@dataclass(frozen=True)
class JobPosting:
    id: Hashable
    title: str
    description: str = ""
    required_skills: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    min_years: float | None = None
    max_years: float | None = None
    seniority: str | None = None
    location: str | None = None
    work_mode: str | None = None


@dataclass
class ComponentScore:
    key: str
    label: str
    score: float          # 0-100 (0 when not applicable)
    weight: float         # effective weight after re-normalising over applicable components (0-1)
    contribution: float   # points contributed to the final 0-100 score
    applicable: bool
    detail: str


@dataclass
class MatchResult:
    score: float
    label: str
    summary: str
    method: str
    components: dict[str, ComponentScore]
    matched_required: list[str] = field(default_factory=list)
    partial_required: list[dict[str, str]] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    partial_preferred: list[dict[str, str]] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    top_shared_terms: list[str] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedItem:
    rank: int
    id: Hashable
    result: MatchResult

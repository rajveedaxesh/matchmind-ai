"""Pydantic request/response models and input validation."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .ml.types import DISCLAIMER, PROTECTED_ATTRIBUTE_TERMS, MatchResult

WorkMode = Literal["remote", "hybrid", "onsite"]
Seniority = Literal["junior", "mid", "senior", "lead"]
EmploymentType = Literal["full-time", "part-time", "contract", "internship"]
ApplicationStatus = Literal["saved", "applied", "interviewing", "offer", "rejected", "withdrawn"]
Method = Literal["hybrid", "tfidf"]


def _clean_list(values: Any, max_items: int = 50, max_len: int = 60) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)):
        raise ValueError("must be a list of strings")
    out: dict[str, str] = {}
    for v in values:
        if not isinstance(v, str):
            raise ValueError("every item must be a string")
        s = " ".join(v.split())
        if not s:
            continue
        if len(s) > max_len:
            raise ValueError(f"items must be at most {max_len} characters")
        out.setdefault(s.lower(), s)
    if len(out) > max_items:
        raise ValueError(f"at most {max_items} items are allowed")
    return list(out.values())


# ------------------------------------------------------------------------------ jobs
class JobBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=120)
    company: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    work_mode: WorkMode
    employment_type: EmploymentType = "full-time"
    seniority: Seniority | None = None
    min_years: float | None = Field(default=None, ge=0, le=50)
    max_years: float | None = Field(default=None, ge=0, le=60)
    salary_min: int | None = Field(default=None, ge=0, le=10_000_000)
    salary_max: int | None = Field(default=None, ge=0, le=10_000_000)
    role_family: str | None = Field(default=None, max_length=40)
    description: str = Field(min_length=20, max_length=8000)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def _skills(cls, v: Any) -> list[str]:
        return _clean_list(v)

    @model_validator(mode="after")
    def _ranges(self) -> "JobBase":
        if self.min_years is not None and self.max_years is not None and self.min_years > self.max_years:
            raise ValueError("min_years cannot be greater than max_years")
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max")
        return self


class JobCreate(JobBase):
    pass


class JobOut(JobBase):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)  # outputs may be built from raw DB rows

    id: int
    is_synthetic: bool = True
    created_at: str | None = None
    application_status: ApplicationStatus | None = None


class AdHocJob(BaseModel):
    """A job description entered by a recruiter; lenient because it is not stored."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=20, max_length=8000)
    company: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    work_mode: WorkMode | None = None
    seniority: Seniority | None = None
    min_years: float | None = Field(default=None, ge=0, le=50)
    max_years: float | None = Field(default=None, ge=0, le=60)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def _skills(cls, v: Any) -> list[str]:
        return _clean_list(v)

    @model_validator(mode="after")
    def _ranges(self) -> "AdHocJob":
        if self.min_years is not None and self.max_years is not None and self.min_years > self.max_years:
            raise ValueError("min_years cannot be greater than max_years")
        return self


class JobList(BaseModel):
    items: list[JobOut]
    total: int
    limit: int
    offset: int


# ------------------------------------------------------------------------- candidates
class CandidateBase(BaseModel):
    """Job-relevant fields only. Protected characteristics are rejected with a clear error."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str = Field(min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    skills: list[str] = Field(default_factory=list)
    summary: str = Field(default="", max_length=3000)
    desired_titles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_work_modes: list[WorkMode] = Field(default_factory=list)
    open_to_relocation: bool = False

    @model_validator(mode="before")
    @classmethod
    def _reject_protected(cls, data: Any) -> Any:
        if isinstance(data, dict):
            hits = sorted(k for k in data if str(k).lower().replace("-", "_").replace(" ", "_") in PROTECTED_ATTRIBUTE_TERMS)
            if hits:
                raise ValueError(
                    f"Protected attribute(s) {hits} are not accepted: MatchMind never stores or uses "
                    "protected characteristics when ranking."
                )
        return data

    @field_validator("skills", mode="before")
    @classmethod
    def _skills(cls, v: Any) -> list[str]:
        return _clean_list(v, max_items=60)

    @field_validator("desired_titles", "preferred_locations", mode="before")
    @classmethod
    def _short_lists(cls, v: Any) -> list[str]:
        return _clean_list(v, max_items=10, max_len=80)

    @field_validator("preferred_work_modes", mode="before")
    @classmethod
    def _modes(cls, v: Any) -> list[str]:
        return [m.lower() for m in _clean_list(v, max_items=3, max_len=10)]


class ProfileIn(CandidateBase):
    display_name: str | None = Field(default=None, max_length=80)


class CandidateOut(CandidateBase):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)  # outputs may be built from raw DB rows

    id: int
    display_name: str
    is_synthetic: bool = True


class Completeness(BaseModel):
    percent: int
    missing: list[str]


class ProfileOut(CandidateOut):
    completeness: Completeness


# ------------------------------------------------------------------------------ match
class ComponentOut(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    contribution: float = Field(ge=0, le=100)
    applicable: bool
    detail: str


class PartialSkill(BaseModel):
    required: str
    via: str


class MatchOut(BaseModel):
    score: float = Field(ge=0, le=100)
    label: str
    summary: str
    method: Method
    components: dict[str, ComponentOut]
    matched_required: list[str]
    partial_required: list[PartialSkill]
    missing_required: list[str]
    matched_preferred: list[str]
    partial_preferred: list[PartialSkill]
    missing_preferred: list[str]
    top_shared_terms: list[str]
    explanations: list[str]
    disclaimer: str = DISCLAIMER

    @classmethod
    def from_result(cls, result: MatchResult) -> "MatchOut":
        return cls.model_validate(result.to_dict())


class JobRecommendation(BaseModel):
    rank: int
    job: JobOut
    match: MatchOut


class RecommendationList(BaseModel):
    method: Method
    total_scored: int
    total_returned: int
    items: list[JobRecommendation]
    weights: dict[str, float]
    warnings: list[str]
    disclaimer: str = DISCLAIMER


# ------------------------------------------------------------------------ applications
class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApplicationStatus
    notes: str | None = Field(default=None, max_length=2000)


class ApplicationOut(BaseModel):
    job: JobOut
    status: ApplicationStatus
    notes: str | None = None
    updated_at: str
    match: MatchOut | None = None


class ApplicationList(BaseModel):
    items: list[ApplicationOut]
    counts: dict[str, int]


# -------------------------------------------------------------------------- recruiter
class RecruiterMatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: int | None = Field(default=None, ge=1)
    job: AdHocJob | None = None
    limit: int = Field(default=10, ge=1, le=50)
    method: Method = "hybrid"
    min_score: float = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def _exactly_one(self) -> "RecruiterMatchRequest":
        if (self.job_id is None) == (self.job is None):
            raise ValueError("Provide exactly one of 'job_id' (a stored job) or 'job' (an ad-hoc description)")
        return self


class JobSummary(BaseModel):
    id: int | None
    title: str
    company: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    skills_inferred_from_text: bool = False


class CandidateRanking(BaseModel):
    rank: int
    candidate: CandidateOut
    match: MatchOut


class RecruiterMatchResponse(BaseModel):
    job: JobSummary
    method: Method
    total_candidates: int
    total_returned: int
    items: list[CandidateRanking]
    weights: dict[str, float]
    disclaimer: str = DISCLAIMER

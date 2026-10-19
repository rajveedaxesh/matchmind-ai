"""MatchMind matching engine (framework-free, reusable)."""
from .baseline import TfidfBaseline
from .matcher import COMPONENT_KEYS, DEFAULT_WEIGHTS, HybridMatcher, candidate_document, job_document
from .types import (
    DISCLAIMER,
    PROTECTED_ATTRIBUTE_TERMS,
    CandidateProfile,
    ComponentScore,
    JobPosting,
    MatchResult,
    RankedItem,
)

__all__ = [
    "COMPONENT_KEYS",
    "DEFAULT_WEIGHTS",
    "DISCLAIMER",
    "PROTECTED_ATTRIBUTE_TERMS",
    "CandidateProfile",
    "ComponentScore",
    "HybridMatcher",
    "JobPosting",
    "MatchResult",
    "RankedItem",
    "TfidfBaseline",
    "candidate_document",
    "job_document",
]

"""Hybrid matching engine: bounds, components, missing data, ranking, explanations, fairness."""
import dataclasses

import pytest

from app.ml import (
    COMPONENT_KEYS,
    DEFAULT_WEIGHTS,
    DISCLAIMER,
    CandidateProfile,
    HybridMatcher,
    JobPosting,
    TfidfBaseline,
)
from app.ml.matcher import candidate_document, validate_weights
from app.ml.skills import extract_skills, normalize_skill, normalize_skills


def make_job(**kw):
    base = dict(
        id=1, title="Backend Engineer", description="Build REST APIs in Python with PostgreSQL.",
        required_skills=("python", "postgresql", "docker"), preferred_skills=("redis",),
        min_years=3, max_years=6, location="London, UK", work_mode="hybrid",
    )
    base.update(kw)
    return JobPosting(**base)


def make_cand(**kw):
    base = dict(
        id=1, headline="Backend Engineer", summary="Builds Python REST APIs backed by PostgreSQL.",
        skills=("python", "postgresql", "docker", "redis"), years_experience=4,
        desired_titles=("Backend Engineer",), preferred_locations=("London",), preferred_work_modes=("hybrid",),
    )
    base.update(kw)
    return CandidateProfile(**base)


@pytest.fixture(scope="module")
def m():
    return HybridMatcher.from_entities([make_job()], [make_cand()])


# ------------------------------------------------------------------------ bounds
def test_all_seed_pairs_score_within_0_100(matcher, seed_jobs, seed_candidates):
    for c in seed_candidates:
        for j in seed_jobs:
            r = matcher.score(c, j, explain=False)
            assert 0.0 <= r.score <= 100.0
            for comp in r.components.values():
                assert 0.0 <= comp.score <= 100.0
                assert 0.0 <= comp.weight <= 1.0
                assert 0.0 <= comp.contribution <= 100.0


def test_contributions_sum_to_final_score(matcher, seed_jobs, seed_candidates):
    r = matcher.score(seed_candidates[0], seed_jobs[0])
    assert sum(c.contribution for c in r.components.values()) == pytest.approx(r.score, abs=0.3)


def test_effective_weights_sum_to_one(m):
    r = m.score(make_cand(), make_job())
    assert sum(c.weight for c in r.components.values()) == pytest.approx(1.0, abs=1e-3)


def test_perfect_match_scores_high_and_empty_scores_low(m):
    good = m.score(make_cand(), make_job())
    bad = m.score(
        make_cand(headline="Pastry Chef", summary="Bakes bread.", skills=("baking",), years_experience=0,
                  desired_titles=("Pastry Chef",), preferred_locations=("Tokyo",), preferred_work_modes=("onsite",)),
        make_job(),
    )
    assert good.score >= 85
    assert bad.score <= 25
    assert good.score > bad.score + 50


# -------------------------------------------------------------------- skill logic
def test_required_skill_coverage_and_missing_list(m):
    r = m.score(make_cand(skills=("python",)), make_job())
    assert r.matched_required == ["python"]
    assert set(r.missing_required) == {"postgresql", "docker"}
    assert r.components["required_skills"].score == pytest.approx(33.3, abs=0.1)


def test_more_required_skills_never_lowers_score(m):
    few = m.score(make_cand(skills=("python",)), make_job()).score
    more = m.score(make_cand(skills=("python", "postgresql", "docker")), make_job()).score
    assert more > few


def test_related_skill_earns_partial_credit(m):
    job = make_job(required_skills=("pytorch",), preferred_skills=())
    exact = m.score(make_cand(skills=("pytorch",)), job).components["required_skills"].score
    related = m.score(make_cand(skills=("tensorflow",)), job)
    none = m.score(make_cand(skills=("excel",)), job).components["required_skills"].score
    assert exact == 100.0 and none == 0.0
    assert related.components["required_skills"].score == pytest.approx(50.0)
    assert related.partial_required == [{"required": "pytorch", "via": "tensorflow"}]


def test_aliases_are_normalised(m):
    r = m.score(make_cand(skills=("Python3", "Postgres", "Containerization")), make_job())
    assert set(r.matched_required) == {"python", "postgresql", "docker"}


def test_preferred_skills_only_affect_their_component(m):
    with_pref = m.score(make_cand(skills=("python", "postgresql", "docker", "redis")), make_job())
    without = m.score(make_cand(skills=("python", "postgresql", "docker")), make_job())
    assert with_pref.components["preferred_skills"].score == 100.0
    assert without.components["preferred_skills"].score == 0.0
    assert with_pref.components["required_skills"].score == without.components["required_skills"].score


# --------------------------------------------------------------- experience / role
def test_experience_in_range_beats_underqualified(m):
    ok = m.score(make_cand(years_experience=4), make_job()).components["experience"].score
    junior = m.score(make_cand(years_experience=1), make_job()).components["experience"].score
    assert ok == 100.0 and junior < ok


def test_overqualification_is_only_mildly_penalised(m):
    s = m.score(make_cand(years_experience=15), make_job()).components["experience"].score
    assert 60.0 <= s < 100.0


def test_role_alignment_distinguishes_roles(m):
    same = m.score(make_cand(headline="Backend Engineer", desired_titles=()), make_job()).components["role_alignment"].score
    adjacent = m.score(make_cand(headline="Data Engineer", desired_titles=()), make_job()).components["role_alignment"].score
    different = m.score(make_cand(headline="Product Designer", desired_titles=()), make_job()).components["role_alignment"].score
    assert same > adjacent > different


# ------------------------------------------------------------------------ location
def test_location_preference_matters(m):
    match = m.score(make_cand(), make_job()).components["location"].score
    mismatch = m.score(
        make_cand(preferred_locations=("Berlin",), preferred_work_modes=("onsite",)), make_job()
    ).components["location"].score
    assert match == 100.0 and mismatch < 30


def test_relocation_gives_partial_credit(m):
    stay = m.score(make_cand(preferred_locations=("Berlin",), preferred_work_modes=("hybrid",)), make_job()).components["location"].score
    move = m.score(make_cand(preferred_locations=("Berlin",), preferred_work_modes=("hybrid",), open_to_relocation=True), make_job()).components["location"].score
    assert move > stay


def test_remote_job_fits_remote_preference(m):
    r = m.score(make_cand(preferred_locations=("Remote",), preferred_work_modes=("remote",)), make_job(location="Remote", work_mode="remote"))
    assert r.components["location"].score == 100.0


# ------------------------------------------------------------------ missing fields
def test_missing_location_preferences_exclude_component_without_penalty(m):
    r = m.score(make_cand(preferred_locations=(), preferred_work_modes=()), make_job())
    loc = r.components["location"]
    assert loc.applicable is False and loc.weight == 0.0 and loc.contribution == 0.0
    assert "Not scored" in loc.detail
    assert sum(c.weight for c in r.components.values()) == pytest.approx(1.0, abs=1e-3)
    assert r.score >= 85  # not dragged down by an absent preference


def test_missing_years_excludes_experience(m):
    r = m.score(make_cand(years_experience=None), make_job())
    assert r.components["experience"].applicable is False


def test_job_without_skills_lists_excludes_skill_components(m):
    r = m.score(make_cand(), make_job(required_skills=(), preferred_skills=()))
    assert r.components["required_skills"].applicable is False
    assert r.components["preferred_skills"].applicable is False
    assert 0 <= r.score <= 100


def test_fully_empty_candidate_is_handled(m):
    empty = CandidateProfile(id=9, headline="")
    r = m.score(empty, make_job())
    assert 0.0 <= r.score <= 100.0
    assert r.components["required_skills"].score == 0.0  # no skills -> 0 coverage, not an error
    assert r.explanations


def test_fully_empty_job_is_handled(m):
    r = m.score(make_cand(), JobPosting(id=9, title=""))
    assert 0.0 <= r.score <= 100.0


def test_infer_job_skills_from_description(m):
    job = make_job(required_skills=(), description="We use Python, Docker, Kubernetes and Rust daily.")
    r = m.score(make_cand(), job, infer_job_skills=True)
    assert r.components["required_skills"].applicable is True
    assert "python" in r.matched_required and "rust" in r.missing_required
    # Kubernetes is related to the candidate's Docker, so it earns partial (not full, not zero) credit.
    assert any(p["required"] == "kubernetes" and p["via"] == "docker" for p in r.partial_required)
    assert any("inferred" in line for line in r.explanations)


# --------------------------------------------------------------------- weights
def test_zero_weight_removes_component(seed_jobs, seed_candidates):
    custom = HybridMatcher.from_entities(seed_jobs, seed_candidates, weights={**DEFAULT_WEIGHTS, "location": 0.0})
    r = custom.score(seed_candidates[0], seed_jobs[0])
    assert r.components["location"].weight == 0.0


@pytest.mark.parametrize("bad", [{"nope": 1.0}, {"required_skills": -1.0}, {k: 0.0 for k in COMPONENT_KEYS}])
def test_invalid_weights_rejected(bad):
    with pytest.raises(ValueError):
        validate_weights(bad)


# ------------------------------------------------------------------------ ranking
def test_rank_candidates_sorted_and_stable(matcher, seed_jobs, seed_candidates):
    ranked = matcher.rank_candidates(seed_jobs[0], seed_candidates)
    scores = [r.result.score for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert [r.rank for r in ranked] == list(range(1, len(seed_candidates) + 1))
    again = matcher.rank_candidates(seed_jobs[0], list(reversed(seed_candidates)))
    assert [r.id for r in again] == [r.id for r in ranked]  # input order does not matter


def test_rank_jobs_puts_relevant_roles_first(matcher, seed_jobs, seed_candidates):
    ds = next(c for c in seed_candidates if c.headline == "Data Scientist")
    top3 = matcher.rank_jobs(ds, seed_jobs, limit=3)
    titles = [next(j.title for j in seed_jobs if j.id == r.id) for r in top3]
    assert all("Data Scientist" in t for t in titles)


def test_recruiter_ranking_puts_skilled_candidate_first(matcher, seed_jobs, seed_candidates):
    job = next(j for j in seed_jobs if j.title == "Machine Learning Engineer")
    top = matcher.rank_candidates(job, seed_candidates, limit=1)[0]
    assert next(c for c in seed_candidates if c.id == top.id).headline == "Machine Learning Engineer"


def test_limit_applied(matcher, seed_jobs, seed_candidates):
    assert len(matcher.rank_jobs(seed_candidates[0], seed_jobs, limit=5)) == 5


# --------------------------------------------------------------- explanations
def test_explanations_name_missing_skills_and_disclaim(m):
    r = m.score(make_cand(skills=("python",)), make_job())
    text = " ".join(r.explanations)
    assert "Missing required skills" in text and "docker" in text
    assert r.summary and r.label in r.summary
    assert "NOT probabilities" in r.disclaimer == DISCLAIMER or "NOT probabilities" in DISCLAIMER


def test_score_is_not_described_as_hiring_probability(m):
    r = m.score(make_cand(), make_job())
    blob = (r.summary + " ".join(r.explanations)).lower()
    assert "probab" not in blob and "chance of" not in blob and "likelihood" not in blob


# ------------------------------------------------------------------- baseline
def test_tfidf_baseline_scores_text_only(matcher, seed_jobs, seed_candidates):
    base = TfidfBaseline(matcher)
    r = base.match(seed_candidates[0], seed_jobs[0])
    assert r.method == "tfidf" and 0 <= r.score <= 100
    assert [k for k, c in r.components.items() if c.applicable] == ["text_similarity"]


def test_tfidf_similarity_prefers_related_text(matcher, seed_jobs, seed_candidates):
    base = TfidfBaseline(matcher)
    ml_job = next(j for j in seed_jobs if j.title == "Machine Learning Engineer")
    ml_c = next(c for c in seed_candidates if c.headline == "Machine Learning Engineer")
    chef = dataclasses.replace(ml_c, id=99, headline="Pastry Chef", summary="Bakes sourdough bread and croissants.", skills=("baking",))
    assert base.raw_score(ml_c, ml_job) > base.raw_score(chef, ml_job)


def test_semantic_fallback_when_sentence_transformers_missing():
    corpus = ["python backend api", "react frontend ui", "data science statistics", "devops kubernetes docker"]
    fallback = HybridMatcher(corpus, encoder_backend="sentence-transformers", st_model="definitely-not-a-real-model")
    r = fallback.score(make_cand(), make_job())
    assert 0 <= r.score <= 100
    assert fallback.text.backend_name in {"lsa", "tfidf-only"}  # never crashes, degrades locally


def test_tiny_corpus_degrades_to_tfidf_only():
    tiny = HybridMatcher(["only one document here"])
    assert tiny.text.backend_name == "tfidf-only"
    assert 0 <= tiny.score(make_cand(), make_job()).score <= 100


# ----------------------------------------------------------------------- fairness
def test_candidate_profile_has_no_protected_fields():
    banned = {"name", "display_name", "gender", "sex", "age", "ethnicity", "race", "religion", "photo", "nationality", "marital_status"}
    fields = {f.name for f in dataclasses.fields(CandidateProfile)}
    assert not (fields & banned)


def test_score_ignores_candidate_identity(m):
    a, b = make_cand(id=1), make_cand(id=2)
    assert m.score(a, make_job()).score == m.score(b, make_job()).score


def test_document_text_excludes_ids_and_names():
    doc = candidate_document(make_cand(id="SECRET-ID"))
    assert "SECRET-ID" not in doc


# --------------------------------------------------------------------- skills util
def test_skill_normalisation_helpers():
    assert normalize_skill("  PostgreSQL ") == "postgresql"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("Scikit Learn") == "scikit-learn"
    assert normalize_skills(["Python", "python3", "", "  "]) == ["python"]
    assert normalize_skill("totally-unknown-tool") == "totally-unknown-tool"


def test_extract_skills_prefers_longest_match():
    found = extract_skills("Experience with React Native and PyTorch required.")
    assert "react native" in found and "react" not in found and "pytorch" in found
    assert extract_skills("") == []
    assert "go" not in extract_skills("We like to go to lunch")

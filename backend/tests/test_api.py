"""API tests: both workflows end to end, validation, missing fields, score bounds, ranking order."""
import pytest

JOB_PAYLOAD = {
    "title": "Platform Engineer",
    "company": "Testco (fictional)",
    "location": "Remote",
    "work_mode": "remote",
    "description": "Build and operate internal developer platforms on Kubernetes.",
    "required_skills": ["Kubernetes", "Terraform"],
}


def assert_match_shape(match):
    assert 0 <= match["score"] <= 100
    assert "NOT probabilities" in match["disclaimer"]
    assert match["explanations"] and match["summary"]
    keys = {"required_skills", "preferred_skills", "text_similarity", "role_alignment", "experience", "location"}
    assert set(match["components"]) == keys
    for comp in match["components"].values():
        assert 0 <= comp["score"] <= 100 and 0 <= comp["weight"] <= 1
    active = sum(c["weight"] for c in match["components"].values() if c["applicable"])
    assert active == pytest.approx(1.0, abs=0.01)


# ------------------------------------------------------------------ meta / health
def test_health_and_meta(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    meta = client.get("/api/meta").json()
    assert meta["synthetic_data"] is True
    assert "FICTIONAL" in meta["data_notice"]
    assert meta["counts"]["jobs"] >= 25
    assert meta["counts"]["candidates"] >= 15
    assert sum(meta["weights"].values()) == pytest.approx(1.0)


def test_seed_is_reproducible(client):
    first = client.get("/api/jobs?limit=100").json()
    second = client.get("/api/jobs?limit=100").json()
    assert first == second
    assert first["total"] >= 25


# ---------------------------------------------------------------------- jobs
def test_job_filters(client):
    remote = client.get("/api/jobs?work_mode=remote&limit=100").json()
    assert remote["total"] > 0 and all(j["work_mode"] == "remote" for j in remote["items"])
    senior = client.get("/api/jobs?seniority=senior&limit=100").json()
    assert all(j["seniority"] == "senior" for j in senior["items"])
    hit = client.get("/api/jobs?skill=python&limit=100").json()
    assert hit["total"] > 0
    assert client.get("/api/jobs?q=zzzzqqqq").json()["total"] == 0


def test_job_pagination(client):
    page1 = client.get("/api/jobs?limit=5&offset=0").json()
    page2 = client.get("/api/jobs?limit=5&offset=5").json()
    assert len(page1["items"]) == 5
    assert {j["id"] for j in page1["items"]}.isdisjoint({j["id"] for j in page2["items"]})


def test_job_not_found_and_bad_filter(client):
    assert client.get("/api/jobs/99999").status_code == 404
    assert client.get("/api/jobs?work_mode=moon").status_code == 422
    assert client.get("/api/jobs?limit=0").status_code == 422


def test_create_job_and_validation(client):
    created = client.post("/api/jobs", json=JOB_PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["is_synthetic"] is False
    assert client.get(f"/api/jobs/{body['id']}").status_code == 200
    bad = {**JOB_PAYLOAD, "work_mode": "teleport"}
    assert client.post("/api/jobs", json=bad).status_code == 422
    bad = {**JOB_PAYLOAD, "min_years": 8, "max_years": 2}
    assert client.post("/api/jobs", json=bad).status_code == 422
    bad = {**JOB_PAYLOAD, "unexpected": 1}
    assert client.post("/api/jobs", json=bad).status_code == 422
    short = {**JOB_PAYLOAD, "description": "too short"}
    assert client.post("/api/jobs", json=short).status_code == 422


# ------------------------------------------------------------- job-seeker workflow
def test_profile_get_and_update(client):
    profile = client.get("/api/profile").json()
    assert profile["completeness"]["percent"] >= 0
    update = {
        "headline": "Data Engineer",
        "skills": ["Python", "SQL", "Airflow", "python"],
        "years_experience": 4,
        "summary": "Builds reliable batch data pipelines with Airflow and SQL warehouses.",
        "desired_titles": ["Data Engineer"],
        "preferred_work_modes": ["remote"],
    }
    r = client.put("/api/profile", json=update)
    assert r.status_code == 200
    out = r.json()
    assert out["skills"] == ["Python", "SQL", "Airflow"]  # case-insensitive de-duplication
    assert out["completeness"]["percent"] == 100 or out["completeness"]["missing"]
    assert client.get("/api/profile").json()["headline"] == "Data Engineer"


@pytest.mark.parametrize("field", ["gender", "age", "ethnicity", "religion", "marital_status", "photo"])
def test_profile_rejects_protected_attributes(client, field):
    r = client.put("/api/profile", json={"headline": "Engineer", field: "x"})
    assert r.status_code == 422
    assert "Protected attribute" in r.text


def test_profile_validation(client):
    assert client.put("/api/profile", json={"headline": "x"}).status_code == 422
    assert client.put("/api/profile", json={"headline": "Engineer", "years_experience": -3}).status_code == 422
    assert client.put("/api/profile", json={"headline": "Engineer", "preferred_work_modes": ["lunar"]}).status_code == 422


def test_recommendations_ranked_and_bounded(client):
    r = client.get("/api/recommendations?limit=15")
    assert r.status_code == 200
    body = r.json()
    assert body["method"] == "hybrid"
    scores = [i["match"]["score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)
    assert [i["rank"] for i in body["items"]] == list(range(1, len(scores) + 1))
    for item in body["items"]:
        assert_match_shape(item["match"])
    assert "NOT probabilities" in body["disclaimer"]


def test_recommendations_tfidf_baseline_and_filters(client):
    tfidf = client.get("/api/recommendations?method=tfidf&limit=5").json()
    assert tfidf["method"] == "tfidf" and tfidf["items"]
    remote = client.get("/api/recommendations?work_mode=remote&limit=50").json()
    assert all(i["job"]["work_mode"] == "remote" for i in remote["items"])
    high = client.get("/api/recommendations?min_score=101")
    assert high.status_code == 422
    assert client.get("/api/recommendations?method=magic").status_code == 422


def test_recommendation_with_sparse_profile_degrades_gracefully(client):
    """Missing skills / experience / preferences: still scores in bounds, and warns."""
    client.put("/api/profile", json={"headline": "Generalist"})
    body = client.get("/api/recommendations?limit=5").json()
    assert body["warnings"]
    for item in body["items"]:
        assert_match_shape(item["match"])
        comps = item["match"]["components"]
        assert comps["experience"]["applicable"] is False
        assert comps["location"]["applicable"] is False


def test_match_explanation_for_one_job(client):
    top = client.get("/api/recommendations?limit=1").json()["items"][0]
    detail = client.get(f"/api/recommendations/{top['job']['id']}").json()
    assert detail["rank"] == top["rank"] == 1
    assert detail["match"]["score"] == top["match"]["score"]
    assert client.get("/api/recommendations/99999").status_code == 404


def test_save_job_and_update_status(client):
    job_id = client.get("/api/jobs?limit=1").json()["items"][0]["id"]
    saved = client.put(f"/api/applications/{job_id}", json={"status": "saved"})
    assert saved.status_code == 200 and saved.json()["status"] == "saved"
    applied = client.put(f"/api/applications/{job_id}", json={"status": "applied", "notes": "Sent CV"}).json()
    assert applied["status"] == "applied" and applied["notes"] == "Sent CV"
    listing = client.get("/api/applications").json()
    assert listing["counts"] == {"applied": 1}
    assert listing["items"][0]["match"] is not None
    assert client.get(f"/api/jobs/{job_id}").json()["application_status"] == "applied"
    assert client.delete(f"/api/applications/{job_id}").status_code == 204
    assert client.delete(f"/api/applications/{job_id}").status_code == 404
    assert client.get("/api/applications").json()["items"] == []


def test_application_validation(client):
    assert client.put("/api/applications/1", json={"status": "hired"}).status_code == 422
    assert client.put("/api/applications/99999", json={"status": "saved"}).status_code == 404


# ----------------------------------------------------------- recruiter workflow
def test_recruiter_ranks_candidates_for_stored_job(client):
    r = client.post("/api/recruiter/match", json={"job_id": 1, "limit": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["total_candidates"] >= 15
    scores = [i["match"]["score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)
    for item in body["items"]:
        assert_match_shape(item["match"])
        m = item["match"]
        assert set(m["matched_required"]).isdisjoint(m["missing_required"])


def test_recruiter_adhoc_job_infers_skills(client):
    payload = {"job": {"title": "ML Engineer", "description": "Train models in Python with PyTorch and deploy using Docker."}}
    body = client.post("/api/recruiter/match", json=payload).json()
    assert body["job"]["skills_inferred_from_text"] is True
    assert "pytorch" in body["job"]["required_skills"]
    assert body["items"]


def test_recruiter_best_candidate_for_specific_job_is_relevant(client):
    payload = {"job": {
        "title": "Machine Learning Engineer",
        "description": "Build recommender systems and NLP models in Python using scikit-learn.",
        "required_skills": ["python", "scikit-learn", "nlp"],
    }}
    top = client.post("/api/recruiter/match", json=payload).json()["items"][0]
    assert top["match"]["matched_required"], "top candidate should match at least one required skill"
    assert top["match"]["score"] >= 40


def test_recruiter_tfidf_and_min_score(client):
    body = client.post("/api/recruiter/match", json={"job_id": 2, "method": "tfidf"}).json()
    assert body["method"] == "tfidf"
    filtered = client.post("/api/recruiter/match", json={"job_id": 2, "min_score": 60}).json()
    assert all(i["match"]["score"] >= 60 for i in filtered["items"])


def test_recruiter_validation(client):
    assert client.post("/api/recruiter/match", json={}).status_code == 422
    both = {"job_id": 1, "job": {"title": "Engineer", "description": "A sufficiently long description here."}}
    assert client.post("/api/recruiter/match", json=both).status_code == 422
    assert client.post("/api/recruiter/match", json={"job_id": 99999}).status_code == 404
    assert client.post("/api/recruiter/match", json={"job": {"title": "x", "description": "short"}}).status_code == 422
    assert client.post("/api/recruiter/match", json={"job_id": 1, "limit": 500}).status_code == 422


def test_recruiter_output_has_no_protected_attributes(client):
    body = client.post("/api/recruiter/match", json={"job_id": 1}).text.lower()
    for term in ('"gender"', '"age"', '"ethnicity"', '"religion"', '"photo"', '"nationality"'):
        assert term not in body


def test_candidate_endpoints(client):
    cands = client.get("/api/candidates").json()
    assert len(cands) >= 15 and all(c["is_synthetic"] for c in cands)
    assert client.get(f"/api/candidates/{cands[0]['id']}").status_code == 200
    assert client.get("/api/candidates/99999").status_code == 404
    assert client.get("/api/candidates?q=zzzzqqqq").json() == []


# ------------------------------------------------------------------- evaluation
def test_evaluation_endpoint_returns_real_metrics(client):
    r = client.get("/api/evaluation?generated_per_family=2")
    assert r.status_code == 200
    body = r.json()
    assert body["synthetic"] is True and body["caveats"]
    for direction in body["directions"].values():
        assert {"random", "tfidf", "hybrid"} <= set(direction["methods"])
        for method in direction["methods"].values():
            for name, stat in method["metrics"].items():
                assert 0 <= stat["mean"] <= 1, name
                assert stat["ci_low"] <= stat["mean"] + 1e-9 <= stat["ci_high"] + 2e-9
        assert direction["methods"]["hybrid"]["metrics"]["ndcg@5"]["mean"] > direction["methods"]["random"]["metrics"]["ndcg@5"]["mean"]
    assert client.get("/api/evaluation?generated_per_family=99").status_code == 422

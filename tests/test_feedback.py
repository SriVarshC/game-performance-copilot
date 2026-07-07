import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

# Payload guaranteed to produce recommendations
RECOMMEND_PAYLOAD = {
    "game_genre":  "fps_aaa",
    "resolution":  "2560x1440",
    "preset":      "ultra",
    "ray_tracing": 1,
    "upscaling":   "none"
}


# ── Helper: get a real recommendation ID from DB ──────────────────────────────
def _get_first_rec_id(auth_headers) -> int | None:
    resp = client.post("/api/recommend", json=RECOMMEND_PAYLOAD, headers=auth_headers)
    recs = resp.json().get("recommendations", [])
    return recs[0]["id"] if recs else None


# ── /api/feedback/summary ─────────────────────────────────────────────────────
def test_feedback_summary_returns_200(auth_headers):
    response = client.get("/api/feedback/summary", headers=auth_headers)
    assert response.status_code == 200


def test_feedback_summary_has_status_success(auth_headers):
    response = client.get("/api/feedback/summary", headers=auth_headers)
    assert response.json()["status"] == "success"


def test_feedback_summary_required_fields(auth_headers):
    data = client.get("/api/feedback/summary", headers=auth_headers).json()
    for field in ["total_recommendations", "feedback_given",
                  "helpful", "not_helpful", "helpful_percentage", "by_category"]:
        assert field in data, f"Missing field: {field}"


def test_feedback_summary_counts_non_negative(auth_headers):
    data = client.get("/api/feedback/summary", headers=auth_headers).json()
    assert data["total_recommendations"] >= 0
    assert data["helpful"]     >= 0
    assert data["not_helpful"] >= 0
    assert 0.0 <= data["helpful_percentage"] <= 100.0


# ── /api/feedback/{id} ────────────────────────────────────────────────────────
def test_feedback_submit_helpful(auth_headers):
    rec_id = _get_first_rec_id(auth_headers)
    if rec_id is None:
        pytest.skip("No recommendations returned — cannot test feedback")
    response = client.post(f"/api/feedback/{rec_id}", json={"was_helpful": True}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_feedback_submit_not_helpful(auth_headers):
    rec_id = _get_first_rec_id(auth_headers)
    if rec_id is None:
        pytest.skip("No recommendations returned — cannot test feedback")
    response = client.post(f"/api/feedback/{rec_id}", json={"was_helpful": False}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["was_helpful"] is False


def test_feedback_response_contains_id(auth_headers):
    rec_id = _get_first_rec_id(auth_headers)
    if rec_id is None:
        pytest.skip("No recommendations returned — cannot test feedback")
    data = client.post(f"/api/feedback/{rec_id}", json={"was_helpful": True}, headers=auth_headers).json()
    assert "id" in data
    assert data["id"] == rec_id


def test_feedback_updates_summary(auth_headers):
    """After submitting helpful feedback, helpful count should be >= 1."""
    rec_id = _get_first_rec_id(auth_headers)
    if rec_id is None:
        pytest.skip("No recommendations returned — cannot test feedback")
    client.post(f"/api/feedback/{rec_id}", json={"was_helpful": True}, headers=auth_headers)
    summary = client.get("/api/feedback/summary", headers=auth_headers).json()
    assert summary["helpful"] >= 1


def test_recommend_response_includes_ids(auth_headers):
    """Every recommendation in POST /api/recommend must have an 'id' field."""
    data = client.post("/api/recommend", json=RECOMMEND_PAYLOAD, headers=auth_headers).json()
    for rec in data["recommendations"]:
        assert "id" in rec, f"Recommendation missing 'id': {rec}"
        assert isinstance(rec["id"], int)
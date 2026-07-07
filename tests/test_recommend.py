import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "game_genre": "fps_competitive",
    "resolution": "1920x1080",
    "preset": "ultra",
    "ray_tracing": 1,
    "upscaling": "none"
}


def test_recommend_returns_200(auth_headers):
    """Recommend endpoint should return HTTP 200."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    assert response.status_code == 200


def test_recommend_status_success(auth_headers):
    """Response status field should be 'success'."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert data["status"] == "success"


def test_recommend_returns_list(auth_headers):
    """Recommendations field should be a list."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_recommend_not_empty(auth_headers):
    """Ultra preset + ray tracing should trigger at least one recommendation."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert data["count"] > 0


def test_recommend_max_six(auth_headers):
    """Recommendation engine should return at most 6 items."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert data["count"] <= 6


def test_recommend_fields_present(auth_headers):
    """Each recommendation must have all required fields."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    for rec in data["recommendations"]:
        assert "action" in rec
        assert "estimated_fps_gain" in rec
        assert "category" in rec
        assert "difficulty" in rec


def test_recommend_game_settings_echoed(auth_headers):
    """Response should echo back the game settings submitted."""
    response = client.post("/api/recommend", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "game_settings" in data
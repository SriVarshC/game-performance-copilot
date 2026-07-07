import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "game_genre": "fps_competitive",
    "resolution": "1920x1080",
    "preset": "high",
    "ray_tracing": 0,
    "upscaling": "none",
    "gpu_utilization": 75.0,
    "vram_used_mb": 2048.0,
    "cpu_utilization": 45.0,
    "ram_utilization": 82.0,
    "gpu_temperature": 65.0,
    "gpu_clock_mhz": 1500.0,
    "gpu_power_watts": 60.0
}

VALID_TIERS = {"Excellent", "Playable", "Acceptable", "Poor"}


def test_predict_returns_200(auth_headers):
    """Predict endpoint should return HTTP 200 with valid input."""
    response = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers)
    assert response.status_code == 200


def test_predict_fps_is_positive(auth_headers):
    """Predicted FPS should be a positive number."""
    response = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "predicted_fps" in data
    assert data["predicted_fps"] > 0


def test_predict_frame_time_is_positive(auth_headers):
    """Frame time in ms should be a positive number."""
    response = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "frame_time_ms" in data
    assert data["frame_time_ms"] > 0


def test_predict_valid_performance_tier(auth_headers):
    """Performance tier must contain one of the four valid tier keywords."""
    response = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "performance_tier" in data
    tier = data["performance_tier"]
    VALID_KEYWORDS = ["Excellent", "Playable", "Acceptable", "Poor"]
    assert any(keyword in tier for keyword in VALID_KEYWORDS), \
        f"Unexpected performance_tier value: '{tier}'"


def test_predict_model_name_returned(auth_headers):
    """Response must include the model name used."""
    response = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers)
    data = response.json()
    assert "model_name" in data


def test_predict_ray_tracing_on(auth_headers):
    """Predict should work fine with ray tracing enabled."""
    payload = {**VALID_PAYLOAD, "ray_tracing": 1, "upscaling": "dlss"}
    response = client.post("/api/predict", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["predicted_fps"] > 0


def test_predict_ultra_preset(auth_headers):
    """Ultra preset with high GPU load should still return valid response."""
    payload = {**VALID_PAYLOAD, "preset": "ultra", "gpu_utilization": 98.0}
    response = client.post("/api/predict", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["predicted_fps"] > 0
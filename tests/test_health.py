import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_returns_200():
    """Health endpoint should return HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_status_healthy():
    """Health endpoint should report status as healthy."""
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_model_loaded():
    """LightGBM model should be loaded."""
    response = client.get("/api/health")
    data = response.json()
    assert data["model_loaded"] is True


def test_health_model_name_lightgbm():
    """Best model should be LightGBM."""
    response = client.get("/api/health")
    data = response.json()
    assert data["model_name"] == "LightGBM"


def test_health_api_version():
    """API version should be 2.0.0."""
    response = client.get("/api/health")
    data = response.json()
    assert data["api_version"] == "2.0.0"
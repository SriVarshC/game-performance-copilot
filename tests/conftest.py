"""
Shared pytest fixtures — Phase 8.
Registers a throwaway test user once per test session and provides
Authorization headers for every protected-route test.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


@pytest.fixture(scope="session")
def auth_headers():
    """
    Registers a test user (or logs in if it already exists from a
    previous run) and returns headers with a valid Bearer token.
    """
    credentials = {
        "username": "pytest_test_user",
        "email":    "pytest_test_user@example.com",
        "password": "pytest_password_123",
    }

    # Try registering; if the user already exists from a prior test run,
    # fall back to logging in instead.
    resp = client.post("/api/auth/register", json=credentials)
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        login_resp = client.post("/api/auth/login", json={
            "username": credentials["username"],
            "password": credentials["password"],
        })
        assert login_resp.status_code == 200, f"Test user login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
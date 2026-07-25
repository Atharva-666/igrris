"""Tests for the FastAPI backend (api.py)."""

import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestPredictEndpoint:
    def test_valid_prediction(self):
        response = client.post(
            "/predict",
            json={"text": "Congratulations! You won a free vacation!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "label" in data
        assert "confidence" in data
        assert data["label"] in ("spam", "ham")
        assert 0.0 <= data["confidence"] <= 1.0

    def test_ham_message(self):
        response = client.post(
            "/predict",
            json={"text": "Hi, can we reschedule our meeting to 3 PM?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "ham"

    def test_empty_text_returns_422(self):
        response = client.post("/predict", json={"text": ""})
        assert response.status_code == 422

    def test_missing_text_field_returns_422(self):
        response = client.post("/predict", json={})
        assert response.status_code == 422

    def test_invalid_method_returns_405(self):
        response = client.get("/predict")
        assert response.status_code == 405

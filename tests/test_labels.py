"""
test_labels.py — Unit tests for Gmail label manager and delete labels endpoint.
"""

import sys
import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.labels.manager import (
    delete_managed_label,
    delete_all_managed_labels,
    _SYSTEM_LABEL_ALIASES,
)
from backend.igrris_api import app

client = TestClient(app)


class TestLabelManagerDelete:
    def test_delete_system_alias_label_skipped(self):
        service = MagicMock()
        # 'Spam' is mapped to 'SPAM' system label
        result = delete_managed_label(service, "Spam")
        assert result is False
        service.users().labels().delete.assert_not_called()

    def test_delete_nonexistent_label_returns_true(self):
        service = MagicMock()
        service.users().labels().list().execute.return_value = {"labels": []}
        result = delete_managed_label(service, "NonExistentLabel")
        assert result is True

    def test_delete_existing_managed_label(self):
        service = MagicMock()
        service.users().labels().list().execute.return_value = {
            "labels": [{"name": "Phishing", "id": "Label_123"}]
        }
        service.users().labels().delete().execute.return_value = {}

        result = delete_managed_label(service, "Phishing")
        assert result is True

    def test_delete_all_managed_labels(self):
        service = MagicMock()
        service.users().labels().list().execute.return_value = {
            "labels": [
                {"name": "Phishing", "id": "Label_1"},
                {"name": "Security", "id": "Label_2"},
                {"name": "SPAM", "id": "SPAM"},
            ]
        }
        service.users().labels().delete().execute.return_value = {}

        summary = delete_all_managed_labels(service)
        assert "Phishing" in summary["deleted"]
        assert "Security" in summary["deleted"]
        assert "Spam" in summary["skipped_system"]


class TestDeleteLabelsEndpoint:
    def test_delete_labels_unauthorized_when_no_creds(self, monkeypatch):
        monkeypatch.setattr("backend.igrris_api.load_credentials", lambda: None)
        response = client.post("/labels/delete", json={})
        assert response.status_code == 401

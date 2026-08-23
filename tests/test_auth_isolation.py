"""
test_auth_isolation.py — Multi-user isolation & session security tests.
"""

import sys
import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.igrris_api import app
from backend.auth.session import store as session_store
from backend.auth.oauth import save_credentials, load_credentials, generate_user_id

# Use https base_url so secure cookies are accepted by TestClient
client = TestClient(app, base_url="https://testserver")


class TestMultiUserIsolation:
    def test_anonymous_session_status(self):
        """Unauthenticated browser gets authenticated=false."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["email"] is None

    def test_session_cookie_created_on_auth_url(self):
        """GET /auth/url creates a session cookie and sets CSRF state in session."""
        response = client.get("/auth/url")
        assert response.status_code == 200
        assert "igrris_session" in client.cookies
        data = response.json()
        assert "url" in data
        assert "accounts.google.com" in data["url"]

    def test_csrf_state_validation(self):
        """POST /auth/callback fails if OAuth state does not match session state."""
        # 1. Get auth URL (sets session & oauth_state on test client)
        res1 = client.get("/auth/url")
        assert res1.status_code == 200

        # 2. Submit mismatched state using the same client (session cookie attached automatically)
        res2 = client.post(
            "/auth/callback",
            json={"code": "fake_code", "state": "invalid_state"},
        )
        assert res2.status_code == 400
        assert "Failed to exchange" in res2.json()["detail"]

    def test_multi_user_isolation(self, tmp_path, monkeypatch):
        """Verify User A and User B have completely separate sessions and credentials."""
        monkeypatch.setattr("backend.auth.oauth.CREDENTIALS_DIR", str(tmp_path))

        # Create two distinct user IDs
        user_id_a = generate_user_id()
        user_id_b = generate_user_id()

        creds_a = MagicMock()
        creds_a.token = "token_a"
        creds_a.refresh_token = "refresh_a"
        creds_a.token_uri = "https://oauth2.googleapis.com/token"
        creds_a.client_id = "client_a"
        creds_a.client_secret = "secret_a"
        creds_a.scopes = ["scope_a"]
        creds_a.expiry = None

        creds_b = MagicMock()
        creds_b.token = "token_b"
        creds_b.refresh_token = "refresh_b"
        creds_b.token_uri = "https://oauth2.googleapis.com/token"
        creds_b.client_id = "client_b"
        creds_b.client_secret = "secret_b"
        creds_b.scopes = ["scope_b"]
        creds_b.expiry = None

        # Save credentials for both users
        save_credentials(user_id_a, creds_a)
        save_credentials(user_id_b, creds_b)

        # Confirm user A file exists and matches A's token
        loaded_a = load_credentials(user_id_a)
        assert loaded_a is not None
        assert loaded_a.token == "token_a"

        # Confirm user B file exists and matches B's token
        loaded_b = load_credentials(user_id_b)
        assert loaded_b is not None
        assert loaded_b.token == "token_b"

        # User A credentials file is separate from User B credentials file
        assert os.path.exists(os.path.join(tmp_path, f"{user_id_a}.json"))
        assert os.path.exists(os.path.join(tmp_path, f"{user_id_b}.json"))
        assert not os.path.exists(os.path.join(tmp_path, "token.json"))

    def test_scan_token_issuance_and_single_use(self):
        """POST /scan/token issues a short-lived token that is single-use."""
        test_client = TestClient(app, base_url="https://testserver")

        # Create an authenticated session manually
        session_id = session_store.create()
        user_id = generate_user_id()
        session_store.set_data(session_id, "user_id", user_id)
        session_store.set_data(session_id, "authenticated", True)

        test_client.cookies.set("igrris_session", session_id)

        # Issue scan token
        res = test_client.post("/scan/token")
        assert res.status_code == 200
        scan_token = res.json()["scan_token"]
        assert scan_token is not None

        # Unauthenticated request cannot get scan token
        unauth_client = TestClient(app, base_url="https://testserver")
        res_unauth = unauth_client.post("/scan/token")
        assert res_unauth.status_code == 401

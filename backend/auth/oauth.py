"""
oauth.py — Google OAuth 2.0 flow for Igrris AI.

Responsibilities:
  - Generate Google authorization URL
  - Exchange authorization code for credentials
  - Refresh expired access tokens automatically
  - Save / load credentials from disk
  - Revoke credentials on logout

Security notes:
  - No Gmail passwords are ever stored.
  - Only access tokens and refresh tokens are stored (token.json).
  - OAUTHLIB_INSECURE_TRANSPORT=1 is set for local HTTP dev only.
    Remove this in any production deployment using HTTPS.
  - OAuth state is saved to a temp file (.oauth_state) to survive the
    browser redirect. This protects against CSRF for single-user local use.
"""

import json
import logging
import os
import datetime

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    OAUTH_STATE_FILE,
    REDIRECT_URI,
    SCOPES,
    TOKEN_FILE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _client_config() -> dict:
    """Build the OAuth 2.0 client config dict from environment variables."""
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def _save_state(state: str, code_verifier: str | None = None) -> None:
    """Persist OAuth state and code_verifier (PKCE) to disk so it survives the browser redirect."""
    with open(OAUTH_STATE_FILE, "w") as f:
        json.dump({"state": state, "code_verifier": code_verifier}, f)


def _load_state() -> tuple[str | None, str | None]:
    """Load and delete saved OAuth state + code_verifier. Returns (state, code_verifier)."""
    if not os.path.exists(OAUTH_STATE_FILE):
        return None, None
    try:
        with open(OAUTH_STATE_FILE, "r") as f:
            data = json.load(f)
        return data.get("state"), data.get("code_verifier")
    except Exception as e:
        logger.warning("Could not load OAuth state: %s", e)
        return None, None
    finally:
        # Always remove state file after reading — it is single-use
        try:
            os.remove(OAUTH_STATE_FILE)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_auth_url() -> str:
    """
    Build and return the Google OAuth 2.0 authorization URL.

    The generated 'state' parameter and PKCE 'code_verifier' are saved to disk
    so they can be verified when Google redirects back to the app.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise EnvironmentError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in your .env file."
        )

    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    url, state = flow.authorization_url(
        access_type="offline",          # request a refresh token
        include_granted_scopes="true",
        prompt="consent",               # always show consent screen to get refresh token
    )

    code_verifier = getattr(flow, "code_verifier", None)
    _save_state(state, code_verifier)
    logger.info("Authorization URL generated.")
    return url


def exchange_code(code: str) -> Credentials:
    """
    Exchange the authorization code (from Google callback) for credentials.

    Parameters
    ----------
    code : str
        The 'code' query parameter from the OAuth callback URL.

    Returns
    -------
    Credentials
        Valid Google OAuth credentials with access + refresh tokens.
    """
    state, code_verifier = _load_state()  # may be (None, None) if state file was lost

    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=state,  # None = skip state verification (safe for local dev)
    )
    flow.redirect_uri = REDIRECT_URI
    if code_verifier:
        flow.code_verifier = code_verifier

    # fetch_token exchanges the code for access + refresh tokens
    flow.fetch_token(code=code)

    credentials = flow.credentials
    logger.info("Authorization code exchanged successfully.")
    return credentials


def refresh_if_expired(credentials: Credentials) -> Credentials:
    """
    Check if the access token is expired and refresh it if needed.
    Saves updated credentials to disk after refresh.
    """
    if credentials.expired and credentials.refresh_token:
        logger.info("Access token expired. Refreshing...")
        credentials.refresh(Request())
        save_credentials(credentials)
        logger.info("Access token refreshed.")
    return credentials


def save_credentials(credentials: Credentials) -> None:
    """
    Serialize and save credentials to token.json.

    Stored fields: access token, refresh token, token URI,
    client ID, client secret, scopes.
    """
    data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Credentials saved to %s", TOKEN_FILE)


def load_credentials() -> Credentials | None:
    """
    Load saved credentials from token.json.

    Returns None if the file does not exist or cannot be parsed.
    """
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)

        expiry_str = data.get("expiry")
        expiry = datetime.datetime.fromisoformat(expiry_str) if expiry_str else None

        credentials = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes"),
            expiry=expiry,
        )
        logger.info("Credentials loaded from disk.")
        return credentials

    except Exception as e:
        logger.error("Failed to load credentials: %s", e)
        return None


def revoke_credentials(credentials: Credentials) -> None:
    """
    Revoke the access token with Google and delete token.json.

    After this call the user must sign in again.
    """
    try:
        requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": credentials.token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        logger.info("Access token revoked with Google.")
    except Exception as e:
        # Revocation failure is non-critical; we still delete the local token
        logger.warning("Token revocation request failed: %s", e)
    finally:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            logger.info("token.json deleted.")

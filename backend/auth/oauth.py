"""
oauth.py — Google OAuth 2.0 flow for Igrris AI (multi-user edition).

Design principles:
  - No global token.json — every user has credentials/<user_id>.json
  - No global .oauth_state file — OAuth state is stored in the server-side session
  - user_id is a cryptographically-random internal UUID (NOT the Google 'sub')
  - Google 'sub' is stored as an identity field alongside user_id
  - Path traversal is prevented by validating user_id as UUID4 format

Session-aware API:
    get_auth_url(session_id)           → stores state in session, returns Google URL
    exchange_code(code, session_id)    → validates state from session, returns Credentials
    save_credentials(user_id, creds)   → writes credentials/<user_id>.json
    load_credentials(user_id)          → reads credentials/<user_id>.json
    refresh_if_expired(user_id, creds) → refreshes and saves back to same user file
    revoke_credentials(user_id, creds) → revokes with Google, deletes user's file only

Security notes:
  - OAUTHLIB_INSECURE_TRANSPORT is only enabled when DEBUG=true (local HTTP dev).
    config.py sets this conditionally — never enabled in Railway production.
  - Refresh tokens are never sent to the browser; they live only in the cred file.
  - State + code_verifier live in the server-side session for the duration of OAuth.
"""

import json
import logging
import os
import re
import uuid
import datetime

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    CREDENTIALS_DIR,
    REDIRECT_URI,
    SCOPES,
)
from backend.auth.session import store as session_store

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# UUID validation — prevents path traversal
# ---------------------------------------------------------------------------

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _validate_user_id(user_id: str) -> None:
    """Raise ValueError if user_id is not a valid UUID4 (prevents path traversal)."""
    if not _UUID_RE.match(user_id):
        raise ValueError(f"Invalid user_id format: {user_id!r}")


def _cred_path(user_id: str) -> str:
    """Return the absolute path for a user's credential file."""
    _validate_user_id(user_id)
    os.makedirs(CREDENTIALS_DIR, exist_ok=True)
    return os.path.join(CREDENTIALS_DIR, f"{user_id}.json")


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


# ---------------------------------------------------------------------------
# Public API — session-aware
# ---------------------------------------------------------------------------

def get_auth_url(session_id: str) -> str:
    """
    Build and return the Google OAuth 2.0 authorization URL.

    The generated 'state' and PKCE 'code_verifier' are stored in the server-side
    session (not on disk), so they are isolated per browser session.

    Parameters
    ----------
    session_id : str
        The caller's session ID (used to store OAuth state).
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise EnvironmentError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in your .env file."
        )

    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    code_verifier = getattr(flow, "code_verifier", None)

    # Store state in this browser's session only — no global file
    session_store.set_data(session_id, "oauth_state", state)
    session_store.set_data(session_id, "code_verifier", code_verifier)

    logger.info("Authorization URL generated for session %s.", session_id)
    return url


def exchange_code(code: str, session_id: str) -> Credentials:
    """
    Exchange the authorization code for credentials.

    Reads (and validates) the OAuth state from the server-side session,
    so only the browser that initiated the OAuth flow can complete it.

    Parameters
    ----------
    code : str
        The 'code' query parameter from the OAuth callback URL.
    session_id : str
        The caller's session ID (used to retrieve and validate OAuth state).
    """
    session_data = session_store.get(session_id)
    if session_data is None:
        raise ValueError("No active session found. OAuth flow may have expired.")

    state = session_data.get("oauth_state")
    code_verifier = session_data.get("code_verifier")

    if not state:
        raise ValueError("No OAuth state found in session. Possible CSRF attack or expired session.")

    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=state,  # Enforce CSRF validation
    )
    flow.redirect_uri = REDIRECT_URI

    if code_verifier:
        flow.code_verifier = code_verifier

    # Exchange code for tokens — this validates the state parameter
    flow.fetch_token(code=code)

    # Clear state from session immediately after use (single-use)
    session_store.set_data(session_id, "oauth_state", None)
    session_store.set_data(session_id, "code_verifier", None)

    logger.info("Authorization code exchanged successfully for session %s.", session_id)
    return flow.credentials


def generate_user_id() -> str:
    """
    Generate a cryptographically-random internal user UUID.

    This is NOT the Google 'sub' — it is IGRRIS's own internal identifier.
    The Google 'sub' is stored as a separate field for identity reference only.
    """
    return str(uuid.uuid4())


def save_credentials(user_id: str, credentials: Credentials) -> None:
    """
    Serialize and save credentials to credentials/<user_id>.json.

    Only the tokens and OAuth config are stored. The file is named by the
    internal user_id (UUID), never by email or Google sub.
    """
    _validate_user_id(user_id)
    path = _cred_path(user_id)

    data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

    # Write atomically by using a tmp file then rename (avoids partial writes)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up tmp file if something went wrong
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    logger.info("Credentials saved for user %s.", user_id)


def load_credentials(user_id: str) -> Credentials | None:
    """
    Load credentials for a specific user from credentials/<user_id>.json.

    Returns None if the file does not exist or cannot be parsed.
    """
    _validate_user_id(user_id)
    path = _cred_path(user_id)

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
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
        logger.info("Credentials loaded for user %s.", user_id)
        return credentials

    except Exception as e:
        logger.error("Failed to load credentials for user %s: %s", user_id, e)
        return None


def refresh_if_expired(user_id: str, credentials: Credentials) -> Credentials:
    """
    Check if the access token is expired and refresh it if needed.

    Saves updated credentials back to the SAME user's file after refresh.
    Never writes to a global token.json.
    """
    if credentials.expired and credentials.refresh_token:
        logger.info("Access token expired for user %s. Refreshing...", user_id)
        credentials.refresh(Request())
        save_credentials(user_id, credentials)
        logger.info("Access token refreshed for user %s.", user_id)
    return credentials


def revoke_credentials(user_id: str, credentials: Credentials) -> None:
    """
    Revoke the access token with Google and delete this user's credential file.

    Only affects credentials/<user_id>.json — never touches any other user's file.
    """
    _validate_user_id(user_id)

    try:
        requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": credentials.token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        logger.info("Access token revoked with Google for user %s.", user_id)
    except Exception as e:
        # Revocation failure is non-critical; we still delete the local file
        logger.warning("Token revocation request failed for user %s: %s", user_id, e)
    finally:
        path = _cred_path(user_id)
        if os.path.exists(path):
            os.remove(path)
            logger.info("Credential file deleted for user %s.", user_id)


def get_google_user_info(credentials: Credentials) -> dict:
    """
    Fetch the Google user's profile from the userinfo endpoint.

    Returns a dict with keys: sub, email, name, picture (empty dict on failure).
    The 'sub' is Google's stable account identifier.
    """
    try:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning("Failed to fetch Google user info: %s", e)
    return {}

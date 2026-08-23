"""
session.py — Server-side session store for Igrris AI.

Design principles:
  - session_id  → identifies the BROWSER (set in HTTP-only cookie)
  - user_id     → identifies the authenticated IGRRIS user (internal UUID, NOT Google sub)
  - google_sub  → the stable Google account identifier (stored inside the session only)

Session data structure:
  {
    "oauth_state":    str | None,   # CSRF state for the current OAuth attempt
    "code_verifier":  str | None,   # PKCE verifier
    "user_id":        str | None,   # Internal UUID (once authenticated)
    "google_sub":     str | None,   # Google's stable 'sub' field (for reference)
    "authenticated":  bool,
  }

Security:
  - Sessions are stored server-side only (not in the cookie).
  - The cookie carries only the session_id (UUID4).
  - Cookie is HttpOnly=True, Secure=True, SameSite=None (required for cross-origin
    Vercel → Railway architecture).
  - SameSite=None requires Secure=True per RFC 6265bis.
  - Session fixation is prevented by regenerating session_id after successful auth.
"""

import logging
import os
import uuid
from typing import Any

from fastapi import Request, Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COOKIE_NAME = "igrris_session"

# 7-day session lifetime in seconds
SESSION_MAX_AGE = 60 * 60 * 24 * 7

# Read from env so Railway vs local can differ
_IS_PRODUCTION = os.environ.get("DEBUG", "false").lower() != "true"


# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------

class _SessionStore:
    """
    Thread-safe(ish) in-memory session store.

    For a single-process Railway deployment (one Uvicorn worker) this is
    sufficient. For multi-worker deployments, switch this to Redis or a DB.
    """

    def __init__(self) -> None:
        # {session_id: {key: value}}
        self._store: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def create(self) -> str:
        """Generate a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._store[session_id] = {
            "oauth_state": None,
            "code_verifier": None,
            "user_id": None,
            "google_sub": None,
            "authenticated": False,
        }
        logger.debug("Session created: %s", session_id)
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Return the session dict or None if the session does not exist."""
        return self._store.get(session_id)

    def set_data(self, session_id: str, key: str, value: Any) -> None:
        """Update a single key in an existing session."""
        session = self._store.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} does not exist")
        session[key] = value

    def delete(self, session_id: str) -> None:
        """Remove a session entirely."""
        self._store.pop(session_id, None)
        logger.debug("Session deleted: %s", session_id)

    def regenerate(self, old_session_id: str) -> str:
        """
        Prevent session fixation: copy data to a new session ID and delete the old one.
        Call this immediately after successful authentication.
        """
        old_data = self._store.get(old_session_id, {})
        new_session_id = str(uuid.uuid4())
        self._store[new_session_id] = dict(old_data)
        self._store.pop(old_session_id, None)
        logger.debug("Session regenerated: %s → %s", old_session_id, new_session_id)
        return new_session_id

    def __len__(self) -> int:
        return len(self._store)


# Singleton — imported everywhere in the app
store = _SessionStore()


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------

def get_session_id(request: Request) -> str | None:
    """Read the session cookie and return its value, or None if absent."""
    return request.cookies.get(COOKIE_NAME)


def get_or_create_session(request: Request, response: Response) -> tuple[str, dict]:
    """
    Return the current (session_id, session_data).

    If no valid session cookie exists, create a new anonymous session and
    set the cookie on the provided response object.
    """
    session_id = get_session_id(request)
    if session_id:
        data = store.get(session_id)
        if data is not None:
            return session_id, data

    # No valid session — create a fresh one
    session_id = store.create()
    _set_cookie(response, session_id)
    return session_id, store.get(session_id)  # type: ignore[return-value]


def get_authenticated_session(request: Request) -> tuple[str, dict] | tuple[None, None]:
    """
    Return (session_id, session_data) only if the session is authenticated.
    Returns (None, None) otherwise — caller should respond with 401.
    """
    session_id = get_session_id(request)
    if not session_id:
        return None, None
    data = store.get(session_id)
    if data is None or not data.get("authenticated"):
        return None, None
    return session_id, data


def promote_session(old_session_id: str, response: Response, **updates: Any) -> str:
    """
    Regenerate session ID (prevents fixation) and apply updates to the new session.
    Set the new cookie on the response.
    Returns the new session_id.
    """
    new_session_id = store.regenerate(old_session_id)
    for key, value in updates.items():
        store.set_data(new_session_id, key, value)
    _set_cookie(response, new_session_id)
    return new_session_id


def delete_session(session_id: str, response: Response) -> None:
    """Destroy a session and expire its cookie."""
    store.delete(session_id)
    _expire_cookie(response)


# ---------------------------------------------------------------------------
# Internal cookie setters
# ---------------------------------------------------------------------------

def _set_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=_IS_PRODUCTION,   # False only during local HTTP dev (DEBUG=true)
        samesite="none" if _IS_PRODUCTION else "lax",
        path="/",
    )


def _expire_cookie(response: Response) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value="",
        max_age=0,
        httponly=True,
        secure=_IS_PRODUCTION,
        samesite="none" if _IS_PRODUCTION else "lax",
        path="/",
    )

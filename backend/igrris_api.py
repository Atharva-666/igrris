"""
igrris_api.py — FastAPI layer for Igrris AI (multi-user edition).

Multi-user authentication architecture:
    Browser
        ↓  HTTP-only session cookie (igrris_session=<UUID>)
    Railway FastAPI
        ↓  server-side session store  (session_id → {user_id, oauth_state, ...})
        ↓  credentials/<user_id>.json (per-user credential file, never shared)
        ↓  Google OAuth credentials
        ↓  Gmail API

Session/User ID separation:
    session_id  — identifies the BROWSER (cookie value)
    user_id     — internal UUID for the authenticated IGRRIS user (NOT Google sub)
    google_sub  — Google's stable account identifier (stored in session for reference)

SSE Scan token flow (required because EventSource cannot send cookies):
    POST /scan/token  → validate session → issue short-lived scan_token (60s, single-use)
    GET  /scan/stream?scan_token=<token>  → validate token → look up user → stream SSE

Endpoints:
    GET  /health              — liveness probe
    GET  /auth/url            — returns Google OAuth authorization URL
    POST /auth/callback       — exchanges code → credentials, sets session
    GET  /auth/status         — checks current session's auth status
    POST /auth/logout         — revokes current user's credentials only
    POST /scan/token          — issues a short-lived scan token
    GET  /scan/stream         — streams Gmail scan results via SSE (scan_token auth)
    POST /scan/stop/{scan_id} — cancels an ongoing scan
    POST /predict             — ML spam/ham classification (no auth required)
    GET  /labels              — list Gmail labels for current user
    POST /labels/delete       — delete managed Gmail labels for current user
"""

import logging
import sys
import os
import time
import threading
import uuid

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.auth.oauth import (
    get_auth_url,
    exchange_code,
    load_credentials,
    refresh_if_expired,
    revoke_credentials,
    save_credentials,
    generate_user_id,
    get_google_user_info,
)
from backend.auth.session import (
    get_or_create_session,
    get_authenticated_session,
    promote_session,
    delete_session,
    store as session_store,
)
from backend.gmail.connector import get_gmail_service
from backend.services.scan_service import run_scan
from backend.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Igrris AI API",
    description="Gmail security assistant — multi-user OAuth + ML scan pipeline.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    from backend.threat_intelligence.startup import init_threat_intelligence
    init_threat_intelligence()


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Set ALLOWED_ORIGINS=https://igrris.vercel.app on Railway.
# Falls back to localhost origins for local development.
# NEVER use allow_origins=["*"] with allow_credentials=True — browsers block it.

_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501"
)
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,          # required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class CallbackRequest(BaseModel):
    code: str
    state: str


class HealthResponse(BaseModel):
    status: str
    version: str = "3.0.0"


class AuthUrlResponse(BaseModel):
    url: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    email: str | None = None
    picture: str | None = None
    name: str | None = None


class ScanTokenResponse(BaseModel):
    scan_token: str


class ScanResponse(BaseModel):
    total: int
    results: list[dict]
    summary: dict


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Email / SMS body text")


class PredictResponse(BaseModel):
    label: str
    confidence: float


class DeleteLabelsRequest(BaseModel):
    label_name: str | None = Field(
        default=None,
        description="Optional specific label name to delete. If omitted, deletes all managed labels.",
    )


class DeleteLabelsResponse(BaseModel):
    status: str
    deleted: list[str]
    failed: list[str]
    skipped_system: list[str]
    message: str


# ---------------------------------------------------------------------------
# Scan token store
# (short-lived, single-use tokens that bridge the EventSource auth gap)
# ---------------------------------------------------------------------------

# {scan_token: {"user_id": str, "expires_at": float, "scan_id": str}}
_scan_tokens: dict[str, dict] = {}
_SCAN_TOKEN_TTL = 60  # seconds

# Global map for cancellation events {scan_id: threading.Event}
active_scans: dict[str, threading.Event] = {}


def _issue_scan_token(user_id: str) -> tuple[str, str]:
    """
    Issue a short-lived (60s), single-use scan token for the given user.

    Returns (scan_token, scan_id).
    scan_token is passed in the EventSource URL query param.
    scan_id is used later to cancel the scan.
    """
    scan_token = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    _scan_tokens[scan_token] = {
        "user_id": user_id,
        "expires_at": time.time() + _SCAN_TOKEN_TTL,
        "scan_id": scan_id,
    }
    # Opportunistically clean expired tokens
    _prune_scan_tokens()
    return scan_token, scan_id


def _consume_scan_token(scan_token: str) -> dict | None:
    """
    Validate and consume a scan token. Returns token data or None if invalid/expired.
    Single-use: token is removed from the store after retrieval.
    """
    entry = _scan_tokens.pop(scan_token, None)
    if entry is None:
        return None
    if time.time() > entry["expires_at"]:
        return None
    return entry


def _prune_scan_tokens() -> None:
    """Remove expired tokens from the store."""
    now = time.time()
    expired = [tok for tok, data in _scan_tokens.items() if now > data["expires_at"]]
    for tok in expired:
        _scan_tokens.pop(tok, None)


# ---------------------------------------------------------------------------
# Helper — load + refresh credentials for the current session
# ---------------------------------------------------------------------------

def _get_user_credentials(session_data: dict):
    """
    Load credentials for the user identified by the session.
    Raises HTTPException 401 if credentials are missing or refresh fails.
    """
    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user in session.",
        )

    creds = load_credentials(user_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials not found. Please sign in again.",
        )

    try:
        creds = refresh_if_expired(user_id, creds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {exc}",
        )

    return user_id, creds


# ---------------------------------------------------------------------------
# Endpoints — system
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Liveness probe — always returns 200 if the server is running."""
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# Endpoints — auth
# ---------------------------------------------------------------------------

@app.get("/auth/url", response_model=AuthUrlResponse, tags=["auth"])
async def auth_url(request: Request, response: Response) -> AuthUrlResponse:
    """
    Generate and return the Google OAuth 2.0 authorization URL.

    Creates or reuses the current browser session.
    OAuth state is stored in the session (not on disk).
    """
    session_id, _ = get_or_create_session(request, response)
    try:
        url = get_auth_url(session_id)
        return AuthUrlResponse(url=url)
    except EnvironmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth misconfiguration: {exc}",
        )


@app.post("/auth/callback", response_model=AuthStatusResponse, tags=["auth"])
async def auth_callback(
    body: CallbackRequest,
    request: Request,
    response: Response,
) -> AuthStatusResponse:
    """
    Exchange the OAuth authorization code for credentials.

    1. Reads the session cookie to identify the initiating browser.
    2. Validates the OAuth state stored in that session (CSRF protection).
    3. Exchanges the authorization code with Google.
    4. Retrieves the Google user identity (sub, email, name, picture).
    5. Creates an internal user_id (UUID) separate from the Google sub.
    6. Saves credentials to credentials/<user_id>.json.
    7. Regenerates session ID (prevents session fixation).
    8. Returns user profile — never returns tokens.
    """
    # Step 1: Get the browser's existing session (must exist — same browser that called /auth/url)
    session_id, session_data = get_or_create_session(request, response)

    try:
        # Step 2 & 3: Validate state + exchange code
        creds = exchange_code(body.code, session_id, body.state)
    except Exception as exc:
        logger.error("OAuth callback failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {exc}",
        )

    # Step 4: Get Google identity — never trust frontend-supplied values
    user_info = get_google_user_info(creds)
    google_sub = user_info.get("sub")
    if not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve Google user identity.",
        )

    # Step 5: Create or reuse internal user_id
    # Check if this Google sub already has a user_id in any existing session
    # (simple approach: always generate a fresh UUID — credential file is keyed by UUID)
    # For persistent credential mapping across sessions, you would look up google_sub → user_id
    # in a DB. For now we generate a new UUID per login (credentials last across refreshes).
    user_id = generate_user_id()

    # Step 6: Save credentials — only to this user's file
    try:
        save_credentials(user_id, creds)
    except Exception as exc:
        logger.error("Failed to save credentials for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save credentials.",
        )

    # Step 7: Regenerate session (prevents fixation) and store user identity
    new_session_id = promote_session(
        session_id,
        response,
        user_id=user_id,
        google_sub=google_sub,
        authenticated=True,
    )

    logger.info(
        "User authenticated: google_sub=%s user_id=%s session=%s",
        google_sub,
        user_id,
        new_session_id,
    )

    # Step 8: Return profile — no tokens
    return AuthStatusResponse(
        authenticated=True,
        email=user_info.get("email"),
        picture=user_info.get("picture"),
        name=user_info.get("name"),
    )


@app.get("/auth/status", response_model=AuthStatusResponse, tags=["auth"])
async def auth_status(request: Request, response: Response) -> AuthStatusResponse:
    """
    Check whether the current browser session is authenticated.

    Uses the session cookie to look up the server-side session, then loads
    that user's credentials. Never reads token.json (gone) or a global file.
    """
    session_id, session_data = get_authenticated_session(request)
    if session_id is None:
        return AuthStatusResponse(authenticated=False)

    user_id = session_data.get("user_id")
    if not user_id:
        return AuthStatusResponse(authenticated=False)

    creds = load_credentials(user_id)
    if not creds:
        return AuthStatusResponse(authenticated=False)

    try:
        creds = refresh_if_expired(user_id, creds)
        user_info = get_google_user_info(creds)
        return AuthStatusResponse(
            authenticated=True,
            email=user_info.get("email"),
            picture=user_info.get("picture"),
            name=user_info.get("name"),
        )
    except Exception as exc:
        logger.warning("Credential refresh failed for user %s: %s", user_id, exc)
        return AuthStatusResponse(authenticated=False)


@app.post("/auth/logout", response_model=AuthStatusResponse, tags=["auth"])
async def auth_logout(request: Request, response: Response) -> AuthStatusResponse:
    """
    Revoke credentials and destroy the current user's session.

    ONLY touches this user's credentials — never affects other sessions.
    """
    session_id, session_data = get_authenticated_session(request)
    if session_id is not None and session_data:
        user_id = session_data.get("user_id")
        if user_id:
            creds = load_credentials(user_id)
            if creds:
                revoke_credentials(user_id, creds)
        delete_session(session_id, response)
        logger.info("User logged out: user_id=%s session=%s", user_id, session_id)

    return AuthStatusResponse(authenticated=False)


# ---------------------------------------------------------------------------
# Endpoints — scan
# ---------------------------------------------------------------------------

@app.post("/scan/token", response_model=ScanTokenResponse, tags=["scan"])
async def create_scan_token(request: Request, response: Response) -> ScanTokenResponse:
    """
    Issue a short-lived (60s), single-use scan token for the authenticated user.

    This is needed because EventSource (used for SSE streaming) cannot send
    HTTP cookies. The token is passed as a URL query param to /scan/stream.

    The token encodes the user_id server-side — the frontend never sees it.
    """
    session_id, session_data = get_authenticated_session(request)
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Call GET /auth/url first.",
        )

    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user in session.",
        )

    scan_token, _ = _issue_scan_token(user_id)
    return ScanTokenResponse(scan_token=scan_token)


@app.get("/scan/stream", tags=["scan"])
async def scan_stream(scan_token: str, scan_id: str):
    """
    Run a complete Gmail inbox scan and stream results via Server-Sent Events (SSE).

    Authentication is via the short-lived scan_token (issued by POST /scan/token),
    NOT a cookie, because EventSource cannot send cookies cross-origin.

    Parameters
    ----------
    scan_token : str
        Single-use token from POST /scan/token. Valid for 60 seconds.
    scan_id : str
        Client-generated scan UUID for cancellation via POST /scan/stop/{scan_id}.
    """
    # Validate and consume the scan token (single-use)
    token_data = _consume_scan_token(scan_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired scan token. Request a new one from POST /scan/token.",
        )

    user_id = token_data["user_id"]
    creds = load_credentials(user_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials not found. Please sign in again.",
        )

    try:
        creds = refresh_if_expired(user_id, creds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {exc}",
        )

    try:
        service = get_gmail_service(creds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build Gmail service: {exc}",
        )

    # Register the cancel event keyed by the client-provided scan_id
    cancel_event = threading.Event()
    active_scans[scan_id] = cancel_event

    def event_generator():
        try:
            for event_str in run_scan(service, cancel_event=cancel_event):
                yield event_str
        except Exception as e:
            logger.exception("Unexpected error during scan for user %s", user_id)
            import json as _json
            error_data = _json.dumps({"message": f"Fatal error: {e}"})
            yield f"event: error\ndata: {error_data}\n\n"
        finally:
            active_scans.pop(scan_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/scan/stop/{scan_id}", tags=["scan"])
async def stop_scan(scan_id: str):
    """Cancel an ongoing scan."""
    cancel_event = active_scans.get(scan_id)
    if cancel_event:
        cancel_event.set()
        logger.info("Cancellation requested for scan %s", scan_id)
        return {"status": "cancelling"}
    return {"status": "not_found"}


# ---------------------------------------------------------------------------
# Endpoints — ML predict (no auth required)
# ---------------------------------------------------------------------------

from predict import predict


@app.post("/predict", response_model=PredictResponse, tags=["scan"])
async def predict_endpoint(request: PredictRequest):
    """Classify input text as spam or ham."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    try:
        result = predict(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error during prediction")
        raise HTTPException(status_code=500, detail="Internal server error")

    return PredictResponse(**result)


# ---------------------------------------------------------------------------
# Endpoints — Gmail labels
# ---------------------------------------------------------------------------

from backend.labels.manager import delete_all_managed_labels, _list_all_labels


@app.get("/labels", tags=["labels"])
async def get_labels(request: Request, response: Response):
    """List all labels in the authenticated user's Gmail account."""
    session_id, session_data = get_authenticated_session(request)
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user_id, creds = _get_user_credentials(session_data)
    try:
        service = get_gmail_service(creds)
        labels_map = _list_all_labels(service)
        return {"labels": labels_map}
    except Exception:
        logger.exception("Failed to fetch labels for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to fetch labels.")


@app.post("/labels/delete", response_model=DeleteLabelsResponse, tags=["labels"])
async def delete_labels_endpoint(
    request: Request,
    response: Response,
    body: DeleteLabelsRequest | None = None,
):
    """Delete managed Gmail labels (or a specific label) for the current user."""
    session_id, session_data = get_authenticated_session(request)
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user_id, creds = _get_user_credentials(session_data)
    try:
        service = get_gmail_service(creds)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to build Gmail service: {exc}",
        )

    label_names = [body.label_name] if (body and body.label_name) else None

    try:
        result = delete_all_managed_labels(service, label_names=label_names)
        count = len(result["deleted"])
        msg = f"Successfully deleted {count} label(s)." if count > 0 else "No labels were deleted."
        return DeleteLabelsResponse(
            status="success",
            deleted=result["deleted"],
            failed=result["failed"],
            skipped_system=result["skipped_system"],
            message=msg,
        )
    except Exception:
        logger.exception("Failed to delete labels for user %s", user_id)
        raise HTTPException(status_code=500, detail="Label deletion failed.")

"""
mailshield_api.py — FastAPI layer for MailShield AI.

Exposes the existing Gmail OAuth + ML scan pipeline over HTTP so that
any frontend (Nuxt, React, mobile, CLI) can use it without touching the
Python internals directly.

Run from the project root:
    uvicorn backend.mailshield_api:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    GET  /health          — liveness probe
    GET  /auth/url        — returns Google OAuth authorization URL
    POST /auth/callback   — exchanges code → credentials, saves token.json
    GET  /auth/status     — checks whether credentials exist & are valid
    POST /auth/logout     — revokes + deletes credentials
    POST /scan            — runs full Gmail scan synchronously, returns JSON
"""

import logging
import sys
import os

# Allow HTTP for local OAuth development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ---------------------------------------------------------------------------
# Path setup so this module can be run from the project root with uvicorn
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.auth.oauth import (
    get_auth_url,
    exchange_code,
    load_credentials,
    refresh_if_expired,
    revoke_credentials,
    save_credentials,
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
    title="MailShield AI API",
    description="Gmail security assistant — OAuth + ML scan pipeline.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the Nuxt dev server (port 3000) and any other local origin.
# In production replace ["*"] with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class CallbackRequest(BaseModel):
    code: str


class HealthResponse(BaseModel):
    status: str
    version: str = "2.0.0"


class AuthUrlResponse(BaseModel):
    url: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    email: str | None = None


class ScanResponse(BaseModel):
    total: int
    results: list[dict]
    summary: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Liveness probe — always returns 200 if the server is running."""
    return HealthResponse(status="ok")


@app.get("/auth/url", response_model=AuthUrlResponse, tags=["auth"])
async def auth_url() -> AuthUrlResponse:
    """
    Generate and return the Google OAuth 2.0 authorization URL.

    The frontend should redirect the user to this URL.  After the user
    grants consent, Google will redirect back to REDIRECT_URI with
    ?code=...&state=...  — forward those params to POST /auth/callback.
    """
    try:
        url = get_auth_url()
        return AuthUrlResponse(url=url)
    except EnvironmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth misconfiguration: {exc}",
        )


@app.post("/auth/callback", response_model=AuthStatusResponse, tags=["auth"])
async def auth_callback(body: CallbackRequest) -> AuthStatusResponse:
    """
    Exchange the OAuth authorization code for credentials.

    The Nuxt frontend receives ?code=... from Google's redirect, then
    calls this endpoint with the code in the request body.
    """
    try:
        creds = exchange_code(body.code)
        save_credentials(creds)
        logger.info("OAuth callback successful — credentials saved.")
        return AuthStatusResponse(authenticated=True)
    except Exception as exc:
        logger.error("OAuth callback failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {exc}",
        )


@app.get("/auth/status", response_model=AuthStatusResponse, tags=["auth"])
async def auth_status() -> AuthStatusResponse:
    """
    Check whether valid credentials exist on disk.

    The frontend calls this on page load to decide whether to show the
    login page or the dashboard.
    """
    creds = load_credentials()
    if not creds:
        return AuthStatusResponse(authenticated=False)

    try:
        creds = refresh_if_expired(creds)
        return AuthStatusResponse(authenticated=True)
    except Exception as exc:
        logger.warning("Credential refresh failed: %s", exc)
        return AuthStatusResponse(authenticated=False)


@app.post("/auth/logout", response_model=AuthStatusResponse, tags=["auth"])
async def auth_logout() -> AuthStatusResponse:
    """Revoke the access token and delete local credentials."""
    creds = load_credentials()
    if creds:
        revoke_credentials(creds)
    return AuthStatusResponse(authenticated=False)


from fastapi.responses import StreamingResponse
import threading
import uuid

# Global map to store cancellation events for active scans
active_scans: dict[str, threading.Event] = {}

@app.get("/scan/stream", tags=["scan"])
async def scan_stream(scan_id: str):
    """
    Run a complete Gmail inbox scan and stream results via Server-Sent Events (SSE).
    """
    creds = load_credentials()
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Call GET /auth/url first.",
        )

    try:
        creds = refresh_if_expired(creds)
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

    # Register the cancel event
    cancel_event = threading.Event()
    active_scans[scan_id] = cancel_event

    def event_generator():
        try:
            for event_str in run_scan(service, cancel_event=cancel_event):
                yield event_str
        except Exception as e:
            logger.exception("Unexpected error during scan")
            import json
            error_data = json.dumps({"message": f"Fatal error: {e}"})
            yield f"event: error\ndata: {error_data}\n\n"
        finally:
            active_scans.pop(scan_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/scan/stop/{scan_id}", tags=["scan"])
async def stop_scan(scan_id: str):
    """
    Cancel an ongoing scan.
    """
    cancel_event = active_scans.get(scan_id)
    if cancel_event:
        cancel_event.set()
        logger.info("Cancellation requested for scan %s", scan_id)
        return {"status": "cancelling"}
    return {"status": "not_found"}

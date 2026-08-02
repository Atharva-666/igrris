"""
igrris_api.py — FastAPI layer for Igrris AI.

Exposes the existing Gmail OAuth + ML scan pipeline over HTTP so that
any frontend (Nuxt, React, mobile, CLI) can use it without touching the
Python internals directly.

Run from the project root:
    uvicorn backend.igrris_api:app --host 0.0.0.0 --port 8000 --reload

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

# Note: OAUTHLIB_INSECURE_TRANSPORT is handled conditionally in backend/config.py
# (only set when DEBUG=true, never in production)

# ---------------------------------------------------------------------------
# Path setup so this module can be run from the project root with uvicorn
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    title="Igrris AI API",
    description="Gmail security assistant — OAuth + ML scan pipeline.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup_event():
    from backend.threat_intelligence.startup import init_threat_intelligence
    init_threat_intelligence()


# CORS — reads from ALLOWED_ORIGINS env var in production (Railway).
# Set ALLOWED_ORIGINS=https://your-app.vercel.app on Railway.
# Falls back to localhost origins for local development.
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501"
)
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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
    picture: str | None = None
    name: str | None = None


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
    label_name: str | None = Field(default=None, description="Optional specific label name to delete. If omitted, deletes all managed labels.")


class DeleteLabelsResponse(BaseModel):
    status: str
    deleted: list[str]
    failed: list[str]
    skipped_system: list[str]
    message: str


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


import requests

def get_user_info(credentials) -> dict:
    try:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch user info: {e}")
    return {}

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
        user_info = get_user_info(creds)
        return AuthStatusResponse(
            authenticated=True,
            email=user_info.get("email"),
            picture=user_info.get("picture"),
            name=user_info.get("name")
        )
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
    except Exception as exc:
        logger.exception("Unexpected error during prediction")
        raise HTTPException(status_code=500, detail="Internal server error")

    return PredictResponse(**result)


from backend.labels.manager import delete_all_managed_labels, delete_managed_label, _list_all_labels


@app.get("/labels", tags=["labels"])
async def get_labels():
    """List all labels in the authenticated Gmail account."""
    creds = load_credentials()
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        creds = refresh_if_expired(creds)
        service = get_gmail_service(creds)
        labels_map = _list_all_labels(service)
        return {"labels": labels_map}
    except Exception as exc:
        logger.exception("Failed to fetch labels")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/labels/delete", response_model=DeleteLabelsResponse, tags=["labels"])
async def delete_labels_endpoint(request: DeleteLabelsRequest | None = None):
    """
    Delete managed Gmail labels (or a specific label).
    """
    creds = load_credentials()
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        creds = refresh_if_expired(creds)
        service = get_gmail_service(creds)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication error: {exc}")

    label_names = [request.label_name] if (request and request.label_name) else None

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
    except Exception as exc:
        logger.exception("Failed to delete labels")
        raise HTTPException(status_code=500, detail=f"Label deletion failed: {exc}")


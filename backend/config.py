"""
config.py — Central configuration for MailShield AI.

All secrets come from a .env file. Copy .env.example → .env and fill in values.
Never commit .env to version control.
"""

import os

from dotenv import load_dotenv

# Load .env from project root (works regardless of where the app is launched from)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"))

# ---------------------------------------------------------------------------
# Google OAuth credentials
# Obtain from: https://console.cloud.google.com/ → Credentials → OAuth 2.0
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Redirect URI must EXACTLY match what is registered in Google Cloud Console.
# For local Streamlit: http://localhost:8501
REDIRECT_URI: str = os.environ.get("REDIRECT_URI", "http://localhost:8501")

# ---------------------------------------------------------------------------
# Gmail OAuth scopes (minimum required)
#   gmail.modify  → read messages + apply/remove labels (NO send / NO delete)
#   gmail.labels  → create and manage custom labels
# ---------------------------------------------------------------------------
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

# ---------------------------------------------------------------------------
# File paths (relative to project root)
# ---------------------------------------------------------------------------
TOKEN_FILE: str = os.path.join(_ROOT, "token.json")
OAUTH_STATE_FILE: str = os.path.join(_ROOT, ".oauth_state")

# ---------------------------------------------------------------------------
# Gmail API settings
# ---------------------------------------------------------------------------
# Maximum messages per API page (Gmail API maximum is 500)
MAX_RESULTS_PER_PAGE: int = 500

# Seconds to sleep between messages.modify calls to respect Gmail rate limits.
# Gmail free tier allows ~10,000 quota units/day. messages.get = 5 units each.
API_CALL_DELAY: float = 0.05

# ---------------------------------------------------------------------------
# AI label definitions
# Gmail supports a fixed palette; these hex values are within that palette.
# ---------------------------------------------------------------------------
AI_LABELS: dict[str, dict] = {
    "AI Safe": {
        "textColor": "#FFFFFF",
        "backgroundColor": "#16a765",  # green
    },
    "AI Spam": {
        "textColor": "#FFFFFF",
        "backgroundColor": "#cc3a21",  # red
    },
    "AI Needs Review": {
        "textColor": "#000000",
        "backgroundColor": "#f2c960",  # amber
    },
}

# ---------------------------------------------------------------------------
# SECURITY NOTE (local development only)
# Allow OAuth flow over plain HTTP. In production, use HTTPS and remove this.
# ---------------------------------------------------------------------------
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

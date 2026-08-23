"""
config.py — Central configuration for Igrris AI.

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
# For production (Railway backend):  https://<railway-domain>/auth/callback
# For local dev:                     http://localhost:8000/auth/callback
REDIRECT_URI: str = os.environ.get("REDIRECT_URI", "http://localhost:8000/auth/callback")

# ---------------------------------------------------------------------------
# Gmail OAuth scopes (minimum required)
#   gmail.modify  → read messages + apply/remove labels (NO send / NO delete)
#   gmail.labels  → create and manage custom labels
# ---------------------------------------------------------------------------
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# ---------------------------------------------------------------------------
# Per-user credential storage directory
#
# CREDENTIALS_DIR is configurable via environment variable so Railway volumes
# can be mounted at any path.
#
# Railway production:  Set CREDENTIALS_DIR=/app/credentials
#                      (mount a Railway persistent Volume there for persistence)
# Local dev:           Defaults to <project_root>/credentials/
#
# NEVER use a single global token.json — each user gets their own file.
# ---------------------------------------------------------------------------
CREDENTIALS_DIR: str = os.environ.get(
    "CREDENTIALS_DIR",
    os.path.join(_ROOT, "credentials"),
)

# ---------------------------------------------------------------------------
# Session secret (for future HMAC signing of session tokens if needed)
# ---------------------------------------------------------------------------
SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "")

# ---------------------------------------------------------------------------
# Log paths (relative to project root)
# ---------------------------------------------------------------------------
LOG_DIR: str = os.path.join(_ROOT, "logs")
LOG_FILE: str = os.path.join(LOG_DIR, "igrris.log")

# Path to the rule engine YAML config
RULES_CONFIG_FILE: str = os.path.join(_ROOT, "backend", "classifier", "rules_config.yaml")

# ML confidence threshold — below this → 'Needs Review'
CONFIDENCE_THRESHOLD: float = 0.70

# ---------------------------------------------------------------------------
# Gmail API settings
# ---------------------------------------------------------------------------
# Maximum messages per API page (Gmail API maximum is 500)
MAX_RESULTS_PER_PAGE: int = 500

# Maximum number of pages to fetch per scan to avoid hitting rate limits (e.g. 2 pages = 1000 emails)
MAX_PAGES_TO_FETCH: int = 2

# Seconds to sleep between messages.modify calls to respect Gmail rate limits.
# Gmail free tier allows ~10,000 quota units/day. messages.get = 5 units each.
API_CALL_DELAY: float = 0.05

# ---------------------------------------------------------------------------
# Label definitions (11 labels — clean, no product branding)
# Gmail supports a fixed palette; these hex values are within that palette.
# ---------------------------------------------------------------------------
LABELS: dict[str, dict] = {
    "Trusted":      {"textColor": "#ffffff", "backgroundColor": "#16a766"},  # green
    "Spam":         {"textColor": "#ffffff", "backgroundColor": "#cc3a21"},  # red
    "Needs Review": {"textColor": "#434343", "backgroundColor": "#f2c960"},  # amber
    "Phishing":     {"textColor": "#ffffff", "backgroundColor": "#ac2b16"},  # dark red
    "Security":     {"textColor": "#ffffff", "backgroundColor": "#4a86e8"},  # blue
    "Banking":      {"textColor": "#ffffff", "backgroundColor": "#0b804b"},  # dark green
    "Orders":       {"textColor": "#ffffff", "backgroundColor": "#8e63ce"},  # purple
    "Promotions":   {"textColor": "#ffffff", "backgroundColor": "#eaa041"},  # orange
    "Education":    {"textColor": "#ffffff", "backgroundColor": "#43d6b0"},  # cyan
    "Work":         {"textColor": "#ffffff", "backgroundColor": "#285bac"},  # navy
    "Personal":     {"textColor": "#ffffff", "backgroundColor": "#666666"},  # gray
}

# Keep AI_LABELS as alias for backward compatibility with tests
AI_LABELS = LABELS

# ---------------------------------------------------------------------------
# SECURITY NOTE
# OAUTHLIB_INSECURE_TRANSPORT allows OAuth over plain HTTP.
# Only enabled when DEBUG=true (local development). Never set in production.
# Railway serves over HTTPS so this flag must be absent there.
# ---------------------------------------------------------------------------
if os.environ.get("DEBUG", "false").lower() == "true":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

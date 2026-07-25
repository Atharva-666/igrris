"""
streamlit_app.py — MailShield AI Gmail Security Assistant
Frontend dashboard built with Streamlit.

Run from the project root:
    streamlit run frontend/streamlit_app.py

OAuth flow (how it works in Streamlit):
  1. User clicks "Sign in with Google" → app generates auth URL and redirects
  2. Google authenticates the user and redirects back to:
       http://localhost:8501?code=<auth_code>&state=<state>
  3. Streamlit detects 'code' in st.query_params on the next page load
  4. App exchanges the code for credentials, saves to token.json
  5. App clears the query params and reruns → user is now logged in

App states:
  NOT_AUTHENTICATED  → show sign-in button
  AUTHENTICATED      → show scan button + results
  SCANNING           → show live progress bar
"""

import logging
import os
import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — ensure project root is importable
# frontend/streamlit_app.py → root = one level up
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ---------------------------------------------------------------------------
# Page config — MUST be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MailShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports (after path setup)
# ---------------------------------------------------------------------------
from backend.auth.oauth import (
    exchange_code,
    get_auth_url,
    load_credentials,
    refresh_if_expired,
    revoke_credentials,
    save_credentials,
)
from backend.gmail.connector import get_gmail_service
from backend.services.scan_service import run_scan

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom CSS — dark, premium feel
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* App background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Main content area */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Hero header */
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
    margin-bottom: 2rem;
}

/* Stat cards */
.stat-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.4rem 1rem;
    text-align: center;
    backdrop-filter: blur(10px);
}

.stat-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
}

.stat-label {
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

/* Sign-in card */
.signin-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    text-align: center;
    max-width: 480px;
    margin: 4rem auto;
    backdrop-filter: blur(20px);
}

.signin-card h2 {
    color: #f1f5f9;
    font-size: 1.6rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.signin-card p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* Label badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

.badge-safe     { background: #16a765; color: #fff; }
.badge-spam     { background: #cc3a21; color: #fff; }
.badge-review   { background: #f2c960; color: #000; }
.badge-error    { background: #6b7280; color: #fff; }

/* Results table */
.results-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 6px;
}

.results-table th {
    color: #64748b;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.5rem 1rem;
    text-align: left;
}

.results-table td {
    background: rgba(255,255,255,0.04);
    padding: 0.75rem 1rem;
    color: #e2e8f0;
    font-size: 0.88rem;
    vertical-align: middle;
}

.results-table tr td:first-child { border-radius: 10px 0 0 10px; }
.results-table tr td:last-child  { border-radius: 0 10px 10px 0; }

.truncate {
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
    vertical-align: middle;
}

/* User pill */
.user-pill {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 999px;
    padding: 0.35rem 1rem;
    color: #cbd5e1;
    font-size: 0.85rem;
    display: inline-block;
}

/* Progress text */
.progress-label {
    color: #94a3b8;
    font-size: 0.88rem;
    margin-top: 0.4rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "credentials": None,
        "user_email": None,
        "scan_results": [],
        "total_emails": 0,
        "scanning": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# ---------------------------------------------------------------------------
# Helper: get Gmail service from session credentials
# ---------------------------------------------------------------------------
def _get_service():
    creds = st.session_state.credentials
    creds = refresh_if_expired(creds)
    save_credentials(creds)
    st.session_state.credentials = creds
    return get_gmail_service(creds)


# ---------------------------------------------------------------------------
# Helper: fetch user email from Gmail profile
# ---------------------------------------------------------------------------
def _fetch_user_email(service) -> str:
    try:
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "Gmail User")
    except Exception:
        return "Gmail User"


# ---------------------------------------------------------------------------
# Step 1: Handle OAuth callback (code in URL query params)
# ---------------------------------------------------------------------------
params = st.query_params

if "code" in params and st.session_state.credentials is None:
    code = params["code"]
    with st.spinner("Completing Google sign-in…"):
        try:
            credentials = exchange_code(code)
            save_credentials(credentials)
            st.session_state.credentials = credentials
            # Clear the code from the URL so a page refresh doesn't re-trigger
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Sign-in failed: {e}")
            logger.exception("OAuth code exchange failed")
            st.query_params.clear()

# ---------------------------------------------------------------------------
# Step 2: Load saved credentials from disk (survives app restarts)
# ---------------------------------------------------------------------------
if st.session_state.credentials is None:
    saved = load_credentials()
    if saved:
        try:
            saved = refresh_if_expired(saved)
            st.session_state.credentials = saved
        except Exception:
            # Stored token is invalid → user must re-login
            pass

# ---------------------------------------------------------------------------
# Lazy-load user email once after authentication
# ---------------------------------------------------------------------------
if st.session_state.credentials is not None and st.session_state.user_email is None:
    try:
        svc = _get_service()
        st.session_state.user_email = _fetch_user_email(svc)
    except Exception:
        st.session_state.user_email = "Gmail User"


# ===========================================================================
# UI RENDERING
# ===========================================================================

# ---------------------------------------------------------------------------
# Header (always visible)
# ---------------------------------------------------------------------------
col_logo, col_spacer, col_user = st.columns([3, 4, 2])

with col_logo:
    st.markdown("""
    <p class="hero-title">🛡️ MailShield AI</p>
    <p class="hero-subtitle">Gmail Smart Security — powered by TF-IDF + LinearSVC</p>
    """, unsafe_allow_html=True)

with col_user:
    if st.session_state.credentials:
        st.markdown(f"""
        <div style="text-align:right; margin-top: 1.2rem;">
            <span class="user-pill">✉️ {st.session_state.user_email}</span>
        </div>
        """, unsafe_allow_html=True)
        st.write("")  # spacing
        if st.button("Sign Out", key="btn_signout", use_container_width=True):
            try:
                revoke_credentials(st.session_state.credentials)
            except Exception:
                pass
            st.session_state.credentials = None
            st.session_state.user_email = None
            st.session_state.scan_results = []
            st.session_state.total_emails = 0
            st.rerun()

st.markdown("---")

# ===========================================================================
# NOT AUTHENTICATED — show sign-in card
# ===========================================================================
if st.session_state.credentials is None:
    st.markdown("""
    <div class="signin-card">
        <h2>🔐 Connect Your Gmail</h2>
        <p>
            Sign in with your Google account to let MailShield AI scan
            your inbox and automatically apply smart labels.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Center the button
    _, center, _ = st.columns([2, 1.5, 2])
    with center:
        try:
            auth_url = get_auth_url()
            st.link_button(
                "🔵  Sign in with Google",
                url=auth_url,
                use_container_width=True,
            )
        except EnvironmentError as e:
            st.error(str(e))
            st.info(
                "Create a `.env` file in the project root with your "
                "`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. "
                "See `.env.example` for a template."
            )

    st.stop()  # Don't render anything else until authenticated


# ===========================================================================
# AUTHENTICATED — main dashboard
# ===========================================================================

# ---------------------------------------------------------------------------
# Stats row (shown when we have results)
# ---------------------------------------------------------------------------
if st.session_state.scan_results:
    results = st.session_state.scan_results
    total    = len(results)
    safe     = sum(1 for r in results if r["gmail_label"] == "AI Safe")
    spam     = sum(1 for r in results if r["gmail_label"] == "AI Spam")
    review   = sum(1 for r in results if r["gmail_label"] == "AI Needs Review")
    errors   = sum(1 for r in results if r["status"] == "error")

    s1, s2, s3, s4, s5 = st.columns(5)
    for col, num, label, color in [
        (s1, total,  "Total Scanned", "#60a5fa"),
        (s2, safe,   "✅ Safe",        "#34d399"),
        (s3, spam,   "🚨 Spam",        "#f87171"),
        (s4, review, "🔍 Needs Review","#fbbf24"),
        (s5, errors, "⚠ Errors",       "#94a3b8"),
    ]:
        col.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color:{color}">{num}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

# ---------------------------------------------------------------------------
# Scan button
# ---------------------------------------------------------------------------
col_btn, col_desc = st.columns([1, 3])

with col_btn:
    scan_clicked = st.button(
        "🔍  Scan Inbox",
        key="btn_scan",
        use_container_width=True,
        disabled=st.session_state.scanning,
        type="primary",
    )

with col_desc:
    if st.session_state.scan_results:
        st.markdown(
            "<p style='color:#64748b; font-size:0.88rem; margin-top:0.6rem;'>"
            "Click <b>Scan Inbox</b> to process any new unlabeled emails."
            "</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.88rem; margin-top:0.6rem;'>"
            "First scan will process <b>all emails</b> in your Gmail account. "
            "Subsequent scans skip already-labeled emails — much faster."
            "</p>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Scan execution
# ---------------------------------------------------------------------------
if scan_clicked:
    st.session_state.scanning = True
    st.session_state.scan_results = []

    progress_bar = st.progress(0, text="Connecting to Gmail…")
    status_placeholder = st.empty()
    results_so_far: list[dict] = []

    try:
        service = _get_service()

        def on_start(total: int) -> None:
            st.session_state.total_emails = total
            if total == 0:
                status_placeholder.markdown(
                    "<p class='progress-label'>✅ All emails already labeled — nothing to do!</p>",
                    unsafe_allow_html=True,
                )
            else:
                status_placeholder.markdown(
                    f"<p class='progress-label'>Found <b>{total}</b> unlabeled emails. Starting…</p>",
                    unsafe_allow_html=True,
                )

        def on_progress(current: int, total: int) -> None:
            pct = current / max(total, 1)
            progress_bar.progress(
                pct,
                text=f"Scanning {current} of {total} emails…",
            )

        for result in run_scan(service, on_start=on_start, on_progress=on_progress):
            results_so_far.append(result)

        st.session_state.scan_results = results_so_far
        progress_bar.progress(1.0, text="✅ Scan complete!")
        status_placeholder.empty()

    except Exception as e:
        st.error(f"Scan failed: {e}")
        logger.exception("Scan failed")

    finally:
        st.session_state.scanning = False

    st.rerun()

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------
if st.session_state.scan_results:
    st.markdown(f"### 📋 Scan Results  ({len(st.session_state.scan_results)} emails)")

    # Build HTML table rows
    def _badge(gmail_label: str, status: str) -> str:
        if status == "error":
            return '<span class="badge badge-error">Error</span>'
        classes = {
            "AI Safe":         "badge-safe",
            "AI Spam":         "badge-spam",
            "AI Needs Review": "badge-review",
        }
        css = classes.get(gmail_label, "badge-error")
        return f'<span class="badge {css}">{gmail_label}</span>'

    def _conf(confidence: float) -> str:
        pct = int(confidence * 100)
        color = "#34d399" if pct >= 80 else "#fbbf24" if pct >= 60 else "#f87171"
        return f'<span style="color:{color};font-weight:600">{pct}%</span>'

    rows_html = ""
    for r in st.session_state.scan_results:
        sender  = r.get("sender", "")[:50]
        subject = r.get("subject", "")[:60]
        label   = r.get("gmail_label", "")
        status  = r.get("status", "")
        conf    = r.get("confidence", 0.0)

        rows_html += f"""
        <tr>
          <td><span class="truncate" title="{sender}">{sender}</span></td>
          <td><span class="truncate" title="{subject}">{subject}</span></td>
          <td>{_badge(label, status)}</td>
          <td>{_conf(conf)}</td>
        </tr>
        """

    table_html = f"""
    <table class="results-table">
      <thead>
        <tr>
          <th>Sender</th>
          <th>Subject</th>
          <th>AI Label</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)

elif not st.session_state.scanning:
    # No results yet — welcome message
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 1rem;
        color: #475569;
    ">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">📥</div>
        <p style="font-size: 1.1rem; color: #64748b;">
            Click <b style="color:#a78bfa">Scan Inbox</b> to start labeling your emails with AI.
        </p>
        <p style="font-size: 0.85rem; color: #475569; margin-top: 0.5rem;">
            Labels appear directly inside Gmail: <b>AI Safe</b>, <b>AI Spam</b>, <b>AI Needs Review</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

"""
streamlit_app.py — MailShield AI Gmail Security Assistant
Anime-cyberpunk themed frontend built with Streamlit.

Run from the project root:
    venv\\Scripts\\python.exe -m streamlit run frontend/streamlit_app.py

OAuth flow:
  1. User clicks "Sign in with Google" → app generates auth URL and redirects
  2. Google authenticates and redirects back with code + state in query params
  3. Streamlit detects 'code' in st.query_params on next page load
  4. App exchanges the code for credentials, saves to token.json
  5. App clears query params and reruns → user is now logged in

App states:
  NOT_AUTHENTICATED  → show sign-in card
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
# ANIME-CYBERPUNK CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&family=Share+Tech+Mono&display=swap');

/* ─── Reset & Base ───────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ─── Animated Background ────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(100,0,180,0.25) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(0,200,255,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 40% 50% at 10% 60%, rgba(255,0,128,0.1) 0%, transparent 60%),
        linear-gradient(180deg, #04010f 0%, #070315 40%, #050212 100%);
    min-height: 100vh;
    overflow-x: hidden;
}

/* Scanline overlay */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,0,0,0) 0px,
        rgba(0,0,0,0) 2px,
        rgba(0,0,0,0.08) 2px,
        rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* Grid overlay */
.stApp::after {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(120,0,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(120,0,255,0.04) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

/* ─── Main container ─────────────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
    position: relative;
    z-index: 1;
}

/* ─── Floating particles ─────────────────────────────────────── */
@keyframes float-up {
    0%   { transform: translateY(100vh) scale(0); opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 0.6; }
    100% { transform: translateY(-20px) scale(1); opacity: 0; }
}

.particle {
    position: fixed;
    border-radius: 50%;
    animation: float-up linear infinite;
    pointer-events: none;
    z-index: 2;
}

/* ─── Glitch animation ───────────────────────────────────────── */
@keyframes glitch {
    0%   { clip-path: inset(40% 0 61% 0); transform: translate(-4px, 0); }
    20%  { clip-path: inset(92% 0 1%  0); transform: translate(4px, 0);  }
    40%  { clip-path: inset(43% 0 1%  0); transform: translate(-4px, 0); }
    60%  { clip-path: inset(25% 0 58% 0); transform: translate(4px, 0);  }
    80%  { clip-path: inset(54% 0 7%  0); transform: translate(-4px, 0); }
    100% { clip-path: inset(58% 0 43% 0); transform: translate(4px, 0);  }
}

@keyframes glow-pulse {
    0%, 100% { text-shadow: 0 0 10px #a855f7, 0 0 30px #a855f7, 0 0 60px #a855f7; }
    50%       { text-shadow: 0 0 20px #06b6d4, 0 0 50px #06b6d4, 0 0 100px #06b6d4; }
}

@keyframes border-glow {
    0%, 100% { border-color: rgba(168,85,247,0.6); box-shadow: 0 0 15px rgba(168,85,247,0.3), inset 0 0 15px rgba(168,85,247,0.05); }
    50%       { border-color: rgba(6,182,212,0.6);  box-shadow: 0 0 25px rgba(6,182,212,0.4),  inset 0 0 25px rgba(6,182,212,0.08);  }
}

@keyframes slide-in-left {
    from { transform: translateX(-60px); opacity: 0; }
    to   { transform: translateX(0);     opacity: 1; }
}

@keyframes fade-in-up {
    from { transform: translateY(30px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
}

@keyframes scan-line {
    0%   { top: -10%; }
    100% { top: 110%;  }
}

@keyframes spin-slow {
    from { transform: rotate(0deg);   }
    to   { transform: rotate(360deg); }
}

@keyframes flicker {
    0%, 100% { opacity: 1; }
    92%       { opacity: 1; }
    93%       { opacity: 0.4; }
    94%       { opacity: 1; }
    96%       { opacity: 0.2; }
    97%       { opacity: 1; }
}

@keyframes gradient-shift {
    0%, 100% { background-position: 0% 50%;   }
    50%       { background-position: 100% 50%; }
}

/* ─── Hero section ───────────────────────────────────────────── */
.hero-wrapper {
    position: relative;
    animation: slide-in-left 0.8s cubic-bezier(0.16,1,0.3,1) forwards;
}

.hero-eyebrow {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.25em;
    color: #06b6d4;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    opacity: 0.85;
}

.hero-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #e879f9, #a855f7, #06b6d4, #34d399);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradient-shift 6s ease infinite;
    line-height: 1.1;
    margin-bottom: 0.15rem;
    position: relative;
}

.hero-katakana {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: rgba(168,85,247,0.5);
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
}

.hero-subtitle {
    font-size: 1rem;
    color: #94a3b8;
    letter-spacing: 0.03em;
    margin-top: 0.3rem;
}

.hero-subtitle b { color: #06b6d4; font-weight: 600; }

/* ─── Neon divider ───────────────────────────────────────────── */
.neon-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        rgba(168,85,247,0.6) 20%,
        rgba(6,182,212,0.8) 50%,
        rgba(168,85,247,0.6) 80%,
        transparent 100%
    );
    margin: 1.2rem 0;
    position: relative;
}

.neon-divider::after {
    content: '◆';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    color: #06b6d4;
    font-size: 0.6rem;
    background: #04010f;
    padding: 0 6px;
}

/* ─── User pill ──────────────────────────────────────────────── */
.user-pill {
    background: linear-gradient(135deg, rgba(168,85,247,0.15), rgba(6,182,212,0.1));
    border: 1px solid rgba(168,85,247,0.4);
    border-radius: 6px;
    padding: 0.5rem 1.1rem;
    color: #e2e8f0;
    font-size: 0.82rem;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 0.05em;
    display: inline-block;
    box-shadow: 0 0 12px rgba(168,85,247,0.2), inset 0 0 8px rgba(168,85,247,0.05);
    animation: border-glow 3s ease-in-out infinite, flicker 8s infinite;
}

.user-pill .icon { color: #06b6d4; margin-right: 4px; }

/* ─── Stat cards ─────────────────────────────────────────────── */
.stat-card {
    background: linear-gradient(135deg, rgba(10,5,30,0.9) 0%, rgba(20,10,50,0.7) 100%);
    border: 1px solid rgba(168,85,247,0.35);
    border-radius: 8px;
    padding: 1.2rem 0.8rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: fade-in-up 0.6s ease forwards, border-glow 4s ease-in-out infinite;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 0 30px rgba(168,85,247,0.4), 0 0 60px rgba(6,182,212,0.2);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: -100%; left: -50%;
    width: 200%; height: 200%;
    background: linear-gradient(transparent 0%, rgba(168,85,247,0.06) 50%, transparent 100%);
    animation: scan-line 3s linear infinite;
}

.stat-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-color, #a855f7), transparent);
}

.stat-number {
    font-family: 'Orbitron', monospace;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 0 8px currentColor);
}

.stat-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ─── Sign-in card ───────────────────────────────────────────── */
.signin-card {
    background: linear-gradient(135deg, rgba(10,5,30,0.95) 0%, rgba(25,10,60,0.9) 100%);
    border: 1px solid rgba(168,85,247,0.5);
    border-radius: 12px;
    padding: 3.5rem 3rem;
    text-align: center;
    max-width: 520px;
    margin: 3rem auto;
    position: relative;
    overflow: hidden;
    animation: border-glow 3s ease-in-out infinite;
    box-shadow: 0 0 40px rgba(168,85,247,0.2), 0 0 80px rgba(6,182,212,0.08), inset 0 0 40px rgba(168,85,247,0.05);
}

.signin-card::before {
    content: '';
    position: absolute;
    top: -100%; left: -50%;
    width: 200%; height: 200%;
    background: linear-gradient(transparent 0%, rgba(168,85,247,0.04) 50%, transparent 100%);
    animation: scan-line 2s linear infinite;
}

.signin-card::after {
    content: '';
    position: absolute;
    inset: 8px;
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 8px;
    pointer-events: none;
}

.signin-shield {
    font-size: 4.5rem;
    margin-bottom: 1rem;
    animation: spin-slow 20s linear infinite;
    display: inline-block;
    filter: drop-shadow(0 0 20px rgba(168,85,247,0.8));
}

.signin-card h2 {
    font-family: 'Orbitron', monospace;
    color: #f1f5f9;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    letter-spacing: 0.05em;
}

.signin-card .katakana-sub {
    font-family: 'Share Tech Mono', monospace;
    color: rgba(6,182,212,0.7);
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    margin-bottom: 1rem;
}

.signin-card p {
    color: #94a3b8;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 2rem;
}

/* ─── Streamlit button overrides ─────────────────────────────── */
.stButton > button {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    border: 1px solid rgba(168,85,247,0.7) !important;
    background: linear-gradient(135deg, rgba(168,85,247,0.25) 0%, rgba(6,182,212,0.15) 100%) !important;
    color: #e2e8f0 !important;
    box-shadow: 0 0 15px rgba(168,85,247,0.3), inset 0 0 10px rgba(168,85,247,0.05) !important;
    transition: all 0.25s ease !important;
    padding: 0.6rem 1.4rem !important;
}

.stButton > button:hover {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 25px rgba(6,182,212,0.5), inset 0 0 15px rgba(6,182,212,0.1) !important;
    background: linear-gradient(135deg, rgba(6,182,212,0.3) 0%, rgba(168,85,247,0.2) 100%) !important;
    transform: translateY(-2px) !important;
}

.stButton > button[kind="primary"] {
    border-color: #a855f7 !important;
    background: linear-gradient(135deg, rgba(168,85,247,0.45) 0%, rgba(6,182,212,0.25) 100%) !important;
    box-shadow: 0 0 25px rgba(168,85,247,0.5), inset 0 0 20px rgba(168,85,247,0.1) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 40px rgba(168,85,247,0.7), 0 0 80px rgba(6,182,212,0.3) !important;
}

.stLinkButton > a {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    border: 1px solid #a855f7 !important;
    background: linear-gradient(135deg, rgba(168,85,247,0.4) 0%, rgba(6,182,212,0.25) 100%) !important;
    color: #f1f5f9 !important;
    box-shadow: 0 0 25px rgba(168,85,247,0.5), inset 0 0 15px rgba(168,85,247,0.08) !important;
    text-decoration: none !important;
    transition: all 0.25s !important;
}

.stLinkButton > a:hover {
    box-shadow: 0 0 45px rgba(168,85,247,0.8), 0 0 90px rgba(6,182,212,0.4) !important;
    transform: translateY(-3px) !important;
}

/* ─── Progress bar ───────────────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, #a855f7, #06b6d4, #34d399) !important;
    box-shadow: 0 0 10px #a855f7 !important;
    border-radius: 999px !important;
}

.stProgress > div {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 999px !important;
    border: 1px solid rgba(168,85,247,0.2) !important;
}

/* ─── Badge labels ───────────────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.badge-safe   { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.5);  box-shadow: 0 0 8px rgba(52,211,153,0.2); }
.badge-spam   { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.5); box-shadow: 0 0 8px rgba(248,113,113,0.2); }
.badge-review { background: rgba(251,191,36,0.15);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.5);  box-shadow: 0 0 8px rgba(251,191,36,0.2); }
.badge-error  { background: rgba(148,163,184,0.1);  color: #94a3b8; border: 1px solid rgba(148,163,184,0.3); }

/* ─── Results section header ─────────────────────────────────── */
.results-header {
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-bottom: 0.8rem;
}

.results-header::before { content: '▶'; color: #a855f7; font-size: 0.6rem; }

.results-count-badge {
    background: rgba(168,85,247,0.2);
    border: 1px solid rgba(168,85,247,0.4);
    color: #a855f7;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 4px;
}

/* ─── Results table ──────────────────────────────────────────── */
.results-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 4px;
    animation: fade-in-up 0.5s ease forwards;
}

.results-table th {
    font-family: 'Share Tech Mono', monospace;
    color: rgba(168,85,247,0.7);
    font-size: 0.66rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    padding: 0.4rem 1rem;
    text-align: left;
    border-bottom: 1px solid rgba(168,85,247,0.2);
}

.results-table tbody tr:hover td {
    background: rgba(168,85,247,0.08);
    border-color: rgba(168,85,247,0.3);
}

.results-table td {
    background: rgba(10,5,30,0.7);
    border: 1px solid rgba(255,255,255,0.04);
    border-right: none;
    border-left: none;
    padding: 0.7rem 1rem;
    color: #cbd5e1;
    font-size: 0.86rem;
    vertical-align: middle;
    transition: all 0.2s;
}

.results-table tr td:first-child { border-left: 1px solid rgba(255,255,255,0.04); border-radius: 6px 0 0 6px; }
.results-table tr td:last-child  { border-right: 1px solid rgba(255,255,255,0.04); border-radius: 0 6px 6px 0; }
.results-table tbody tr:hover td:first-child { border-left-color: rgba(168,85,247,0.3); }
.results-table tbody tr:hover td:last-child  { border-right-color: rgba(168,85,247,0.3); }

.truncate {
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
    vertical-align: middle;
}

/* ─── Progress & scan labels ─────────────────────────────────── */
.progress-label {
    font-family: 'Share Tech Mono', monospace;
    color: #06b6d4;
    font-size: 0.82rem;
    margin-top: 0.4rem;
    letter-spacing: 0.05em;
}

.scan-info {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: #475569;
    line-height: 1.6;
    margin-top: 0.5rem;
    letter-spacing: 0.02em;
}

.scan-info b { color: #06b6d4; }

/* ─── Empty state ────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 1rem;
    animation: fade-in-up 0.8s ease forwards;
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1.2rem;
    filter: drop-shadow(0 0 25px rgba(168,85,247,0.6));
    animation: glow-pulse 3s ease-in-out infinite;
    display: inline-block;
}

.empty-state h3 {
    font-family: 'Orbitron', monospace;
    font-size: 1.2rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.08em;
    margin-bottom: 0.6rem;
}

.empty-state p { color: #64748b; font-size: 0.92rem; line-height: 1.6; }
.empty-state .highlight { color: #a855f7; font-weight: 600; }

.empty-state .tags {
    margin-top: 1rem;
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.tag-pill {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    padding: 4px 12px;
    border-radius: 4px;
    letter-spacing: 0.06em;
}

/* ─── Scrollbar ──────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: rgba(10,5,30,0.5); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #a855f7, #06b6d4);
    border-radius: 999px;
}

.particles-container {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 2;
    overflow: hidden;
}
</style>

<!-- Floating particles -->
<div class="particles-container">
  <div class="particle" style="left:8%;  background:#a855f7; animation-duration:12s; animation-delay:0s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:18%; background:#06b6d4; animation-duration:9s;  animation-delay:2s;   width:3px; height:3px;"></div>
  <div class="particle" style="left:30%; background:#e879f9; animation-duration:15s; animation-delay:4s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:45%; background:#a855f7; animation-duration:11s; animation-delay:1s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:58%; background:#06b6d4; animation-duration:14s; animation-delay:6s;   width:3px; height:3px;"></div>
  <div class="particle" style="left:70%; background:#34d399; animation-duration:10s; animation-delay:3s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:82%; background:#a855f7; animation-duration:13s; animation-delay:5s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:92%; background:#e879f9; animation-duration:8s;  animation-delay:7s;   width:3px; height:3px;"></div>
  <div class="particle" style="left:24%; background:#06b6d4; animation-duration:16s; animation-delay:9s;   width:2px; height:2px;"></div>
  <div class="particle" style="left:65%; background:#a855f7; animation-duration:12s; animation-delay:11s;  width:2px; height:2px;"></div>
</div>
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
col_logo, col_spacer, col_user = st.columns([4, 3, 2])

with col_logo:
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-eyebrow">// SYSTEM ONLINE · メールシールド AI · v2.0</div>
        <div class="hero-title">🛡 MAILSHIELD AI</div>
        <div class="hero-katakana">メール・セキュリティ・システム・起動完了</div>
        <div class="hero-subtitle">Gmail threat detection powered by <b>TF-IDF + LinearSVC</b></div>
    </div>
    """, unsafe_allow_html=True)

with col_user:
    if st.session_state.credentials:
        st.markdown(f"""
        <div style="text-align:right; margin-top: 1.4rem;">
            <div class="user-pill"><span class="icon">◈</span> {st.session_state.user_email}</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("⏻  DISCONNECT", key="btn_signout", use_container_width=True):
            try:
                revoke_credentials(st.session_state.credentials)
            except Exception:
                pass
            st.session_state.credentials = None
            st.session_state.user_email = None
            st.session_state.scan_results = []
            st.session_state.total_emails = 0
            st.rerun()

st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

# ===========================================================================
# NOT AUTHENTICATED — show sign-in card
# ===========================================================================
if st.session_state.credentials is None:
    st.markdown("""
    <div class="signin-card">
        <div class="signin-shield">🛡️</div>
        <h2>CONNECT GMAIL</h2>
        <div class="katakana-sub">グーグル・認証・システム</div>
        <p>
            Link your Google account to deploy MailShield AI on your inbox.
            The system will scan, classify, and label all threats automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([2, 1.5, 2])
    with center:
        try:
            auth_url = get_auth_url()
            st.link_button(
                "◈  SIGN IN WITH GOOGLE",
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

    st.stop()


# ===========================================================================
# AUTHENTICATED — main dashboard
# ===========================================================================

# ---------------------------------------------------------------------------
# Stats row (shown when we have results)
# ---------------------------------------------------------------------------
if st.session_state.scan_results:
    results = st.session_state.scan_results
    total   = len(results)
    safe    = sum(1 for r in results if r["gmail_label"] == "AI Safe")
    spam    = sum(1 for r in results if r["gmail_label"] == "AI Spam")
    review  = sum(1 for r in results if r["gmail_label"] == "AI Needs Review")
    errors  = sum(1 for r in results if r["status"] == "error")

    s1, s2, s3, s4, s5 = st.columns(5)
    stat_data = [
        (s1, total,  "TOTAL SCANNED", "#60a5fa", "#60a5fa"),
        (s2, safe,   "◈ SAFE",        "#34d399", "#34d399"),
        (s3, spam,   "◆ SPAM",        "#f87171", "#f87171"),
        (s4, review, "◇ REVIEW",      "#fbbf24", "#fbbf24"),
        (s5, errors, "⚠ ERRORS",       "#94a3b8", "#94a3b8"),
    ]
    for col, num, label, color, accent in stat_data:
        col.markdown(f"""
        <div class="stat-card" style="--accent-color: {accent};">
            <div class="stat-number" style="color:{color}">{num}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

# ---------------------------------------------------------------------------
# Scan button row
# ---------------------------------------------------------------------------
col_btn, col_desc = st.columns([1, 3])

with col_btn:
    scan_clicked = st.button(
        "◈  SCAN INBOX",
        key="btn_scan",
        use_container_width=True,
        disabled=st.session_state.scanning,
        type="primary",
    )

with col_desc:
    if st.session_state.scan_results:
        st.markdown(
            "<p class='scan-info'>Click <b>SCAN INBOX</b> to process any new unlabeled threats.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p class='scan-info'>"
            "First scan will process <b>ALL EMAILS</b> in your Gmail account.<br>"
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

    progress_bar = st.progress(0, text="INITIALIZING SCAN SEQUENCE…")
    status_placeholder = st.empty()
    results_so_far: list[dict] = []

    try:
        service = _get_service()

        def on_start(total: int) -> None:
            st.session_state.total_emails = total
            if total == 0:
                status_placeholder.markdown(
                    "<p class='progress-label'>◈ ALL THREATS ALREADY LABELED — SYSTEM CLEAR</p>",
                    unsafe_allow_html=True,
                )
            else:
                status_placeholder.markdown(
                    f"<p class='progress-label'>◆ TARGET ACQUIRED: <b style='color:#f1f5f9'>{total}</b> UNLABELED EMAILS · ENGAGING…</p>",
                    unsafe_allow_html=True,
                )

        def on_progress(current: int, total: int) -> None:
            pct = current / max(total, 1)
            progress_bar.progress(
                pct,
                text=f"SCANNING [{current}/{total}] · {int(pct*100)}% COMPLETE",
            )

        for result in run_scan(service, on_start=on_start, on_progress=on_progress):
            results_so_far.append(result)

        st.session_state.scan_results = results_so_far
        progress_bar.progress(1.0, text="◈ SCAN COMPLETE · ALL THREATS CLASSIFIED")
        status_placeholder.empty()

    except Exception as e:
        st.error(f"SCAN FAILED: {e}")
        logger.exception("Scan failed")

    finally:
        st.session_state.scanning = False

    st.rerun()

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------
if st.session_state.scan_results:
    count = len(st.session_state.scan_results)
    st.markdown(f"""
    <div class="results-header">
        SCAN RESULTS
        <span class="results-count-badge">{count} ENTRIES</span>
    </div>
    """, unsafe_allow_html=True)

    def _badge(gmail_label: str, status: str) -> str:
        if status == "error":
            return '<span class="badge badge-error">⚠ ERROR</span>'
        classes = {
            "AI Safe":         ("badge-safe",   "◈ SAFE"),
            "AI Spam":         ("badge-spam",   "◆ SPAM"),
            "AI Needs Review": ("badge-review", "◇ REVIEW"),
        }
        css, text = classes.get(gmail_label, ("badge-error", "UNKNOWN"))
        return f'<span class="badge {css}">{text}</span>'

    def _conf(confidence: float) -> str:
        pct = int(confidence * 100)
        if pct >= 80:
            color, glow = "#34d399", "rgba(52,211,153,0.4)"
        elif pct >= 60:
            color, glow = "#fbbf24", "rgba(251,191,36,0.4)"
        else:
            color, glow = "#f87171", "rgba(248,113,113,0.4)"
        return (
            f'<span style="font-family:\'Orbitron\',monospace; color:{color}; '
            f'font-weight:700; font-size:0.82rem; '
            f'text-shadow: 0 0 8px {glow};">{pct}%</span>'
        )

    rows_html = ""
    for r in st.session_state.scan_results:
        sender  = r.get("sender",  "")[:50]
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
          <th>◈ SENDER</th>
          <th>◈ SUBJECT</th>
          <th>◈ AI VERDICT</th>
          <th>◈ CONFIDENCE</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

elif not st.session_state.scanning:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📡</div>
        <h3>AWAITING SCAN COMMAND</h3>
        <p>
            System is online and ready to deploy.<br>
            Click <span class="highlight">◈ SCAN INBOX</span> to initiate threat classification.
        </p>
        <div class="tags">
            <span class="tag-pill badge-safe">◈ AI SAFE</span>
            <span class="tag-pill badge-spam">◆ AI SPAM</span>
            <span class="tag-pill badge-review">◇ AI NEEDS REVIEW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

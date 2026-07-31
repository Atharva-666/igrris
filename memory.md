# MailShield AI — Project Memory

## Architecture

```
Landing Page (/)
      │ "Connect Gmail" button
      ▼
Google OAuth (accounts.google.com)
      │ redirects to REDIRECT_URI
      ▼
/login?code=... (frontend OAuth callback catcher)
      │ calls POST /auth/callback on backend
      ▼
/dashboard (scanning interface)
      │ calls GET /scan/stream (SSE)
      ▼
FastAPI Backend (port 8000)
      │
      ▼
MailShield ML Backend (TF-IDF + LinearSVC)
```

## URL Structure

| URL                        | Page            | Purpose                                                                                                   |
| -------------------------- | --------------- | --------------------------------------------------------------------------------------------------------- |
| `localhost:8501/`          | `index.vue`     | Unified Landing Page & Dashboard. Has "Secure Your Inbox", Pipeline flow, and the actual scanning dashboard. |
| `localhost:8501/login`     | `login.vue`     | **OAuth callback catcher** — catches `?code=` from Google, exchanges for token, redirects to `/` |

## Critical Rules

### OAuth Flow

- `REDIRECT_URI` in `backend/config.py` MUST be `http://localhost:8501/login`
- This MUST also exactly match what is registered in **Google Cloud Console** → Credentials → OAuth 2.0 Client → Authorized Redirect URIs
- If you change the port, update BOTH `config.py` AND Google Cloud Console

### Page Responsibilities

- **`index.vue`** — Unified Application. Handles landing page content (Hero, Pipeline Section, Features). If authenticated, reveals the Dashboard section at the bottom (`#dashboard`) with real-time scan logs, results table, and stop button.
- **`login.vue`** — Invisible callback handler ONLY. If `?code=` is present → exchange token → redirect to `/`. If no code → redirect to `/`.

### SSE Streaming

- Scan uses `GET /scan/stream?scan_id=...` (Server-Sent Events)
- Stop scan uses `POST /scan/stop/{scan_id}`
- `active_scans` dict in `mailshield_api.py` maps `scan_id → threading.Event`
- Backend yields events with types: `log`, `progress`, `start`, `result`, `done`, `error`

## Key Files

| File                                      | Purpose                                                     |
| ----------------------------------------- | ----------------------------------------------------------- |
| `backend/config.py`                       | All config including `REDIRECT_URI`                         |
| `backend/mailshield_api.py`               | FastAPI routes including SSE scan stream                    |
| `backend/services/scan_service.py`        | ML scanning logic, yields SSE events                        |
| `backend/auth/oauth.py`                   | Google OAuth flow (get URL, exchange code, refresh, revoke) |
| `frontend-web/app/pages/index.vue`        | Landing page & Scan Dashboard (Merged)                      |
| `frontend-web/app/pages/login.vue`        | OAuth callback catcher                                      |
| `frontend-web/app/composables/useApi.ts`  | All API calls                                               |
| `frontend-web/app/composables/useAuth.ts` | Auth state, login(), logout()                               |

## Startup

```powershell
# From project root:
.\start.ps1
```

Script starts:

1. FastAPI backend on port 8000 (hidden background process)
2. Nuxt frontend on port 8501 (foreground — Ctrl+C to stop both)

## ML Labels (11 categories)

| Label        | Color      | Use                                     |
| ------------ | ---------- | --------------------------------------- |
| Phishing     | Dark Red   | Credential harvesting, fake login pages |
| Spam         | Red        | Bulk unsolicited mail                   |
| Security     | Blue       | Security alerts, account notifications  |
| Needs Review | Amber      | Low-confidence predictions              |
| Banking      | Dark Green | Financial institutions                  |
| Orders       | Purple     | Shopping receipts, tracking             |
| Work         | Navy       | Professional correspondence             |
| Education    | Cyan       | Schools, courses, certifications        |
| Promotions   | Orange     | Marketing emails                        |
| Personal     | Gray       | From known contacts                     |
| Trusted      | Green      | Verified safe senders                   |

## Common Pitfalls

- **"Connection to server lost" during scan**: The backend process might be a zombie from a previous session. Run `Stop-Process -Name python -Force` before restarting.
- **"/login 404"**: `REDIRECT_URI` in config.py doesn't include `/login` suffix, or `login.vue` was accidentally deleted.
- **"Scope has changed" error**: Make sure `openid` is in the requested scopes list inside `backend/config.py` along with email, profile, etc.
- **"circles around itself"**: `index.vue` was also handling `?code=` OAuth callback — only `login.vue` should do this.
- **Labels cut off in table**: Ensure the dashboard container has a wider max-width (e.g. `1600px` or `95%`) and `whitespace-nowrap` on `td`.

## Inspira UI & Animation Architecture

- **`useMotionPresets.ts`**: Centralized composable providing `fadeUp`, `scaleIn`, and `hoverLift` spring animation presets.
- **`lenis.client.ts`**: Desktop-only smooth scroll initialization using `@studio-freight/lenis`.
- **SSE Item Batching**: In `index.vue` (dashboard section), fast SSE `result` stream events are queued into `resultBatchQueue` and flushed every 100ms.
- **Global `WavyBackground.vue`**: High-end interactive canvas hero background applied **globally** in `app.vue`.

## UI & Component Map (Where to find what)

**Layout & Main Sections (`frontend-web/app/pages/index.vue`)**:
- **Header (`<header>`)**: Seamless floating navbar (`bg-transparent border-none py-6`) with no dark background bar, allowing background waves to flow cleanly through to the top edge behind the brand logo and profile controls.
- **Hero Section (`id="hero"`)**: The main title "Secure Your Inbox" with the large CTA button that auto-scrolls to the dashboard or logs the user in.
- **Features Grid (`id="features"`)**: 3-column grid explaining Core Engine, Action, and Live Processing.
- **Pipeline Flow (`id="how-it-works"`)**: The 4-step vertical timeline featuring IDE window cards with top bar dots, glassmorphic backdrop, and custom code syntax highlighting.
- **Dashboard Section (`id="dashboard"`)**: Conditionally rendered (`v-if="authenticated"`) at the bottom of the page. Contains the live scanning terminal and the max 1600px wide scan results table.

**Reusable Components (`frontend-web/app/components/`)**:
- **`InteractiveHoverButton.vue`**: Fluid buttons used for "Secure Your Inbox", Header actions, and Dashboard controls. Features an expanding background circle and slide-in arrow.
- **`ScanStats.vue`**: Component used in the dashboard header to display counters (Total, Spam, Phishing, Clean).
- **`LabelBadge.vue`**: Colored pill badges used in the dashboard results table to display the ML prediction category.
- **`WavyBackground.vue`**: The animated canvas background rendered globally (uses `fixed inset-0` with bounded sinusoidal Y-parallax to keep waves centered in viewport at all scroll depths including page bottom, `waveWidth: 100`, `blur: 23`).




## Enterprise Threat Intelligence Layer (Added 2026-07-30)
- Added ackend/threat_intelligence module.
- Acts as a pre-filter before the ML model inside scan_service.py (_process_single_email).
- Uses config.json for block severity (critical, high).
- Downloads, parses and caches threat feeds into Python sets.
- Starts automatically at FastAPI startup (mailshield_api.py).
- Does not modify existing ML logic (predict.py, models).


## Detection Architecture

### Layer 1: Threat Intelligence
- Known malicious URLs
- Blacklisted domains
- Disposable domains
- Security rules

### Layer 2: Machine Learning
- TF-IDF
- LinearSVC
- Unknown pattern detection

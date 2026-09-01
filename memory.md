# Igrris AI — Project Memory

## Architecture

```
Landing Page (/)
      │ "Connect Gmail" button
      ▼
Google OAuth (accounts.google.com)
      │ redirects to REDIRECT_URI
      ▼
/login?code=... (frontend OAuth callback catcher)
      │ calls POST /auth/callback on backend -> Sets HTTP-only secure Cookie (igrris_session=<UUID>)
      ▼
/dashboard (scanning interface)
      │ calls POST /scan/token (returns 60s single-use token)
      │ calls GET /scan/stream?scan_token=... (SSE)
      ▼
FastAPI Backend (port 8000)
      │ validates session cookie / scan_token -> user_id -> loads credentials/<user_id>.json
      ▼
Threat Intelligence Pre-filter (Blocks known malicious URLs/domains)
      │
      ▼
Igrris ML Backend (TF-IDF + LinearSVC)
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
- `active_scans` dict in `igrris_api.py` maps `scan_id → threading.Event`
- Backend yields events with types: `log`, `progress`, `start`, `result`, `done`, `error`

## Key Files

| File                                      | Purpose                                                     |
| ----------------------------------------- | ----------------------------------------------------------- |
| `backend/config.py`                       | All config including `REDIRECT_URI`                         |
| `backend/igrris_api.py`                   | FastAPI routes including SSE scan stream & Label APIs       |
| `backend/services/scan_service.py`        | ML scanning logic, yields SSE events                        |
| `backend/auth/oauth.py`                   | Google OAuth flow (get URL, exchange code, refresh, revoke) |
| `backend/labels/manager.py`               | Gmail Managed label creation and deletion logic             |
| `frontend-web/app/pages/index.vue`        | Landing page & Scan Dashboard (Merged)                      |
| `frontend-web/app/pages/login.vue`        | OAuth callback catcher                                      |
| `frontend-web/app/components/EncryptedText.vue` | Cyber text encryption scramble component for header brand |
| `frontend-web/app/composables/useApi.ts`  | All API calls                                               |
| `frontend-web/app/composables/useAuth.ts` | Auth state, login(), logout()                               |
| `requirements.txt`                        | Python backend dependencies manifest                        |
| `old-code-files/`                         | Archive of legacy root-level scripts no longer used in the active project (api.py, app.py, predict.py, train.py, data_preprocessing.py, sms-spam-detection.ipynb, spam.csv, etc.) |

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

## Inspira UI & Animation Architecture

- **`useMotionPresets.ts`**: Centralized composable providing `fadeUp`, `scaleIn`, and `hoverLift` spring animation presets.
- **`lenis.client.ts`**: Desktop-only smooth scroll initialization using `@studio-freight/lenis`.
- **SSE Item Batching**: In `index.vue` (dashboard section), fast SSE `result` stream events are queued into `resultBatchQueue` and flushed every 100ms.
- **Global `WavyBackground.vue`**: High-end interactive canvas hero background applied **globally** in `app.vue`.

---

## Session Change Log (2026-07-31)

### 1. Gmail Label Management & Deletion System
- Implemented `delete_managed_label` and `delete_all_managed_labels` in `backend/labels/manager.py`.
- Created FastAPI endpoints `POST /labels/delete` and `GET /labels` in `backend/igrris_api.py`.
- Added `deleteLabels` and `getLabels` functions in `frontend-web/app/composables/useApi.ts`.
- Built dark glassmorphic label deletion modal in `frontend-web/app/pages/index.vue` with individual and batch label deletion support.
- System safeguards: System labels (`INBOX`, `SPAM`, `TRASH`) protected against accidental deletion; only custom managed labels are removed.
- Added comprehensive unit tests in `tests/test_labels.py`.

### 2. Header Brand Encrypted Text Scramble Component
- Created reusable component `frontend-web/app/components/EncryptedText.vue`.
- Features cyber text cipher animation (~70ms frame tick) that decrypts to `"Igrris"`, holds clear text for 3 seconds (`:interval="3000"`), and repeats continuously.
- Integrated `<EncryptedText>` exclusively for the top-left header navbar brand title in `frontend-web/app/pages/index.vue`.
- Added hover trigger so hovering over the brand logo text initiates a scramble cycle.

### 3. Shadow Monarch Helmet Shield Logo & Transparent Header Layout
- Integrated custom logo asset `photos/logo2-bg-removed.png` as `/logo.png` in `frontend-web/public/logo.png`.
- Updated logo container in `index.vue` to be completely transparent (`bg-transparent border-0 p-0 shadow-none`).
- Fine-tuned header brand layout sizing (`w-20 h-20` emblem box with `text-xl sm:text-2xl font-black` title text) for clean visual alignment.

### 4. Pip Dependencies Manifest (`requirements.txt`)
- Updated root `requirements.txt` to lock all backend required dependencies:
  - `scikit-learn`, `pandas`, `nltk`, `numpy` (ML & NLP)
  - `fastapi`, `uvicorn`, `pydantic` (Backend REST API)
  - `google-auth`, `google-auth-oauthlib`, `google-api-python-client` (OAuth & Gmail API)
  - `Pillow` (Image & logo transparency processing)
  - `pytest`, `httpx` (Testing & async HTTP)

### 5. Canvas strokeStyle Type Check Fix (`WavyBackground.vue`)
- Fixed TypeScript type mismatch `string | undefined` is not assignable to `string | CanvasGradient | CanvasPattern` on line 101 of `frontend-web/app/components/WavyBackground.vue`.
- Added nullish coalescing fallback `?? '#ffffff'` for `props.colors[i % totalColors]` array index access to satisfy strict TypeScript array indexing rules (`noUncheckedIndexedAccess`).

### 6. EncryptedText TypeScript Type Check Fix (`EncryptedText.vue`)
- Fixed TypeScript type error `Type 'string | undefined' is not assignable to type 'string'` on line 48 of [EncryptedText.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/components/EncryptedText.vue).
- Replaced string bracket index lookup `chars[index]` with `chars.charAt(index)` which strictly returns `string`, satisfying TypeScript's return type signature for `getRandomChar(): string`.

### 7. SSE EventSource MessageEvent Type Check Fix (`index.vue`)
- Fixed TypeScript type error `Property 'data' does not exist on type 'Event'` on lines 979-1016 of [index.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/pages/index.vue).
- Added explicit type casting `(e as MessageEvent)` for all EventSource event listeners (`log`, `progress`, `start`, `result`, `done`, `error`), resolving `Property 'data' does not exist on type 'Event'` DOM event type mismatch in TypeScript.

### 8. Vue Component `class` Prop Binding Type Check Fix (`InteractiveHoverButton.vue`, `ShimmerButton.vue`, `WavyBackground.vue`, `EncryptedText.vue`)
- Fixed TypeScript error `Type '{ 'opacity-50 cursor-not-allowed': boolean; }' is not assignable to type 'string'` when passing object/array class bindings to `<InteractiveHoverButton>` in [index.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/pages/index.vue#L190-L196).
- Updated `class?: string` to `class?: any` across UI components so Vue's object (`:class="{ key: val }"`) and array class bindings are supported without type checking errors.

### 9. Solo Leveling Metallic Igris Typography (`EncryptedText.vue`)
- Resolved Chromium WebKit `background-clip: text` rendering bug in [EncryptedText.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/components/EncryptedText.vue):
  - **Chromium Rendering Fix**: Replaced inline `text-shadow` with `filter: drop-shadow(...)`.
  - **6-Stop High-Contrast Steel Armor Gradient**: `linear-gradient(180deg, #ffffff 0%, #e4e4e7 18%, #71717a 38%, #18181b 52%, #a1a1aa 72%, #ffffff 88%, #3f3f46 100%)`.
  - **Outer Dark Bevel & Red Aura**: Multi-layer `filter: drop-shadow(...)` preserves gradient visibility with dark armor drop-shadows and red eye energy glow.

---

## Session Change Log (2026-08-02)

### 10. Deployment: Vercel (Frontend) + Railway (Backend)

- **`railway.toml`** (NEW): Nixpacks build + start command `uvicorn backend.igrris_api:app --host 0.0.0.0 --port $PORT` + healthcheck `/health`.
- **`backend/config.py`**: `OAUTHLIB_INSECURE_TRANSPORT` now only set when `DEBUG=true`. Safe for production Railway (HTTPS).
- **`backend/igrris_api.py`**: CORS `allow_origins` now reads from `ALLOWED_ORIGINS` env var (comma-separated). Falls back to localhost for dev.
- **`frontend-web/nuxt.config.ts`**: Added `googleClientId` to `runtimeConfig.public` — maps to `NUXT_PUBLIC_GOOGLE_CLIENT_ID` env var.
- **`.env.example`** (root): Documents all backend prod env vars (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REDIRECT_URI`, `ALLOWED_ORIGINS`, `DEBUG`).
- **`frontend-web/.env.example`**: Documents `NUXT_PUBLIC_API_BASE` and `NUXT_PUBLIC_GOOGLE_CLIENT_ID`.
- **`.env`** (local): Added `ALLOWED_ORIGINS` for localhost and `DEBUG=true` so local dev still works.

### Deployment Environment Variables

| Platform | Variable | Value |
|---|---|---|
| Vercel | `NUXT_PUBLIC_API_BASE` | `https://your-api.up.railway.app` |
| Vercel | `NUXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| Railway | `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| Railway | `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| Railway | `REDIRECT_URI` | `https://your-app.vercel.app/login` |
| Railway | `ALLOWED_ORIGINS` | `https://your-app.vercel.app` |

### Google Cloud Console — Required URI
Add `https://your-app.vercel.app/login` to:
> Credentials → OAuth 2.0 Client → Authorized Redirect URIs

---

## Flash of Unstyled Content (FOUC) Fix — 2026-08-06

**Problem:** On first page load, there was a brief white/unstyled flash before the dark-mode styles appeared.

**Root Cause:** `app.vue` was applying the `dark` class via `process.client` (runs after hydration). During SSR + hydration gap, the `<html>` element had no `dark` class → browser briefly rendered light styles.

**Fix Applied:**
- Added a **blocking inline `<script>`** in `nuxt.config.ts` → `app.head.script` that sets `dark` class AND `background-color: #030712` on `<html>` **before the first paint**.
- Removed the `process.client` setter from `app.vue` (redundant and late).

**Key files changed:**
- `frontend-web/nuxt.config.ts` — added `script: [{ innerHTML: "document.documentElement.classList.add('dark');document.documentElement.style.backgroundColor='#000000';" }]`
- `frontend-web/app/app.vue` — added `<SplashScreen />` overlay component
- `frontend-web/app/components/FallingStarsBg.vue` — Inspira UI HTML5 canvas-based meteor/falling stars background component with mobile fallback viewport dimensions.
- `frontend-web/app/components/SplashScreen.vue` — Pitch-black fullscreen splash screen incorporating `FallingStarsBg`, centered glowing logo, scramble text, and smooth fade-out.
- `frontend-web/app/pages/index.vue` & `frontend-web/app/components/WavyBackground.vue` — Fixed mobile right-side text & card cutoff in "How it works" section by shifting timeline line position (`left-5`), reducing container left padding (`pl-12 sm:pl-16`), and wrapping code snippets (`whitespace-pre-wrap break-all`).

---

## Mobile View Alignment & Scan Results Hiding Fix — 2026-08-07

### 11. Mobile View Layout Refinements & Persistent Scan Results (`index.vue`, `EmailDetails.vue`, `ScanStats.vue`)

- **Fixed Scan Gmail Button Hiding Results**:
  - **Problem**: When user clicked "Scan Gmail" button (`#btn-scan-results` / `#btn-scan-empty`), the results section condition was `!scanning && results.length > 0`. This caused the entire results section (stats strip, filter controls, results table, email detail view) to completely vanish while scanning was active, popping back up only after scanning stopped.
  - **Fix**: Updated condition to `<div v-if="results.length > 0">`. Now, during scanning, the live terminal card displays at the top, and the results table remains visible directly below it, updating live in real-time as SSE streams results.
- **Mobile Alignment & Touch Sizing**:
  - **Scanning Live Terminal State**: Converted top header to responsive `flex-col sm:flex-row`, adjusted card padding (`p-4 sm:p-6 md:!p-8`) to prevent horizontal clipping on 360px-430px viewports.
  - **Results Toolbar**: Placed "Scan Gmail" and "Delete Labels" buttons in a responsive 2-column grid container (`grid grid-cols-2 sm:flex`), ensuring full touch-target width (`w-full sm:w-auto`), centered text, and balanced text sizes (`text-xs sm:text-sm`).
  - **Email Table & Mobile Row Badges**: Added horizontal overflow scroll wrapper (`overflow-x-auto`), constrained sender column width on mobile (`w-36 sm:w-64 max-w-[130px] sm:max-w-none`), and rendered an inline `<LabelBadge>` next to subject line on `< sm` screens so mobile users see email categories directly in the list.
  - **Slide-Over Panel (`EmailDetails.vue`)**: Configured slide panel to `w-full sm:max-w-lg`, added `p-4 sm:p-6` mobile padding, set metadata cards to single column on mobile (`grid-cols-1 sm:grid-cols-2`), and updated stacking order to `z-50`.
  - **Stats Strip (`ScanStats.vue`)**: Added touch padding (`!p-3 sm:!p-4`), truncated long label names, and tuned grid gaps (`gap-2.5 sm:gap-3`).

---

## Frontend Checklist Audit & Best Practices Fixes — 2026-08-07

### 12. Frontend Checklist Compliance ([mcp.frontendchecklist.io](https://mcp.frontendchecklist.io))

- **HTML Foundations & SEO**:
  - Configured `htmlAttrs: { lang: 'en' }` in [nuxt.config.ts](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/nuxt.config.ts).
  - Added full OpenGraph metadata (`og:type`, `og:title`, `og:description`, `og:image`) and Twitter Cards (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`).
  - Added `{ name: 'theme-color', content: '#000000' }` meta tag.
- **Accessibility & ARIA**:
  - Modal dialogs: Added `role="dialog"`, `aria-modal="true"`, `aria-labelledby` to Delete Labels modal in [index.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/pages/index.vue#L768-L785) and detail panel in [EmailDetails.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/components/EmailDetails.vue#L1-L15).
  - Explicit `type="button"` attributes added across [InteractiveHoverButton.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/components/InteractiveHoverButton.vue), [ShimmerButton.vue](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/igrris/frontend-web/app/components/ShimmerButton.vue), and form action buttons to avoid accidental form submissions.
  - Added explicit `aria-label` tags on input fields and icon-only close buttons.
- **Performance**:
  - Added `decoding="async"` and explicit dimensions (`width`, `height`) on image elements.

---

## Mobile Sizing Round 2 — 2026-08-07

### Changes to `index.vue`
- **Header**: Reduced vertical padding from `pt-4 pb-4` → `pt-3 pb-3` on mobile. Shrank profile avatar from `w-8 h-8` → `w-6 h-6` on mobile (sm: stays w-8). Reduced "Sign out" button padding and text from `text-xs` → `text-[11px]` on mobile. Auth pill gaps/padding reduced on mobile.
- **Logo**: Increased from `w-9 h-9` → `w-10 h-10` on mobile so it's slightly more visible (was too small).
- **Hero Section**: Reduced top padding from `pt-12` → `pt-8` and bottom `pb-16` → `pb-10` on mobile. Shimmer button text reduced from `text-lg` → `text-base sm:text-lg` on mobile.
- **Feature Cards**: Padding reduced from fixed `p-8` → `p-5 sm:p-8`, icon boxes from `w-12 h-12` → `w-10 h-10 sm:w-12 sm:h-12`, headings from `text-xl` → `text-base sm:text-xl` on mobile.
- **Dashboard Main**: Horizontal padding `px-4` → `px-3` on mobile; vertical `py-8` → `py-4 sm:py-8`.
- Build verified successfully with `npm run build`.

---

## Session Change Log (2026-08-23)

### 13. Multi-User OAuth Security Fix (Session Isolation)
- **Problem**: A critical security issue existed where a single global `token.json` and `.oauth_state` meant all users shared the same Google credentials.
- **Session Management**: Built `backend/auth/session.py` with an in-memory session store (`_SessionStore`). The browser identity is now tracked via a cryptographically random, HTTP-only, Secure cookie (`igrris_session`), mapping to an internal `user_id`.
- **Per-User Credentials**: Rewrote `backend/auth/oauth.py` to save Google credentials per-user in `credentials/<user_id>.json`. Added UUID path traversal protection.
- **SSE Token Bridge**: Implemented `POST /scan/token` to bridge the single-use, short-lived tokens (60s) for cross-origin EventSource connections (`/scan/stream`), as SSE cannot send cross-origin cookies.
- **Frontend Integration**: Updated `frontend-web/app/composables/useApi.ts` to include `credentials: 'include'` and utilize the 2-step scan stream initialization (`/scan/token` followed by `EventSource`). Updated `index.vue` to extract and forward the OAuth `state` parameter for CSRF validation.

### 14. Root `.gitignore` Audit & Cleanup
- Restructured root `.gitignore` to preserve Nuxt/Node and Python rules.
- Ensured sensitive files are strictly ignored to prevent credential leaks: added rules for `token.json`, `.oauth_state`, `credentials/`, `*.pem`, `*.key`, and `backend/threat_intelligence/runtime_data/`.

### 15. Threat Intelligence Lifecycle Fix
- **Data Segregation**: Separated Git-tracked `SEED_DATA_DIR` (`backend/threat_intelligence/data/`) from `RUNTIME_DATA_DIR` (`backend/threat_intelligence/runtime_data/` or `TI_RUNTIME_DIR` env var).
- **Cache Fallback**: Updated `backend/threat_intelligence/cache.py` to prioritize `RUNTIME_DATA_DIR/file` (if present and >0 bytes) and seamlessly fall back to `SEED_DATA_DIR/file` (useful for ephemeral environments without mounted volumes).
- **Updates**: Modified `backend/threat_intelligence/updater.py` to save feeds (`metadata.json`, `statistics.json`) securely into `RUNTIME_DATA_DIR` using `.tmp` files and atomic `os.replace`.
- **Git Hygiene**: Restored `backend/threat_intelligence/data/` files to a clean git state, ensuring `git status` remains clean after running feed updates.
- **Regex Expansion**: Updated `backend/threat_intelligence/engine.py`'s `_extract_urls` to support `ftp://` protocol matching (e.g., URLhaus feeds).
- **Testing**: Added `tests/test_threat_intelligence.py` to cover TI engine pre-filter, FTP URL extraction, and seed vs runtime fallback logic.

### 16. IDE Virtualenv Alias Fix
- Addressed Pyrefly IDE in-memory diff buffer errors (`c:\__pyrefly_virtual__\inmemory\*.py`) and module resolution issues (`pytest`, `fastapi.testclient`) by creating a `.venv` directory junction pointing to `venv` on Windows. All 39 unit tests pass perfectly.

### 17. Frontend SSE Stream Initialization & Variable Scoping Fix
- **Scan Token Integration**: Added `getScanToken()` in `frontend-web/app/composables/useApi.ts` and updated `startScan()` in `frontend-web/app/pages/index.vue` to fetch the token before instantiating `EventSource`.
- **Variable Scope**: Fixed `const es` inside the `try` block which was previously block-scoped and prevented the 7 SSE event listeners (`log`, `progress`, `start`, `result`, `done`, `error`, `onerror`) from attaching to the stream.
- **Safe Error Parsing**: Guarded `JSON.parse` against undefined `data` payloads on connection errors.

### 18. OAuth Callback State & Confidential Client Fix
- **Problem**: When user completed Google OAuth, if the in-memory session was cleared (due to server restart or cross-origin redirect drop), `exchange_code` threw `"No OAuth state found in session. Possible CSRF attack or expired session."`
- **Fix**: Updated `Flow.from_client_config` with `autogenerate_code_verifier=False` (using standard confidential client authorization with `client_secret`) and enabled `exchange_code` to accept `body.state` from the Google redirect. If session state exists, it validates against CSRF mismatch; if lost due to container restart, it gracefully completes the token exchange using the verified authorization code and client secret.

---

## Production Deployment Context (Vercel + Railway)

### Architecture Context
- **Frontend**: Nuxt 3 hosted on **Vercel** (`https://igrris.vercel.app`).
- **Backend**: FastAPI hosted on **Railway** (`https://igrris.up.railway.app`).
- **Google Cloud Console**: OAuth 2.0 Client credentials registered for both local and production redirect URIs.

### Multi-User Migration & Cross-Origin Invariants
1. **Cross-Origin Cookie Protocol**:
   - Vercel and Railway operate on different domains (`vercel.app` vs `up.railway.app`).
   - Browser cookies require `SameSite=None` and `Secure=True` in production (`DEBUG=false`).
   - Backend CORS must have `allow_credentials=True` with explicit `ALLOWED_ORIGINS` (e.g. `https://igrris.vercel.app`, not wildcard `*`).
   - Frontend `fetch` calls must specify `credentials: 'include'`.
2. **SSE Streaming (Cross-Origin)**:
   - `EventSource` cannot send cross-origin cookies.
   - Flow: Frontend calls `POST /scan/token` (authenticated via session cookie) → receives 60-second single-use `scan_token` → opens `GET /scan/stream?scan_token=...&scan_id=...`.
3. **Session Store & Ephemeral Containers**:
   - The in-memory session store (`_SessionStore`) lives in backend RAM. If Railway restarts, active in-flight OAuth attempts are wiped, requiring a fresh login click.
   - For user credentials to survive Railway redeployments, a Railway Persistent Volume must be mounted at `/app/credentials` and `CREDENTIALS_DIR=/app/credentials` set in environment variables.

### Environment Variable Checklist

| Location | Variable | Value Description |
|---|---|---|
| **Vercel (Frontend)** | `NUXT_PUBLIC_API_BASE` | `https://igrris.up.railway.app` (or your Railway domain) |
| **Vercel (Frontend)** | `NUXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| **Railway (Backend)** | `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| **Railway (Backend)** | `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| **Railway (Backend)** | `REDIRECT_URI` | `https://igrris.vercel.app/login` |
| **Railway (Backend)** | `ALLOWED_ORIGINS` | `https://igrris.vercel.app` |
| **Railway (Backend)** | `DEBUG` | `false` (enables `Secure=True`, `SameSite=None`) |
| **Railway (Backend)** | `CREDENTIALS_DIR` | `/app/credentials` (with Railway Volume mounted) |
| **Google Cloud Console** | Authorized Redirect URI | `https://igrris.vercel.app/login` and `http://localhost:8501/login` |

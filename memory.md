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
      │ calls POST /auth/callback on backend
      ▼
/dashboard (scanning interface)
      │ calls GET /scan/stream (SSE)
      ▼
FastAPI Backend (port 8000)
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
- `frontend-web/nuxt.config.ts` — added `script: [{ innerHTML: "document.documentElement.classList.add('dark');..." }]`
- `frontend-web/app/app.vue` — removed `process.client` dark class setter

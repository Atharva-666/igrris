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
| `localhost:8501/`          | `index.vue`     | Public landing page — explains features, has "Connect Gmail" CTA                                          |
| `localhost:8501/login`     | `login.vue`     | **OAuth callback catcher** — catches `?code=` from Google, exchanges for token, redirects to `/dashboard` |
| `localhost:8501/dashboard` | `dashboard.vue` | Protected page — shows real-time scan logs, results table, stop button                                    |

## Critical Rules

### OAuth Flow

- `REDIRECT_URI` in `backend/config.py` MUST be `http://localhost:8501/login`
- This MUST also exactly match what is registered in **Google Cloud Console** → Credentials → OAuth 2.0 Client → Authorized Redirect URIs
- If you change the port, update BOTH `config.py` AND Google Cloud Console

### Page Responsibilities

- **`index.vue`** — Pure landing page. NO OAuth callback handling. Only redirects already-authenticated users to `/dashboard`.
- **`login.vue`** — Invisible callback handler ONLY. If `?code=` is present → exchange token → redirect to `/dashboard`. If no code → redirect to `/`.
- **`dashboard.vue`** — Protected. If not authenticated → redirect to `/`.

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
| `frontend-web/app/pages/index.vue`        | Landing page                                                |
| `frontend-web/app/pages/login.vue`        | OAuth callback catcher                                      |
| `frontend-web/app/pages/dashboard.vue`    | Scan dashboard                                              |
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
- **"circles around itself"**: `index.vue` was also handling `?code=` OAuth callback — only `login.vue` should do this.
- **Labels cut off in table**: Ensure the Label `th` has `w-48` and the `td` has `whitespace-nowrap`.

## Inspira UI & Animation Architecture

- **`useMotionPresets.ts`**: Centralized composable providing `fadeUp`, `scaleIn`, and `hoverLift` spring animation presets with `prefers-reduced-motion` auto-detection.
- **`lenis.client.ts`**: Desktop-only smooth scroll initialization using `@studio-freight/lenis`. Automatically skipped on mobile screens (`<=768px`) or when reduced motion is requested. Pauses `requestAnimationFrame` on `visibilitychange` (hidden tab).
- **SSE Item Batching**: In [`dashboard.vue`](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/MailShield-AI/frontend-web/app/pages/dashboard.vue), fast SSE `result` stream events are queued into `resultBatchQueue` and flushed every 100ms to prevent layout thrashing and animation lag.
- **Page Transitions**: Smooth 0.4s cubic-bezier page transitions defined in [`app.vue`](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/MailShield-AI/frontend-web/app/app.vue).
- **Global `WavyBackground.vue`**: High-end interactive canvas hero background creating smooth, non-repeating sine waves in a monochrome palette (`#ffffff`, `#e5e5e5`, etc.). Applied **globally** in [`app.vue`](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/MailShield-AI/frontend-web/app/app.vue) so it renders behind all pages. Card components use `backdrop-blur` to let the sweeping waves shine through.
- **Buttons**: All buttons across the app (Landing Page CTA, Header, Dashboard actions) upgraded to **[`InteractiveHoverButton.vue`](file:///c:/Users/VICTUS/OneDrive/Attachments/Desktop/MailShield-AI/frontend-web/app/components/InteractiveHoverButton.vue)**, featuring a fluid expanding background circle and slide-in arrow on hover.



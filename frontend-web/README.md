# MailShield AI — Nuxt Frontend

Modern Nuxt 3/4 frontend for the MailShield AI Gmail security assistant.

## Stack

- **Nuxt 4** (Vue 3, TypeScript, Composition API)
- **Tailwind CSS** — dark mode by default
- **Lucide Icons** (via inline SVG)
- **Lenis** — smooth scrolling (installed as a plugin)

## Getting Started

### 1. Start the FastAPI backend

From the **project root**:

```bash
venv\Scripts\uvicorn backend.mailshield_api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Nuxt dev server

```bash
cd frontend-web
npm run dev
```

Open **http://localhost:3000** in your browser.

### 3. Configure environment (optional)

Copy `.env.example` to `.env.local` and adjust `NUXT_PUBLIC_API_BASE` if your API runs on a different URL.

## Project Structure

```
frontend-web/
├── app/
│   ├── app.vue                   # Root component (dark mode)
│   ├── assets/css/main.css       # Global Tailwind styles
│   ├── components/
│   │   ├── EmailDetails.vue      # Slide-over panel
│   │   ├── LabelBadge.vue        # Label color pill
│   │   └── ScanStats.vue         # Stats cards
│   ├── composables/
│   │   ├── useApi.ts             # FastAPI HTTP abstraction
│   │   └── useAuth.ts            # Reactive auth state
│   ├── middleware/
│   │   └── auth.global.ts        # Auth route guard
│   └── pages/
│       ├── index.vue             # Dashboard
│       └── login.vue             # Login / OAuth callback
├── nuxt.config.ts
├── tailwind.config.ts
└── .env.example
```

## API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness check |
| GET | /auth/url | Get Google OAuth URL |
| POST | /auth/callback | Exchange code for credentials |
| GET | /auth/status | Check if authenticated |
| POST | /auth/logout | Revoke credentials |
| POST | /scan | Run full Gmail scan (sync) |

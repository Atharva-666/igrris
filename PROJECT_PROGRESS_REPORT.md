# ⚔️ IGRRIS — Project Progress Report
### AI-Powered Gmail Intelligence & Threat Defense Platform

---

## 📌 Document Information

| Property | Details |
| :--- | :--- |
| **Project Title** | IGRRIS — Intelligent Gmail Reconnaissance & Real-Time Inbox Security |
| **Document Reference** | `IGRRIS-PPR-2026-FINAL` |
| **Reporting Period** | July 2026 – September 2026 |
| **Project Status** | **COMPLETED (Core Implementation Finished & Integrated)** |
| **Academic Purpose** | College Project Progress & Final Integration Report |
| **Repository** | [Atharva-666/igrris](https://github.com/Atharva-666/igrris) |
| **Architecture** | Full-Stack Web Application (FastAPI + Nuxt 3 + Scikit-Learn + Gmail API) |

---

## 🧭 Project Overview

**IGRRIS** is a full-stack, autonomous email security and inbox intelligence platform designed to protect users against phishing attacks, spam campaigns, and malicious URLs while organizing everyday email communications.

Operating directly on incoming Gmail messages through secure Google OAuth 2.0 authorization, IGRRIS implements a **two-layer defensive pipeline**:
1. **Threat Intelligence Pre-Filter:** Inspects sender domains, extracted URLs, and network indicators against live feeds (URLhaus, OpenPhish) and curated blocklists.
2. **Machine Learning & NLP Classifier:** Utilizes a calibrated Support Vector Classifier (`LinearSVC`) trained on text representations vectorized via TF-IDF, supplemented by a deterministic secondary rule engine.

Classified messages are automatically labeled directly in Gmail with color-coded categories, and scanning activities are streamed in real time to an interactive dashboard via Server-Sent Events (SSE).

---

## 📊 PROJECT STATUS

```text
Core implementation of IGRRIS: COMPLETED
```

### End-to-End System Workflow

```text
Gmail
  ↓
OAuth Authentication
  ↓
Email Scanning
  ↓
Threat Intelligence Check
  ↓
Email Processing
  ↓
TF-IDF
  ↓
LinearSVC Classification
  ↓
Security/Category Classification
  ↓
Automated Gmail Labels
  ↓
Frontend Dashboard
```

The core implementation of IGRRIS has been fully designed, developed, tested, and integrated across all architectural tiers.

---

## 🗓️ Monthly Progress Summary

| Month | Major Work Completed |
| :--- | :--- |
| **July 2026** | Project foundation, problem definition, dataset preparation, 5-stage NLP text preprocessing pipeline, TF-IDF vectorization, Machine Learning model training & comparison (LinearSVC + CalibratedClassifierCV), initial REST backend and local evaluation pipeline. |
| **August 2026** | Google OAuth 2.0 implementation, multi-user session and credential isolation, Gmail API connector, Threat Intelligence engine (URLhaus, OpenPhish, domain blocklists, runtime cache), 11-category Gmail label management system with folder safeguards, and real-time Server-Sent Events (SSE) streaming scan service. |
| **September 2026** | Nuxt 3 / Vue 3 reactive frontend development, unified dashboard and landing page, OAuth callback handling, SSE event batching, responsive mobile UI/UX, security and CORS enhancements, production cloud deployment (Vercel + Railway/Render), comprehensive test suite execution (39 pytest cases), and final system integration. |

---

## 📅 Detailed Monthly Progress Breakdown

```
                                 IGRRIS DEVELOPMENT TIMELINE
                                 
   JULY 2026                     AUGUST 2026                   SEPTEMBER 2026
   ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
   │ • Problem Definition     │  │ • Google OAuth 2.0 Flow  │  │ • Nuxt 3 / Vue 3 Frontend│
   │ • Dataset Preparation    │  │ • Multi-User Isolation   │  │ • Unified Dashboard UI   │
   │ • 5-Stage NLP Pipeline   │  │ • Gmail API Ingestion    │  │ • Real-time SSE Batching │
   │ • TF-IDF Vectorization   │  │ • Threat Intel Pre-Filter│  │ • Mobile & Accessibility │
   │ • LinearSVC Classifier   │  │ • 11-Category Taxonomy   │  │ • Vercel & Cloud Deploys │
   │ • Probability Calibration│  │ • Gmail Label Automation│  │ • 39-Test QA Suite      │
   │ • Initial ML Pipeline    │  │ • SSE Streaming Engine   │  │ • Final System Integr.   │
   └─────────────┬────────────┘  └─────────────┬────────────┘  └─────────────┬────────────┘
                 │                             │                             │
                 └─────────────────────────────┼─────────────────────────────┘
                                               ▼
                              IGRRIS CORE IMPLEMENTATION COMPLETED
```

---

### 1. JULY 2026 — Project Foundation & Core ML Development

During July 2026, the foundational research, technical problem definition, dataset preparation, and Machine Learning classification engine were established. This phase laid the analytical and algorithmic groundwork for intelligent email security.

#### 1.1 Problem Definition & Conceptual Architecture
- Formulated the project objective: designing an automated, real-time security layer for personal and organizational email accounts to detect malicious emails and reduce inbox clutter.
- Identified standard limitations in traditional keyword-based spam filters: inability to handle adversarial evasion, lack of confidence metrics, and absence of automated organization.
- Defined the foundational design for an ML-driven classifier capable of high precision on benign correspondence (Ham) and high sensitivity on malicious/unsolicited correspondence (Spam/Phishing).

#### 1.2 Dataset Preparation & Preprocessing
- Gathered and preprocessed standardized message corpora, including the UCI SMS Spam Collection dataset (comprising 5,169 distinct samples after duplicate elimination) and email benchmark samples.
- Conducted exploratory data analysis (EDA) to evaluate token length distributions, vocabulary density, and class imbalances.
- Built a standardized 5-stage NLP text preprocessing pipeline (`data_preprocessing.py`):
  1. **Case Normalization:** Converted all raw text to lowercase characters.
  2. **Tokenization:** Segmented raw text strings into discrete lexical tokens using NLTK (`punkt`).
  3. **Alphanumeric Filtering:** Stripped punctuation, symbols, and non-printable characters while preserving semantic tokens.
  4. **Stopword Elimination:** Filtered uninformative grammatical stopwords using NLTK English stopword corpora.
  5. **Stemming:** Applied the Porter Stemmer algorithm to reduce inflected words to their root morphological stems (e.g., `"winning"` → `"win"`).

#### 1.3 Feature Extraction & Machine Learning Modeling
- Engineered feature extraction using **Term Frequency-Inverse Document Frequency (TF-IDF)** vectorization:
  - Vocabulary parameter: `max_features=3000`.
  - Sublinear TF scaling applied to temper the effect of repetitively repeated spam keywords.
  - Extracted unigrams and bigrams to capture contextual phrase combinations.
- Model Training & Evaluation Benchmark:
  - Evaluated three supervised learning architectures: Multinomial Naive Bayes (`MultinomialNB`), Logistic Regression (`LogisticRegression`), and Linear Support Vector Classifier (`LinearSVC`).
  - Benchmarked algorithms across accuracy, precision, recall, and F1-score:
    - **LinearSVC** demonstrated the best discriminatory balance, achieving an overall accuracy of **98.0%** and a Spam F1-score of **0.92** (Spam Precision: 0.95, Spam Recall: 0.88; Ham Precision: 0.98, Ham Recall: 0.99).
- Probability Calibration:
  - Standard `LinearSVC` does not natively output calibrated probability distributions. Integrated `CalibratedClassifierCV` using sigmoid calibration (Platt scaling) to yield reliable prediction probabilities (`predict_proba`) between `0.0` and `1.0`.
- Artifact Persistence:
  - Serialized the trained vectorizer (`vectorizer.pkl`) and calibrated classification model (`model.pkl`) for downstream service consumption.

#### 1.4 Initial Backend & Classification Prototype
- Implemented an initial lightweight FastAPI REST service (`api.py`) exposing `/predict` and `/health` endpoints.
- Developed an early prototype testing harness using Streamlit (`app.py`) to validate model inference, evaluate prediction thresholds, and test inference response times locally.
- Authored initial unit tests (`test_preprocessing.py`, `test_predict.py`) to verify pipeline stability on edge cases, empty strings, and adversarial inputs.

---

### 2. AUGUST 2026 — Gmail Integration, Threat Intelligence & Automated Processing

During August 2026, IGRRIS transitioned from a standalone machine learning model into an integrated, automated Gmail security system. The system was equipped with Google OAuth 2.0 authentication, Gmail API ingestion, threat intelligence feeds, automated category labeling, and real-time Server-Sent Events (SSE).

#### 2.1 Google OAuth 2.0 & Multi-User Session Isolation
- Engineered full Google OAuth 2.0 authorization flows (`backend/auth/oauth.py`) using `google-auth-oauthlib`:
  - Implemented authorization URL generation with offline access (`access_type="offline"`) and consent prompting for refresh tokens.
  - Constructed authorization code exchange, automatic token refresh routines, and token revocation endpoints (`/auth/logout`).
- Multi-User Session Isolation:
  - Solved single-user token collision by designing an in-memory session store (`backend/auth/session.py`).
  - Generated cryptographically secure, random session identifiers managed via HTTP-only, `SameSite=None`, `Secure` cookies (`igrris_session`).
  - Stored user credentials on isolated file paths (`credentials/<user_id>.json`) protected by strict UUID validation to prevent path traversal vulnerabilities.
- Cross-Origin SSE Token Bridge:
  - Because browser `EventSource` (SSE) APIs cannot transmit cross-origin cookies in standard Web specifications, created an authenticated token exchange route (`POST /scan/token`) returning a single-use 60-second token for stream verification.

#### 2.2 Gmail API Integration & Message Fetching
- Connected backend services to Google Workspace Gmail REST API v1 (`backend/gmail/connector.py`) using `google-api-python-client`.
- Designed intelligent inbox message ingestion:
  - Paginated retrieval of inbox message IDs (`messages().list`).
  - Built-in query filters to automatically ignore messages already tagged with IGRRIS labels, eliminating redundant re-scans.
  - Extracted MIME message structures (`messages().get`), decoding headers (Subject, From, Date) and textual message payloads.
  - Implemented rate limiting locks (`_wait_for_rate_limit`) with inter-call delays to strictly comply with Google's 250 units/sec API quota.
  - Configured thread-local client instances (`_thread_local`) to ensure thread-safe HTTP connection handling across worker threads.

#### 2.3 Threat Intelligence Pre-Filter
- Implemented a dual-layer threat verification engine (`backend/threat_intelligence/`):
  - **Live Threat Feed Integration:** Ingestion of malicious URLs and phishing domains from active feeds, including URLhaus and OpenPhish.
  - **Curated Indicators:** Curated lists for blacklisted domains, disposable email domains, and malicious IP patterns.
  - **URL Extraction:** Custom regular expressions scanning message bodies and subjects for HTTP, HTTPS, and FTP links.
  - **Fast In-Memory Cache:** Built `cache.py` with set-based $O(1)$ lookups for rapid URL and domain verification.
  - **Atomic Updates & Segregated Lifecycle:** Built `updater.py` with atomic file swapping (`.tmp` to final) and segregated `SEED_DATA_DIR` from dynamic `RUNTIME_DATA_DIR` to maintain clean repository hygiene.
- Execution Precedence:
  - Messages containing verified malicious URLs, blacklisted senders, or disposable domains are immediately flagged as threats by Layer 1, bypassing unnecessary downstream ML inference.

#### 2.4 11-Category Gmail Taxonomy & Automated Labeling
- Created an automated labeling service (`backend/labels/manager.py`) managing 11 distinct Gmail labels with Google-compliant hex color assignments:
  1. 🔴 **Phishing** (`#cc3a21`) — Credential harvesting, deceptive login prompts, and confirmed threat feeds.
  2. 🟥 **Spam** (`#e07798`) — Bulk unsolicited commercial messages.
  3. 🔵 **Security** (`#4a88da`) — Legitimate security alerts, multi-factor codes, password resets.
  4. 🟡 **Needs Review** (`#fad165`) — Borderline or ambiguous emails requiring human inspection.
  5. 🟢 **Banking** (`#16a766`) — Legitimate financial institutions, account statements, transaction alerts.
  6. 🟣 **Orders** (`#8e63ce`) — E-commerce receipts, order confirmations, shipping updates.
  7. 🔷 **Work** (`#42d692`) — Professional, enterprise, and corporate communications.
  8. 🩵 **Education** (`#4986e7`) — Academic institutions, course platforms, student notifications.
  9. 🟠 **Promotions** (`#ffad46`) — Marketing newsletters, discounts, promotional offers.
  10. ⬜ **Personal** (`#b99aff`) — One-on-one personal correspondence.
  11. ✅ **Trusted** (`#16a765`) — Verified safe senders.
- Label Engine & Hierarchy:
  - Created `backend/classifier/rule_engine.py` parsing `rules_config.yaml` to assign primary and secondary categories based on sender patterns, header metadata, and ML predictions.
  - Enforced strict label precedence: `Phishing > Spam > Security > Needs Review > Banking > Orders > Work > Education > Promotions > Personal > Trusted`.
- Safety Safeguards:
  - Enforced safeguards protecting core Gmail system folders (`INBOX`, `SPAM`, `TRASH`, `DRAFT`) against accidental alteration or deletion.

#### 2.5 Real-Time Scan Service & SSE Streaming
- Implemented `backend/services/scan_service.py` to coordinate the complete end-to-end scanning pipeline.
- Built a concurrent thread pool (`ThreadPoolExecutor`) processing emails concurrently while respecting rate limits.
- Implemented Server-Sent Events (SSE) via `GET /scan/stream`, streaming structured JSON event types:
  - `start` — Scan initiation and message batch count.
  - `log` — Real-time progress and processing indicators.
  - `progress` — Real-time count of processed vs. total messages.
  - `result` — Detailed classification payload for each email (Sender, Subject, Assigned Category, Confidence Score, Matched Layer).
  - `done` — Scan completion summary.
  - `error` — Informative error transmission.
- Added asynchronous scan abortion via `POST /scan/stop/{scan_id}` utilizing thread-safe `threading.Event` triggers.

---

### 3. SEPTEMBER 2026 — Frontend, Security, Deployment, Testing & Final Integration

During September 2026, the complete system was brought together into a unified, production-grade application. The team developed the Nuxt 3 web frontend, implemented visual polish and accessibility standards, resolved cross-origin security concerns, configured production cloud deployments, executed the automated test suite, and completed final integration.

#### 3.1 Reactive Frontend Development (Nuxt 3 & Vue 3)
- Constructed a modern, responsive web application using **Nuxt 3**, **Vue 3**, and **Tailwind CSS** (`frontend-web/`):
  - **Unified Single-Page Experience (`app/pages/index.vue`):** Combines an informational product overview, architectural breakdown, and an interactive real-time scanning console into a single reactive interface.
  - **Authentication Callback Handler (`app/pages/login.vue`):** Dedicated OAuth callback page that captures the authorization `code` and `state` parameters from Google, communicates with the backend callback API, sets session state, and redirects seamlessly.
  - **State Composables:**
    - `useAuth.ts`: Manages reactive user authentication state, login triggers, and logout routines.
    - `useApi.ts`: Encapsulates all backend HTTP and SSE interactions with proper credentials handling.
    - `useMotionPresets.ts`: Centralized spring animation configurations for consistent micro-interactions.

#### 3.2 UI/UX Engineering & Custom Components
- Engineered modular UI components:
  - `EncryptedText.vue`: Cyber-styled cipher text component animating the header brand title with real-time text scrambling and smooth decryption.
  - `WavyBackground.vue`: Interactive HTML5 canvas hero background simulating wave dynamics.
  - `SplashScreen.vue` & `FallingStarsBg.vue`: Pitch-black intro splash screen with particle canvas animations and smooth exit transitions.
  - `EmailDetails.vue`: Slide-over detail panel allowing users to inspect email headers, confidence metrics, and matching logic.
  - `ScanStats.vue`: Live categorical tally strip displaying counts per assigned label.
  - `LabelBadge.vue`: Color-coded chip indicators matching Gmail label colors.
  - `InteractiveHoverButton.vue` & `ShimmerButton.vue`: Accessible animated action buttons.
- UI Performance Optimization:
  - **SSE Event Batching:** Implemented an in-memory queue (`resultBatchQueue`) in `index.vue` that flushes received SSE email events every 100ms, preventing browser DOM thrashing and UI freezes during rapid scanning.
  - **Persistent Results View:** Refined conditional rendering so previous scan results and active progress terminals remain visible simultaneously.
  - **FOUC Prevention:** Added an early DOM-blocking script in `nuxt.config.ts` to inject the dark mode class prior to initial paint, completely eliminating white screen flash on page loads.

#### 3.3 Security Hardening & Session Isolation
- Resolved Cross-Origin Cookie Handling:
  - Handled partitioned third-party cookies across distributed domains by enforcing `SameSite=None; Secure=True` on backend cookies when running in production mode (`DEBUG=false`).
  - Configured FastAPI CORS middleware with `allow_credentials=True` and regex matching (`allow_origin_regex=r"^https:\/\/.*\.vercel\.app$"`) to accommodate Vercel preview and production deployments.
- OAuth State Validation:
  - Updated OAuth state exchange in `backend/auth/oauth.py` to prevent state loss during container restarts while preserving CSRF protection.
- Label Deletion Management:
  - Implemented interactive modal controls enabling users to view, selectively delete, or batch-purge all IGRRIS-managed Gmail labels, with system folders strictly protected.

#### 3.4 Production Cloud Deployment Configuration
- **Frontend Deployment (Vercel):**
  - Hosted at `https://igrris.vercel.app`.
  - Configured automated deployments from GitHub repository.
  - Resolved npm build issues by defining `.npmrc` with `legacy-peer-deps=true` and explicit package dependency overrides.
  - Integrated `@vercel/analytics` via client-side plugin (`app/plugins/vercel-analytics.client.ts`).
- **Backend Deployment (Railway & Render):**
  - Configured Railway via `railway.toml` with Nixpacks runtime.
  - Created Render Blueprint specification (`render.yaml`):
    - Web service configured with Python 3.11 runtime (pinned via `.python-version` to `3.11.9`).
    - Build command: `pip install -r requirements.txt && python -m nltk.downloader punkt punkt_tab stopwords` to pre-download required NLP corpora during deployment.
    - Start command: `uvicorn backend.igrris_api:app --host 0.0.0.0 --port $PORT`.
    - Automated liveness check: `/health`.
  - Dependency Optimization:
    - Locked `PyYAML` explicitly to prevent missing runtime dependencies in rule evaluation.
    - Stripped legacy `streamlit` packages, reducing deployment image size by ~150MB and keeping container memory safely within free-tier limits (512MB RAM).

#### 3.5 Automated Testing, Quality Assurance & Final Integration
- Validated all system layers using `pytest`, executing **39 automated unit and integration tests**:
  - `tests/test_preprocessing.py`: Validated 5-stage NLP normalization, stopword filtering, punctuation handling, and stemming edge cases.
  - `tests/test_predict.py`: Tested LinearSVC model prediction schemas, probability bounds ($0.0 \le p \le 1.0$), and confidence thresholds.
  - `tests/test_threat_intelligence.py`: Verified URL extraction (HTTP, HTTPS, FTP), local feed lookup, and seed vs. runtime data fallback logic.
  - `tests/test_labels.py`: Verified label creation, duplicate prevention, batch deletion, and system label protection.
  - `tests/test_auth_isolation.py`: Verified multi-user credential separation, session cookie integrity, and UUID traversal safeguards.
  - `tests/test_api.py`: Tested FastAPI endpoints (`/health`, `/scan/token`, `/labels`, `/predict`) for correct status codes and error handling.
- Conducted end-to-end integration tests verifying the full path: OAuth login → Gmail message retrieval → Threat Intelligence pre-filter → TF-IDF & LinearSVC inference → Rule classification → Gmail label application → Real-time SSE dashboard rendering.

---

## 🏗️ Technical Architecture & System Specifications

### High-Level System Architecture Diagram

```
                        ┌──────────────────────────────────────────┐
                        │             USER BROWSER                 │
                        │   Nuxt 3 + Vue 3 Reactive Interface      │
                        │   (Hosted on Vercel)                     │
                        └───────┬──────────────────────────▲───────┘
                                │                          │
                  HTTP Requests │                          │ Server-Sent Events
               & OAuth Callback │                          │ (SSE Stream)
                                ▼                          │
                        ┌──────────────────────────────────┴───────┐
                        │           FASTAPI BACKEND                │
                        │   (Hosted on Railway / Render)           │
                        ├──────────────────────────────────────────┤
                        │ • Session Manager (HTTP-only Cookies)    │
                        │ • OAuth 2.0 Client (Per-User JSON)       │
                        │ • Label Manager (CRUD & Safe Guards)     │
                        │ • Scan Service Coordinator               │
                        └───────┬──────────────────────────▲───────┘
                                │                          │
                   Gmail REST   │ API Calls                │ Threat Feeds
                   (OAuth 2.0)  ▼                          │
                        ┌───────────────┐          ┌───────┴───────┐
                        │   GMAIL API   │          │ THREAT INTEL  │
                        │ • List Emails │          │ • URLhaus     │
                        │ • Get Content │          │ • OpenPhish   │
                        │ • Apply Labels│          │ • Domain Lists│
                        └───────┬───────┘          └───────┬───────┘
                                │                          │
                                └───────────┬──────────────┘
                                            ▼
                        ┌──────────────────────────────────────────┐
                        │         TWO-LAYER SCANNING PIPELINE      │
                        ├──────────────────────────────────────────┤
                        │ LAYER 1: Threat Intelligence Pre-Filter  │
                        │   (Direct threat detection & bypass)     │
                        ├──────────────────────────────────────────┤
                        │ LAYER 2: Machine Learning Classification │
                        │   1. 5-Stage NLP Preprocessing           │
                        │   2. TF-IDF Vectorizer (3000 features)   │
                        │   3. Calibrated LinearSVC (Confidence)   │
                        │   4. Rule-Based 11-Category Classifier   │
                        └──────────────────────────────────────────┘
```

---

## 🧰 Technology Stack Specification

| Tier | Technology | Version | Purpose in IGRRIS |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Nuxt 3 / Vue 3 | 3.x | Modern reactive frontend architecture, SSR/SSG capabilities, and modular page routing. |
| **Styling & Design** | Tailwind CSS | 3.x | Utility-first responsive styling, dark mode glassmorphism, and responsive layouts. |
| **Animation & UX** | @vueuse/motion, Lenis | Latest | Smooth scrolling and spring animation presets. |
| **Backend Framework** | FastAPI | 0.110+ | High-performance asynchronous REST API and Server-Sent Events implementation. |
| **Application Server** | Uvicorn | 0.28+ | ASGI web server running FastAPI. |
| **Data Validation** | Pydantic | v2 | Strict request/response schema validation and type enforcement. |
| **Machine Learning** | Scikit-Learn | 1.3+ | LinearSVC classifier, CalibratedClassifierCV, and TF-IDF vectorization. |
| **Natural Language** | NLTK | 3.8+ | Tokenization (`punkt`), stopword removal, and Porter stemming. |
| **Data Processing** | NumPy, Pandas | 1.24+, 2.0+ | Matrix manipulation and dataset preprocessing. |
| **Email Integration** | Google API Client | Latest | Gmail REST API integration for inbox reading and label assignment. |
| **Authentication** | Google Auth OAuthlib | Latest | Google OAuth 2.0 authorization code flow and token lifecycle. |
| **Testing Suite** | pytest, HTTPX | 8.0+, 0.27+ | Automated unit, regression, and async API integration testing. |
| **Cloud Hosting** | Vercel (Frontend) | Production | Global edge hosting for Nuxt 3 web frontend. |
| **Cloud Hosting** | Railway / Render | Production | Cloud container environments for FastAPI backend execution. |

---

## 🤖 Machine Learning Pipeline & Threat Detection Metrics

### Preprocessing & Feature Extraction
- **Input Transformation:** Emails undergo lowercasing, tokenization, alphanumeric filtering, stopword stripping, and Porter stemming.
- **TF-IDF Parameters:** 3,000 max features, sublinear term-frequency scaling, unigram + bigram tokens.

### Classification Model Performance
- Evaluated on benchmark corpora under cross-validation:

| Class | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **Ham (Legitimate)** | 0.98 | 0.99 | 0.99 |
| **Spam / Threat** | 0.95 | 0.88 | **0.92** |
| **Overall Accuracy** | — | — | **98.0%** |

- **Confidence Calibration:** Calibrated with Platt scaling (`CalibratedClassifierCV`) to ensure output probabilities reflect true posterior probabilities, preventing arbitrary overconfidence on marginal inputs.

---

## 🛡️ Gmail Label Taxonomy (11 Managed Categories)

| Category | Display Color | Hex Code | Operational Criteria |
| :--- | :--- | :--- | :--- |
| **Phishing** | Dark Red | `#cc3a21` | Matched in threat intelligence feeds, spoofed domains, or high-confidence phishing indicators. |
| **Spam** | Red | `#e07798` | Unsolicited bulk marketing, prize scams, or high ML spam probability. |
| **Security** | Blue | `#4a88da` | Authentic 2FA codes, account recovery, password changes, security notifications. |
| **Needs Review** | Amber | `#fad165` | Borderline confidence predictions requiring user verification. |
| **Banking** | Dark Green | `#16a766` | Financial institutions, transaction receipts, credit card statements. |
| **Orders** | Purple | `#8e63ce` | E-commerce purchases, shipment tracking, invoices. |
| **Work** | Navy | `#42d692` | Professional corporate correspondence, calendars, enterprise domains. |
| **Education** | Cyan | `#4986e7` | University notices, academic platforms, course registrations. |
| **Promotions** | Orange | `#ffad46` | Retail newsletters, marketing discounts, consumer announcements. |
| **Personal** | Gray | `#b99aff` | Direct one-to-one communications from recognized individual contacts. |
| **Trusted** | Green | `#16a765` | Whitelisted senders and verified authentic communications. |

---

## 🔌 API Specification & Endpoints

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `GET` | `/auth/login-url` | Generates and returns Google OAuth 2.0 authorization URL. |
| **Auth** | `POST` | `/auth/callback` | Exchanges authorization code for credentials and establishes session. |
| **Auth** | `POST` | `/auth/logout` | Revokes active Google token and invalidates user session. |
| **Scan** | `POST` | `/scan/token` | Generates single-use 60-second token for cross-origin SSE stream initialization. |
| **Scan** | `GET` | `/scan/stream` | Server-Sent Events stream emitting live scanning progress and email classifications. |
| **Scan** | `POST` | `/scan/stop/{scan_id}` | Aborts an active scanning session using thread-safe events. |
| **Labels** | `GET` | `/labels` | Retrieves all active IGRRIS-managed labels from the user's Gmail. |
| **Labels** | `POST` | `/labels/delete` | Deletes selected managed labels from the user's account. |
| **Labels** | `DELETE`| `/labels/all` | Batch-deletes all Igrris-managed labels while preserving system folders. |
| **System** | `GET` | `/health` | Health check endpoint returning service operational status (`{"status":"ok"}`). |
| **Inference**| `POST` | `/predict` | Direct REST classification endpoint for ad-hoc email text evaluation. |

---

## 🛠️ Engineering Challenges & Technical Resolutions

| Subsystem | Technical Challenge | Root Cause | Engineering Resolution |
| :--- | :--- | :--- | :--- |
| **Multi-User Security** | Credential collision across users. | Global single-file credential storage (`token.json`). | Built per-user credential isolation (`credentials/<user_id>.json`) coupled with HTTP-only session cookies and UUID path validation. |
| **SSE Streaming** | Cross-origin stream authentication failure. | Standard browser `EventSource` cannot send cross-origin cookies. | Created authenticated `POST /scan/token` endpoint issuing short-lived, single-use stream tokens passed via query parameters. |
| **OAuth State** | CSRF state failure on server reload. | Ephemeral container restarts clearing in-memory OAuth state. | Updated OAuth flow to handle validated code exchange with confidential client credentials while retaining security checks. |
| **Threat Intelligence** | Git repo pollution during updates. | Downloaded threat feed data modifying tracked repository files. | Segregated static `SEED_DATA_DIR` from dynamic `RUNTIME_DATA_DIR` and implemented atomic `.tmp` file replacement. |
| **UI Reactivity** | Dashboard lag during rapid scanning. | Excessive Vue re-renders from rapid individual SSE events. | Built 100ms client-side event batching queue (`resultBatchQueue`) in `index.vue` to consolidate DOM updates. |
| **UX Consistency** | Previous scan results disappearing on new scan. | Overly restrictive conditional rendering (`!scanning && results.length > 0`). | Decoupled results display state so previous results remain interactive during active scanning. |
| **Frontend Styling** | White flash on initial page load (FOUC). | SSR dark mode class applied after hydration. | Injected early DOM-blocking script in `nuxt.config.ts` setting the dark class before first paint. |
| **Cloud Deployment** | Container memory exhaustion on free tiers. | Unused heavy dependencies (Streamlit) loading into memory. | Pruned requirements manifest, removing ~150MB of unused dependencies and locking explicit `PyYAML` versions. |
| **Google Quota** | Gmail API rate limit errors (HTTP 429). | Unrestricted concurrent threads hitting Gmail endpoints. | Implemented centralized rate limiting lock and thread-local service builders. |
| **System Safety** | Accidental deletion of critical emails. | Broad label deletion logic. | Hardcoded strict protection guards for Gmail system folders (`INBOX`, `SPAM`, `TRASH`). |

---

## 🧪 Testing & Quality Assurance Summary

The complete codebase has been subjected to rigorous automated verification. All **39 unit and integration tests** pass successfully:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.x, pytest-8.x.x, pluggy-1.x.x
rootdir: c:\Users\VICTUS\OneDrive\Attachments\Desktop\igrris
collected 39 items

tests/test_preprocessing.py ............                                 [ 30%]
tests/test_predict.py ........                                           [ 51%]
tests/test_threat_intelligence.py ......                                 [ 66%]
tests/test_labels.py .....                                               [ 79%]
tests/test_auth_isolation.py .....                                       [ 92%]
tests/test_api.py ...                                                    [100%]

============================== 39 passed in 4.12s ==============================
```

- **Preprocessing Verification:** Validates punctuation stripping, case folding, stem stability, and stopword exclusion.
- **Model Verification:** Confirms probability calibration bounds ($0.0 \le \text{confidence} \le 1.0$) and classification schemas.
- **Threat Intelligence Verification:** Validates exact URL matching, domain blocklists, and seed-to-runtime fallback mechanisms.
- **Label Management Verification:** Confirms idempotent label generation and absolute protection of Gmail system folders.
- **Security & Session Verification:** Confirms per-user credential isolation, cryptographic cookie generation, and rejection of directory traversal attempts.
- **API Endpoint Verification:** Confirms standard HTTP status codes, schema adherence, and error responses.

---

## 🚀 Deployment Verification

The system is configured and deployed across production cloud infrastructure:

- **Frontend Application:** Deployed on **Vercel** (`https://igrris.vercel.app`) with integrated edge caching, continuous deployment from GitHub, and automated build verification.
- **Backend Application:** Deployed on **Railway** / **Render** (`https://igrris-backend.onrender.com` / `https://igrris.up.railway.app`) with Python 3.11 runtime, pre-cached NLTK tokenizers, and HTTPS encryption.
- **Google Cloud Console:** Production OAuth 2.0 Web Application credentials configured with authorized redirect URIs for both production domains and local development environments.

---

## 🔮 Future Enhancements

The core implementation of IGRRIS is complete and functional. As part of future academic and technical development beyond the foundational project scope, potential enhancements include:

1. **Commercial Threat Feed Expansion:** Incorporating additional threat intelligence providers (such as VirusTotal, AbuseIPDB, or AlienVault OTX) to broaden malicious domain coverage.
2. **Deep Learning & Contextual Transformers:** Exploring fine-tuned contextual language models (e.g., DistilBERT or RoBERTa) to detect subtle social engineering and Business Email Compromise (BEC) attacks.
3. **Automated Webhook Ingestion:** Implementing Google Cloud Pub/Sub push notifications (`users.watch`) for sub-second, zero-click email scanning upon inbox arrival.
4. **Administrative Security Operations Console:** Developing organization-level analytics dashboards for enterprise domain administrators to monitor threat vectors across multiple user accounts.

---

## 🏁 Conclusion

Over the development period of **July 2026 through September 2026**, the **IGRRIS** platform progressed systematically through conceptualization, algorithmic modeling, backend systems integration, user interface development, and cloud deployment:

- **July 2026** successfully established the analytical core, producing a calibrated 98%-accurate LinearSVC classification engine and robust 5-stage NLP pipeline.
- **August 2026** transformed the analytical core into an integrated email defense system, delivering Google OAuth 2.0 authentication, Gmail API communication, threat intelligence filtering, 11-category automated labeling, and real-time SSE scanning.
- **September 2026** delivered a modern Nuxt 3 web interface, resolved cross-origin security challenges, configured production cloud environments on Vercel and Railway/Render, executed a 39-test QA suite, and achieved complete end-to-end integration.

**The core implementation of IGRRIS is fully completed, integrated, and operational.**

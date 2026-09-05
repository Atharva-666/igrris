# ⚔️ IGRRIS: AI-Powered Gmail Intelligence & Threat Defense
# Project Progress & Technical Roadmap Report

**Document Reference:** IGRRIS-PR-2026-Q3-01  
**Current Milestone Status:** **25% COMPLETED | 75% REMAINING**  
**Reporting Period:** Phase 1 Completion & Phase 2–5 Planning  
**Target Delivery Date:** Q4 2026  
**Repository:** [Atharva-666/igrris](https://github.com/Atharva-666/igrris)  
**Lead Architecture:** Full-Stack AI & Cybersecurity (FastAPI, Nuxt 3, Scikit-Learn / Transformers, Google Workspace API)

---

## Executive Summary

Email remains the #1 initial infection vector for cyberattacks, accounting for over 90% of malware deliveries, credential harvesting operations, and Business Email Compromise (BEC) fraud. Traditional email security either relies on blunt spam filters that miss sophisticated spear-phishing or on enterprise appliances that are expensive, complex, and invasive.

**Igrris** is an autonomous, full-stack inbox intelligence and threat defense system. It bridges the gap between high-speed threat intelligence, machine learning classification, and native Gmail workflow integration.

```
Overall Project Progress
[██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 25% Complete
├── Completed (25%): Architecture, OAuth 2.0, ML Core, Threat Pre-filter, SSE, Nuxt UI, Deployment
└── Remaining (75%): Transformer Deep Learning, Pub/Sub Webhooks, Auto-Remediation, Multi-Tenancy, Enterprise Hardening
```

This report documents:
1. **The 25% Completed Work:** The core infrastructure, foundational ML models, dual-layer threat engine, Google OAuth session isolation, real-time SSE streaming pipeline, responsive Nuxt 3 interface, and cloud deployments already operational.
2. **The 75% Remaining Roadmap:** A technical blueprint detailing the four upcoming phases—deep learning transformer models, event-driven Google Cloud Pub/Sub inbox defense, automated remediation and threat defanging, enterprise multi-tenancy, cross-provider support (Microsoft 365), and global threat feed orchestration.

---

## High-Level Progress Gauge

| Milestone Stage | Percentage | Focus Area | Status |
|---|:---:|---|:---:|
| **Milestone 1: MVP Core & Pipeline** | **25%** | Architecture, OAuth, TF-IDF + LinearSVC, Threat Pre-filter, SSE Engine, UI, Staging Deploy | **COMPLETED** |
| **Milestone 2: Deep Learning & Threat Engine** | **25%** | Fine-tuned Transformers (BERT/RoBERTa), Header Forensics (SPF/DKIM/DMARC), Link Sandboxing | **PLANNED (Upcoming)** |
| **Milestone 3: Event-Driven Inbox Defense** | **20%** | Google Cloud Pub/Sub Webhooks, Celery/Redis Queue, Auto-Remediation, Defanging, Rule Builder | **PLANNED** |
| **Milestone 4: Enterprise Privacy & Multi-Tenancy** | **15%** | Zero-Knowledge Token Encryption, RBAC, Team Dashboard, Microsoft 365 (MS Graph API) | **PLANNED** |
| **Milestone 5: Production Scale & Analytics** | **15%** | Global Threat Feeds (OTX/VirusTotal), K8s Cluster, PDF Threat Audits, Final Release | **PLANNED** |
| **Total Project Scope** | **100%** | Comprehensive End-to-End Enterprise Inbox Security Platform | — |

---

# SECTION 1: The 25% Completed Work
*(Milestone 1: Architectural Foundations, ML Prototype & Full-Stack MVP)*

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             CURRENT 25% ARCHITECTURE                             │
└──────────────────────────────────────────────────────────────────────────────────┘

    Browser (Nuxt 3 / Vue 3)
         │  1. Initiate OAuth
         ▼
    Google OAuth 2.0 (accounts.google.com)
         │  2. Redirect ?code=...
         ▼
    /login Callback Catcher ──▶ POST /auth/callback (FastAPI Backend)
                                  │
                                  ├─▶ Session Store (igrris_session HTTP-only Cookie)
                                  └─▶ Isolated Credentials Storage (credentials/<uuid>.json)
         ┌────────────────────────┘
         │
    Scan Dashboard (index.vue)
         │  3. POST /scan/token (60s Single-Use Bridge Token)
         │  4. GET /scan/stream?scan_token=... (Server-Sent Events)
         ▼
    FastAPI Scan Service (scan_service.py)
         │
         ├── Layer 1: Threat Intelligence Pre-Filter
         │    ├── Malicious URLhaus Feed & OpenPhish DB
         │    ├── Blacklisted & Disposable Domains
         │    └── Malicious Regex Engine
         │
         ├── Layer 2: Machine Learning Classification
         │    ├── 5-Stage NLP Preprocessing (NLTK Tokenizer + Stemmer)
         │    ├── TF-IDF Vectorizer (3,000 features)
         │    └── LinearSVC + CalibratedClassifierCV (predict_proba)
         │
         └── Gmail API Integration
              ├── Fetch Recent Messages (Batching)
              ├── 11 Color-Coded Managed Labels Creation
              └── Safe Label Deletion / Cleanup API
```

### 1.1 Core System Architecture & Backend Framework
- **Asynchronous FastAPI Engine:** Built a modular Python 3.11+ backend utilizing FastAPI, Uvicorn, and Pydantic v2 for high-throughput request handling and strict data contract validation.
- **Micro-service Separation:** Codebase partitioned into distinct layers:
  - `backend/auth/`: OAuth2 lifecycle, session management, and credential isolation.
  - `backend/services/`: Scan coordination and async streaming.
  - `backend/ai/`: NLP preprocessing, vectorization, and inference interfaces.
  - `backend/threat_intelligence/`: Threat engine, URL extraction, feed updates, and caching.
  - `backend/labels/`: Gmail label CRUD and color assignment logic.
  - `backend/classifier/`: Heuristic rule engine (`rules_config.yaml`).

### 1.2 Enterprise-Grade OAuth 2.0 & Multi-User Session Isolation
- **Secure Authentication Flow:** Integrated Google OAuth 2.0 with confidential client credentials, automated refresh token handling, and clean session revocation.
- **Cryptographic Session Isolation:** Engineered `backend/auth/session.py` with an in-memory session manager issuing cryptographically signed `igrris_session` HTTP-only, `SameSite=None`, `Secure=True` cookies.
- **Credential Segregation:** Eliminated global token risks by isolating each authenticated user's tokens into path-traversal-proof files (`credentials/<user_id>.json`).
- **Cross-Origin SSE Token Bridge:** Implemented single-use, 60-second scan tokens via `POST /scan/token` to bridge browser `EventSource` connections with strict cross-origin cookie policies across separated frontend and backend domains.

### 1.3 Machine Learning Baseline (Layer 2)
- **5-Stage NLP Preprocessing Pipeline (`data_preprocessing.py`):**
  1. *Text Normalization:* Lowercasing and Unicode sanitization.
  2. *Tokenization:* Sentence and word tokenization via NLTK `punkt` and `punkt_tab`.
  3. *Alphanumeric Filtering:* Removal of formatting noise and non-alphanumeric artifacts.
  4. *Stopword Elimination:* Context-preserving stopword removal.
  5. *Stemming:* Porter Stemmer normalization for lexical generalization.
- **Vectorization & Classification Engine:**
  - TF-IDF vectorization with `max_features=3000`, sublinear TF scaling, and n-gram ranges.
  - Trained `LinearSVC` classifier wrapped in `CalibratedClassifierCV` (sigmoid calibration) to compute continuous confidence probabilities (`predict_proba`).
  - Achieved **98% overall accuracy** and **0.92 F1-score on spam** on benchmark evaluations (SMS Spam Collection & custom email validation corpus).

### 1.4 Dual-Layer Threat Intelligence Pre-filter (Layer 1)
- **Deterministic Threat Evaluation:** Developed `backend/threat_intelligence/engine.py` to intercept emails before they reach the ML model.
- **Live Feed Ingestion & Caching:**
  - URL extraction supporting `http://`, `https://`, and `ftp://` schemes.
  - Cache layer (`cache.py`) prioritizing runtime feeds (`RUNTIME_DATA_DIR`) with seamless fallback to static seed data (`SEED_DATA_DIR`).
  - Atomic feed updates via `updater.py` pulling active indicators from URLhaus, OpenPhish, and curated disposable domain registries.

### 1.5 Gmail API Integration & 11-Category Taxonomy
- **Native Gmail Integration:** Direct interaction with the Google Workspace Gmail REST API using `google-api-python-client`.
- **11 Managed Color-Coded Labels:**
  - 🔴 `Phishing` (Dark Red), 🟥 `Spam` (Red), 🔵 `Security` (Blue), 🟡 `Needs Review` (Amber), 🟢 `Banking` (Dark Green), 🟣 `Orders` (Purple), 🔷 `Work` (Navy), 🩵 `Education` (Cyan), 🟠 `Promotions` (Orange), ⬜ `Personal` (Gray), ✅ `Trusted` (Green).
- **Label Management System:** Added API endpoints (`GET /labels`, `POST /labels/delete`, `DELETE /labels/all`) with strict system guards protecting standard Gmail folders (`INBOX`, `SPAM`, `TRASH`).

### 1.6 Real-Time Server-Sent Events (SSE) Streaming
- **Asynchronous Live Telemetry:** Replaced sluggish REST polling with an active SSE pipeline (`GET /scan/stream`).
- **Event Bus:** Emits structured payloads:
  - `start`: Initialization parameters and total message count.
  - `log`: Real-time scan engine status updates.
  - `progress`: Processed count vs total with percentage calculation.
  - `result`: Individual email classification metadata, confidence score, and threat rationale.
  - `done` / `error`: Scan completion summary or gracefully parsed error reports.
- **Graceful Cancellation:** Supported thread-safe live aborts via `POST /scan/stop/{scan_id}`.

### 1.7 Modern Reactive Frontend (Nuxt 3 / Vue 3)
- **Unified Single-Page Experience:** Merged hero landing and scan dashboard into `index.vue` with seamless authentication switching.
- **Visual Polish & Inspira UI:**
  - Brand identity: Custom `EncryptedText.vue` cyber cipher scramble header component and 6-stop high-contrast metallic typography.
  - Dark glassmorphic aesthetic with canvas background effects (`WavyBackground.vue`, `FallingStarsBg.vue`, `SplashScreen.vue`).
  - Zero Flash of Unstyled Content (FOUC) through early DOM head injection.
- **Performance & Mobile Responsiveness:**
  - SSE event batch queue flushing every 100ms to eliminate Vue DOM reactivity thrashing.
  - Responsive layouts down to 360px viewport widths with sticky table controls, touch targets, and slide-over email detail panel (`EmailDetails.vue`).
  - Passed frontend accessibility and SEO checklist standards (`lang="en"`, OpenGraph, Twitter Cards, ARIA modal dialogs).

### 1.8 Staging Deployment & Quality Assurance
- **Full Cloud Staging Pipeline:**
  - Frontend: Deployed on **Vercel** with automated GitHub CI/CD integration.
  - Backend: Production deployment configurations for **Render** (`render.yaml`, Python 3.11.9 pinned, pre-cached NLTK tokenizers) and **Railway** (`railway.toml`).
- **Automated Test Suite:** 39 unit and integration tests (`tests/test_labels.py`, `tests/test_preprocessing.py`, `tests/test_predict.py`, `tests/test_api.py`, `tests/test_threat_intelligence.py`) validating all core paths.

---

## Completed Deliverables Summary (25%)

| Component | Delivered Artifacts | Validation Metric | Status |
|---|---|---|:---:|
| **Architecture & API** | FastAPI core, Pydantic schemas, config modules | Sub-10ms route response | ✅ Complete |
| **Authentication** | Google OAuth 2.0, HTTP-only session cookies, SSE token bridge | Zero CSRF vulnerabilities, session isolation verified | ✅ Complete |
| **ML Engine** | 5-stage NLP pipeline, TF-IDF, Calibrated LinearSVC | 98% accuracy, 0.92 Spam F1-score | ✅ Complete |
| **Threat Intelligence** | URLhaus & OpenPhish parser, atomic updater, cache fallback | 100% block rate on known malicious test URLs | ✅ Complete |
| **Gmail Labeling** | 11 color-coded custom labels, batch cleanup API | Label creation and deletion safely verified | ✅ Complete |
| **Real-Time Stream** | SSE stream (`/scan/stream`), thread-safe scan stop | Zero event drop, 100ms UI batching | ✅ Complete |
| **Frontend UI** | Nuxt 3 application, Inspira animations, mobile layout | 100% responsive (360px+), 0 FOUC | ✅ Complete |
| **Cloud Deployment** | Render blueprint, Railway spec, Vercel frontend | Staging environments operational | ✅ Complete |
| **Testing** | 39 test cases with pytest | 100% test pass rate | ✅ Complete |

---

# SECTION 2: The 75% Remaining Work
*(The Forward Implementation Roadmap: Phases 2 through 5)*

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            TARGET 100% ARCHITECTURE                              │
└──────────────────────────────────────────────────────────────────────────────────┘

    Inbound Mail Traffic
         │
         ├── Path A: Push Trigger (Google Cloud Pub/Sub Webhooks) [NEW]
         │    └─▶ FastAPI Webhook Ingestion Endpoint
         │         └─▶ Redis Message Broker ──▶ Celery Worker Cluster [NEW]
         │
         └── Path B: User-Initiated Scan (Web Dashboard / Extension)
              └─▶ Existing SSE Streaming Engine
                      │
                      ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                 COMPREHENSIVE DEEP INSPECTION PIPELINE                 │
    └───────────────────────────────────────────────────────────────────────┘
         │
         ├── 1. Cryptographic Header Forensics (SPF, DKIM, DMARC) [NEW]
         │    └─▶ Detects domain spoofing, display-name deception, return-path mismatch
         │
         ├── 2. Live Threat Intelligence Ingestion Network [NEW]
         │    └─▶ Multi-feed: AlienVault OTX, VirusTotal, AbuseIPDB, Spamhaus
         │
         ├── 3. Dynamic URL Sandbox & Expansion Engine [NEW]
         │    └─▶ Unshortens redirect chains, inspects DOM, checks domain registration age
         │
         ├── 4. Deep Attachment Threat Scanner [NEW]
         │    └─▶ Hash lookup (SHA-256), macro/script detection, suspicious MIME audit
         │
         ├── 5. Transformer Deep Learning & Intent Classifier [NEW]
         │    └─▶ Fine-Tuned DistilBERT / RoBERTa (Semantic & Psychological Trigger Analysis)
         │         ├─ BEC (Business Email Compromise) / CEO Fraud Detection
         │         ├─ Urgency & Emotional Manipulation Scoring
         │         └─ Multi-Language Classification Support
         │
         └── 6. Autonomous Remediation & Workflow Actions [NEW]
              ├─▶ Gmail API / MS Graph API (Outlook Support)
              ├─▶ Auto-Quarantine & Labeling
              ├─▶ Safe Link Defanging & Inline Warning Banner Injection
              └─▶ Audit Log & Security Telemetry Database (PostgreSQL + TimescaleDB)
```

The remaining 75% of the project transitions Igrris from a functional ML prototype into a **hardened, autonomous, enterprise-grade inbox security platform**. This work is broken down into four strategic phases:

---

## 2.1 Phase 2: Deep Learning Models & Threat Forensics
**Milestone Progress:** 25% → 50% (+25%)  
**Primary Focus:** Upgrading from classical ML to transformer deep learning and adding deep forensics (headers, URLs, attachments).

### A. Transformer-Based NLP Classification Upgrade
While the current TF-IDF + LinearSVC model performs well on obvious spam, modern spear-phishing and Business Email Compromise (BEC) do not use typical "spam keywords." They use polite, urgent, conversational language.
- **Model Architecture Migration:**
  - Transition to a fine-tuned lightweight Transformer: **DistilBERT** or **RoBERTa-base** optimized with ONNX Runtime or TensorRT for low-latency CPU/GPU inference (<30ms).
  - Train on curated security corpora: Enron, SpamAssassin, modern PhishBowl, and synthetic adversarial phishing datasets.
- **Psychological Trigger & BEC Detection:**
  - Implement intent analysis heads to compute an **Urgency & Manipulation Score** (detecting artificial deadlines, gift-card requests, authority impersonation, and wire transfer prompts).
  - Entity matching to detect **Display Name Spoofing** (e.g., sender named "CEO John Doe" sending from `john.doe@free-mail-provider.com`).
- **Multilingual Support:**
  - Incorporate multilingual embeddings (e.g., `XLM-RoBERTa` or `sentence-transformers/paraphrase-multilingual`) to identify phishing across non-English corporate correspondence.

### B. Cryptographic Email Header Forensics Engine
Attackers frequently falsify sender identity. Phase 2 introduces full RFC 5322 header inspection:
- **Authentication Verification:**
  - Extract and evaluate **SPF (Sender Policy Framework)** pass/fail/softfail records.
  - Cryptographic verification of **DKIM (DomainKeys Identified Mail)** signatures.
  - Policy enforcement of **DMARC (Domain-based Message Authentication, Reporting, and Conformance)** alignment.
- **Anomaly Detection:**
  - Flag mismatches between `From:`, `Sender:`, and `Return-Path:` headers.
  - Analyze `Received:` hop timestamps to detect anomalous routing or untrusted mail relays.

### C. Dynamic URL Sandbox & Redirect Chain Crawler
Over 80% of phishing emails conceal the attack payload behind shortened URLs or multi-stage redirects:
- **Recursive Link Expansion:** Crawl shortened URLs (`bit.ly`, `tinyurl`, `t.co`, `ow.ly`) to reveal the final destination hostname.
- **Domain Age & Reputation Analysis:** Query WHOIS / RDAP APIs to determine domain registration age (newly registered domains `< 30 days` receive a high threat penalty).
- **Homoglyph & Punycode Detection:** Detect internationalized domain name (IDN) visual spoofing (e.g., substituting Cyrillic `а` for Latin `a` in `paypal.com`).

### D. Attachment Signature & Heuristic Scanner
- Compute cryptographic hashes (MD5, SHA-256) of all email attachments.
- Query hashes against local threat caches and public malware signature databases.
- Perform static heuristics: detect double extensions (`invoice.pdf.exe`), embedded macro-enabled documents (`.xlsm`, `.docm`), and disguised archive containers (`.iso`, `.vhd`, `.7z`).

---

## 2.2 Phase 3: Event-Driven Autonomous Inbox Defense
**Milestone Progress:** 50% → 70% (+20%)  
**Primary Focus:** Shifting from manual user scans to 24/7 background threat defense with automated remediation.

### A. Google Cloud Pub/Sub Webhook Integration (Zero-Click Defense)
Currently, a scan must be triggered by the user clicking "Scan Gmail". In production, emails must be analyzed the second they land in the inbox:
- **`users.watch` Lifecycle:** Establish persistent push notifications via Google Cloud Pub/Sub topics.
- **Instant Webhook Handler:** A dedicated FastAPI endpoint receives Pub/Sub push messages containing `historyId` updates, fetching and scanning newly arrived messages within 1.5 seconds of inbox receipt.

### B. Distributed Asynchronous Worker Architecture
- **Queue & Broker Stack:** Integrate **Celery** backed by a high-availability **Redis** or **RabbitMQ** cluster.
- **Decoupled Processing:** Ingestion webhooks acknowledge Google Pub/Sub immediately, delegating heavy ML inference and URL crawling to background worker pools.
- **Rate-Limiting & Backoff:** Implement token-bucket rate limiting matching Google Gmail API quotas (250 quota units per user per second) with exponential jitter backoff.

### C. Active Remediation & Email Defanging
Beyond simply applying labels, Igrris will provide automated defense mechanisms:
- **Automated Quarantine:** Automatically move confirmed zero-day phishing emails out of `INBOX` into a protected `[Igrris]/Quarantine` folder, preventing accidental clicks.
- **Inline Security Warning Banners:** Insert prominent HTML warning badges at the top of suspicious emails:
  > `⚠️ Igrris Alert: This email originated outside your organization and failed DMARC authentication. Links have been neutralized.`
- **Safe Link Defanging:** Rewrite raw hyperlink targets inside suspicious emails (e.g., converting `http://malicious.com` to `https://igrris.app/safe-redirect?url=...` or defanging to `hxxp://malicious[.]com`).

### D. User Heuristic Policy & Custom Rules Builder
- Provide a drag-and-drop rule engine UI in the Nuxt frontend:
  - *"If sender domain is not @mycompany.com AND email contains banking keywords → Apply Banking + Flag Needs Review."*
  - *"Always trust senders matching regex `@.*\.edu$`."*
- Dynamic compilation of user rules into the backend classification pipeline.

---

## 2.3 Phase 4: Enterprise Privacy, Multi-Tenancy & Cross-Platform Support
**Milestone Progress:** 70% → 85% (+15%)  
**Primary Focus:** Multi-tenant organization support, zero-knowledge privacy architecture, and expanding to Microsoft 365.

### A. Zero-Knowledge Token Security & Privacy Architecture
- **Envelope Encryption:** User OAuth access and refresh tokens encrypted at rest using **AES-256-GCM** with master keys managed via AWS KMS, Google Cloud KMS, or HashiCorp Vault.
- **Zero Content Persistence Guarantee:** Email bodies and attachments are strictly processed in volatile memory and never written to persistent databases or disks. Only non-reversible metadata hashes are stored for analytics.
- **Compliance Alignment:** Architecture engineered to satisfy SOC-2 Type II confidentiality criteria and GDPR Article 32 (pseudonymization and continuous security).

### B. Multi-Tenant Organization & Team Dashboard
- **Role-Based Access Control (RBAC):** Roles for `SuperAdmin`, `SecurityAnalyst`, and `Employee`.
- **Centralized Security Operations (SecOps) View:**
  - Real-time threat feed visualizer across all corporate inboxes.
  - Ability for SecOps analysts to "remediate across organization" (e.g., if one employee receives a phishing attack, automatically find and neutralize that email across all other employee inboxes).
- **Synchronized Global Whitelist / Blacklist:** Organization-wide domain and IP policies.

### C. Cross-Platform Email Gateway: Microsoft 365 Support
Gmail accounts for ~30% of business email; Microsoft 365 / Outlook accounts for ~60%.
- **Microsoft Graph API Integration:** Implement OAuth 2.0 and webhook subscriptions for Microsoft 365 / Exchange Online.
- **Unified Provider Abstraction Layer:** Create an abstract base client (`EmailProviderClient`) allowing the exact same threat detection pipeline to run seamlessly across both Gmail and Outlook.
- **IMAP / SMTP Fallback Connector:** Optional connector for legacy self-hosted corporate mail servers.

---

## 2.4 Phase 5: Production Scalability, Analytics & Final Delivery
**Milestone Progress:** 85% → 100% (+15%)  
**Primary Focus:** Threat intelligence feeds, analytics, load testing, and capstone launch.

### A. Commercial & Global Threat Feed Aggregation
- Integrate high-volume threat feeds via asynchronous connectors:
  - **AlienVault Open Threat Exchange (OTX)**
  - **VirusTotal API v3**
  - **AbuseIPDB & Spamhaus DBL**
  - **PhishTank Live Database**
- Distributed Redis Bloom filters for O(1) membership lookups of over 10 million known malicious domains and IP addresses.

### B. Interactive Threat Intelligence & SecOps Analytics
- **Executive Security Dashboard:**
  - Interactive attack vector charts (Phishing trends over time, top impersonated brands, top targeted employees).
  - Domain trust score visualizer powered by D3.js / Chart.js.
- **One-Click Audit Reports:** Exportable executive PDF and CSV security summaries for enterprise audit and compliance requirements.

### C. Production Infrastructure, High Availability & Latency Optimization
- **Containerization & Orchestration:** Full Dockerization with production Kubernetes (`k8s`) manifests or AWS ECS deployment.
- **Horizontal Pod Autoscaling (HPA):** Dynamic scaling of worker pods based on incoming webhook traffic spikes.
- **SLA Benchmarks:** Target sub-50ms inference latency and 99.99% uptime.

### D. Comprehensive Adversarial Evaluation & Final Delivery
- **Stress & Adversarial Testing:** Test the model against prompt injection, evasion attacks (zero-font text, obfuscated HTML tables, image-only text with OCR).
- **Public Developer API & SDK:** Release documented REST API endpoints, Python SDK, and TypeScript client.
- **Final Packaging:** Complete user guide, video walkthrough, and capstone/production release.

---

## Work Breakdown Structure (WBS) & Deliverables Matrix

The table below provides a detailed blueprint of the upcoming tasks required to achieve 100% completion:

| Stage | Module ID | Feature / Component | Technical Stack | Est. Effort | Priority | Deliverable Target |
|:---:|:---:|---|---|:---:|:---:|---|
| **Phase 2** (25% → 50%) | `DL-01` | Fine-tuned DistilBERT/RoBERTa Classifier | PyTorch, HuggingFace, ONNX | 3 Weeks | High | Fine-tuned model with >95% BEC detection |
| | `DL-02` | Psychological & Urgency Intent Scorer | Transformers, Attention Weights | 1.5 Weeks | High | Urgency confidence score (0–100) |
| | `DL-03` | Header Forensics (SPF/DKIM/DMARC) | Python `dnspython`, `authres` | 2 Weeks | Critical | Cryptographic sender validation module |
| | `DL-04` | Dynamic URL Expansion & Age Sandbox | `httpx`, `asyncio`, RDAP/WHOIS | 2 Weeks | High | Unshortening & domain age scoring service |
| | `DL-05` | Attachment Hash & Macro Heuristics | `hashlib`, `oletools`, VirusTotal API | 1.5 Weeks | Medium | Attachment risk assessment pipeline |
| **Phase 3** (50% → 70%) | `EV-01` | Google Cloud Pub/Sub Webhook Listener | GCP Pub/Sub, FastAPI | 2.5 Weeks | Critical | Zero-click real-time inbox ingestion |
| | `EV-02` | Distributed Queue & Worker Cluster | Celery, Redis, Docker | 2 Weeks | High | Background job processing (<1.5s latency) |
| | `EV-03` | Automated Quarantine & Safe Defanging | Gmail API, BeautifulSoup4 | 2 Weeks | High | Link neutralization & warning banners |
| | `EV-04` | Custom Rule Builder & Heuristics UI | Vue 3, Pinia, YAML Parser | 1.5 Weeks | Medium | Interactive user policy configuration UI |
| **Phase 4** (70% → 85%) | `ENT-01` | AES-256-GCM Token Envelope Encryption | `cryptography`, Cloud KMS | 2 Weeks | Critical | Zero-knowledge token security architecture |
| | `ENT-02` | Multi-Tenant RBAC & Admin Portal | FastAPI, Nuxt 3, PostgreSQL | 3 Weeks | High | Multi-seat enterprise dashboard & audit logs |
| | `ENT-03` | Microsoft 365 / Outlook (MS Graph API) | MSAL, Microsoft Graph REST API | 3 Weeks | High | Unified multi-provider email gateway |
| **Phase 5** (85% → 100%) | `PRD-01` | Global Feed Aggregation (OTX, AbuseIPDB) | Redis Bloom Filters, Celery Cron | 2 Weeks | High | 10M+ indicator live feed cluster |
| | `PRD-02` | Threat Analytics & PDF Audit Generator | Chart.js, WeasyPrint / ReportLab | 1.5 Weeks | Medium | Downloadable executive threat reports |
| | `PRD-03` | Kubernetes Cluster & Load Optimization | Kubernetes, Helm, Nginx Ingress | 2 Weeks | High | Auto-scaling cluster with 99.99% SLA |
| | `PRD-04` | Adversarial Red-Teaming & Final Release | `pytest`, Locust, Locust load tests | 2 Weeks | Critical | Full system verification & final delivery |

---

## Technical Risk Assessment & Mitigation Matrix

| Identified Risk | Impact | Probability | Mitigation Strategy |
|---|:---:|:---:|---|
| **Google Cloud Pub/Sub Rate Quotas** | High | Medium | Implement Redis-backed token bucket rate limiter with exponential backoff and jitter to stay well under Google Workspace API per-user quotas. |
| **Transformer Latency on Low-Resource Servers** | High | High | Export models to ONNX format with 8-bit integer quantization (INT8), yielding 4x speedup and enabling CPU inference times <30ms without requiring expensive GPUs. |
| **False Positives on Legitimate Marketing Emails** | Medium | High | Maintain strict separation between `Spam/Promotions` and `Phishing`. Only apply high-impact actions (quarantine/defanging) if both cryptographic header checks (DMARC) and ML confidence fail. |
| **Ephemeral Token Loss in Container Restarts** | High | Low | Migrate from in-memory session dictionaries to persistent encrypted PostgreSQL / Redis stores with automated connection pooling. |
| **Adversarial URL Cloaking (Conditional Redirects)** | Medium | Medium | Perform headless browser rendering (Playwright) on suspicious redirect chains to capture final landing page DOMs and screenshots. |

---

## Implementation Schedule & Milestone Milestones

```mermaid
gantt
    title Igrris Project Timeline: 25% Achieved to 100% Completion
    dateFormat  YYYY-MM-DD
    section Completed (25%)
    Phase 1: Foundations, OAuth, ML Core, Nuxt UI :done, p1, 2026-07-01, 2026-09-05
    section Phase 2: Deep Learning (50%)
    Transformer Models (DistilBERT/RoBERTa)        :active, p2_1, 2026-09-08, 2026-09-29
    Cryptographic Header Forensics (SPF/DKIM/DMARC):p2_2, 2026-09-22, 2026-10-06
    Dynamic URL Sandbox & Expansion               :p2_3, 2026-10-01, 2026-10-15
    Attachment Hash & Macro Scanner               :p2_4, 2026-10-10, 2026-10-22
    section Phase 3: Autonomous Defense (70%)
    Google Cloud Pub/Sub Webhooks                 :p3_1, 2026-10-23, 2026-11-06
    Celery + Redis Worker Architecture            :p3_2, 2026-11-01, 2026-11-15
    Auto-Quarantine & Safe Link Defanging         :p3_3, 2026-11-12, 2026-11-26
    Custom Policy & Heuristic Rule Builder        :p3_4, 2026-11-20, 2026-12-02
    section Phase 4: Enterprise & Privacy (85%)
    Zero-Knowledge Envelope Encryption (KMS)      :p4_1, 2026-12-03, 2026-12-16
    Multi-Tenant RBAC & SecOps Dashboard         :p4_2, 2026-12-10, 2026-12-30
    Microsoft 365 / Outlook (Graph API)           :p4_3, 2026-12-20, 2027-01-12
    section Phase 5: Production & Final (100%)
    Global Threat Feeds & Redis Bloom Filters     :p5_1, 2027-01-13, 2027-01-27
    Threat Analytics & PDF Audit Generator        :p5_2, 2027-01-20, 2027-02-03
    Kubernetes Orchestration & Load Testing       :p5_3, 2027-01-28, 2027-02-12
    Adversarial Red-Teaming & Capstone Release    :p5_4, 2027-02-10, 2027-02-25
```

---

## Conclusion

The first **25%** of the Igrris project has successfully established a fully integrated, cloud-deployed, end-to-end working system: Google OAuth 2.0 authentication, dual-layer threat intelligence and machine learning classification, real-time SSE streaming, and a modern Nuxt 3 user interface.

The remaining **75%** represents the transformation of this working prototype into an autonomous, enterprise-grade cybersecurity platform. By executing the outlined phases—integrating transformer-based semantic classification, zero-click Google Cloud Pub/Sub webhooks, active quarantine and link defanging, zero-knowledge encryption, and cross-platform Microsoft 365 support—Igrris will provide state-of-the-art inbox defense against modern cyber threats.

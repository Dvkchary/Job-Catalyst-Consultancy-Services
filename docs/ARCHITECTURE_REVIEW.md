# JobCatalyst AI - Enterprise Architecture Review Report

**Date:** July 1, 2026
**Reviewing Body:** Independent Enterprise Architecture Review Board
**Outcome:** APPROVED WITH REQUIRED CHANGES (Conditional Approval)

---

## Executive Summary
The Review Board has analyzed the complete architecture suite for JobCatalyst AI. While the proposed Modular Monolith running on AWS/Docker provides a solid baseline, the architecture exhibits critical blind spots regarding asynchronous state management, local-to-cloud synchronization for the desktop client, AI cost-control mechanisms, and webhook idempotency.

The board explicitly rejects several naive assumptions in the current design and requires immediate remediation before implementation begins.

---

## 1. Software Requirements

*   **Missing Requirements (I18n/L10n):** The platform targets "international students," yet there is zero mention of Internationalization, localization, or multi-language LLM prompting.
*   **Feature Gaps (Offline Mode):** A "Windows Desktop Installer" is specified, but the SRS fails to define offline capabilities. If the app is online-only, packaging it as a desktop app is just a heavy wrapper.
*   **Business Risks:** No definition of compliance for scraping "Job Search" data (TOS violations, IP blocking).

## 2. System Architecture

*   **Scalability:** The Modular Monolith is acceptable, but tightly coupling the AI Gateway within the core API monolith is a risk. Long-running AI I/O bounds will starve the ASGI/WSGI thread pools for standard CRUD operations.
*   **Extensibility:** The Desktop (Tauri) architecture is dangerously under-specified. Does it run Ollama locally? If so, how are prompt versions and conversation histories synced with the cloud Postgres DB?
*   **Performance:** Relying on Redis for *both* Celery message brokering and Semantic Caching is dangerous. A sudden influx of Celery tasks could evict the semantic cache if memory limits are reached.

## 3. Backend Architecture

*   **Workers:** Using Celery for heavy AI tasks (PDF parsing, LLM calls taking 30s+) is prone to OOM kills and unacknowledged messages. An Event-Driven approach (e.g., AWS SQS or RabbitMQ) with strict dead-letter queues (DLQ) is mandatory for enterprise resilience.
*   **Layering:** The Repository layer is defined, but the "Unit of Work" pattern is missing. How are cross-repository transactions handled when a user registers, creates a profile, and generates an audit log?
*   **Configuration:** No mechanism defined for live configuration reloads (e.g., flipping a feature flag or changing an AI prompt) without restarting the containers.

## 4. Frontend Architecture

*   **State Management:** Next.js App Router heavily leans on React Server Components (RSC). Specifying `Zustand` and `TanStack Query` globally implies a client-heavy SPA architecture. This is a severe architectural conflict. You must strictly delineate RSCs for marketing/dashboards and Client Components for the interactive resume builder.
*   **Code Splitting:** The Resume Builder (pdf.js/docx parsers) will massively bloat the frontend bundle. Lazy loading strategies for these heavy libraries are missing.

## 5. Database

*   **JSONB Constraints:** Storing `structured_data` as JSONB in `resume_versions` without database-level JSON Schema validation guarantees data corruption over time.
*   **Archiving:** Time-based partitioning on `ai_messages` by `created_at` will make querying "Give me all messages for User X" highly inefficient if they span multiple partitions.
*   **Soft Deletes:** Cascading soft deletes are notoriously complex in SQLAlchemy. A `deleted_at` flag on a User does not automatically filter out their Resumes unless every query explicitly includes the join condition.

## 6. REST API

*   **Streaming & Real-Time:** The API spec lists `/ai-chats/{id}/messages` as returning a JSON response but mentions "SSE support." This is vague. Server-Sent Events (SSE) or WebSockets need a strictly defined protocol for token-by-token streaming, error handling mid-stream, and connection drops.
*   **Webhook Endpoints:** Missing entirely. How does Stripe communicate subscription upgrades? Webhooks require signature validation and strict idempotency keys to prevent double-upgrading accounts.
*   **Pagination:** Cursor-based pagination is recommended, but the API spec uses `?page=1&limit=20` (Offset-based), which degrades heavily on large datasets (Jobs table).

## 7. AI Platform

*   **Provider Abstraction:** The "Fallback Strategy" is naive. If OpenAI fails on a complex JSON-schema extraction, falling back to Gemini/Claude might fail if the prompt isn't uniquely tuned for the fallback model's specific instruction-following quirks.
*   **Cost Tracking:** Token counting is asynchronous, which means a malicious actor can spam requests and rack up thousands of dollars before the token tracker blocks them. Hard limits must be evaluated *pre-flight*.
*   **Ollama Integration:** Running Ollama locally via the Windows App while maintaining enterprise state sync introduces split-brain data issues.

## 8. Security

*   **PII Encryption:** AEAD column-level encryption is proposed for PII, but Key Management Service (KMS) rotation strategies are omitted. If a key is compromised, how do you decrypt and re-encrypt 1 million phone numbers without downtime?
*   **File Uploads:** ClamAV inside Celery is an architectural anti-pattern. Large PDFs will choke the worker queue. Virus scanning should be offloaded to an S3 Object Lambda or an event-triggered serverless function.
*   **Compliance:** "Right to Export" is listed, but generating a massive JSON export blocks the API. This must be an async job that emails the user a secure download link.

## 9. DevOps

*   **Blue-Green Deployments:** Expanding and contracting database schemas across Blue-Green deployments requires strict backward and forward compatibility. The docs mention this, but lack an enforcement mechanism (e.g., Prisma Expand/Contract checks or squashing migrations).
*   **Disaster Recovery:** RTO of 1 hour is optimistic for rebuilding a multi-terabyte PostgreSQL database from an S3 `pg_dump`. Point-in-time recovery (PITR) via WAL must be primary, with logical dumps as secondary.

## 10. Testing

*   **Security Tests:** No mention of automated prompt-injection testing (Red Teaming) in the CI/CD pipeline.
*   **UI Testing:** Missing Visual Regression Testing (e.g., Chromatic/Percy). A Tailwind class typo could destroy the Resume Builder layout, which unit tests won't catch.

## 11. UI / UX

*   **User Flows:** The UX spec does not account for AI latency. An ATS analysis might take 15 seconds. The UI must define optimistic updates, skeleton loaders, and background processing notifications.
*   **Accessibility (a11y):** AI-generated text streams (typing effects) break screen readers if not strictly wrapped in `aria-live` regions.

## 12. Commercial Readiness

*   **Billing Synchronization:** If Stripe fails to renew a subscription, there is no defined grace period workflow or webhook retry mechanism in the architecture.
*   **Analytics:** Tracking "Resume Generated" events is fine, but tracking *AI feature drop-off rates* (e.g., user abandoned the mock interview) is missing and critical for product growth.

## 13. Code Generation Readiness

*   **Architecture:** 🟡 Conditional
*   **Database:** 🟡 Needs JSON Schema validation
*   **APIs:** 🔴 Not ready (Missing Webhooks & SSE specs)
*   **UI Specs:** 🟡 Needs latency state definitions
*   **AI Architecture:** 🟡 Needs pre-flight cost limit definitions

---

## 14. Risk Assessment

### Critical Risks
1.  **AI Streaming State Loss:** If an SSE connection drops mid-generation, the user loses the response, but the system still pays for the LLM tokens.
    *   *Mitigation:* Implement resumable generation IDs or flush partial responses to the DB every 10 tokens.
2.  **Stripe Webhook Idempotency:** Missing webhook handlers will result in out-of-sync subscription states.
    *   *Mitigation:* Design a robust `/api/v1/webhooks/stripe` endpoint utilizing Redis for distributed locks on `event_id`.

### High Risks
3.  **Local vs. Cloud Sync (Desktop App):** Split-brain state if the user operates offline/locally and then reconnects.
    *   *Mitigation:* Remove offline Ollama for v1. Make the desktop app an online-only thin client (WebView) first.
4.  **Celery OOM Kills:** PDF parsers (PDF.js/Tika) consume massive RAM.
    *   *Mitigation:* Isolate PDF parsing to a dedicated, high-memory Celery queue with `max_tasks_per_child=1` to prevent memory leaks.

### Medium Risks
5.  **Offset Pagination:** `?page=1000` will cause database table scans.
    *   *Mitigation:* Mandate Keyset/Cursor pagination for Jobs and Audit Logs.

### Low Risks
6.  **Unlocalized Prompts:** AI generates American English by default.
    *   *Mitigation:* Inject user's locale into the system prompt implicitly.

---

## 15. Improvement Plan

**Priority 1: System Stability & Revenue**
1.  Define strictly typed Stripe Webhook endpoints with idempotency.
2.  Replace offset pagination with cursor pagination for all feed APIs.
3.  Design the Server-Sent Events (SSE) protocol for AI streaming, including disconnect recovery.

**Priority 2: Architecture & Data Integrity**
4.  Isolate Redis: Use one Redis cluster for Caching/Rate Limiting and a separate Redis cluster (or RabbitMQ) for Celery.
5.  Add JSON Schema validation constraints to PostgreSQL `structured_data` columns.
6.  Remove "Local Ollama Sync" from the v1 Desktop scope to guarantee cloud-truth state.

**Priority 3: UX & Performance**
7.  Define UI Skeleton and pending states for all AI operations > 2 seconds.
8.  Move file virus scanning out of Celery into AWS Lambda / serverless triggers.

---

## 16. Implementation Readiness Score

| Module | Score (0-100) | Notes |
| :--- | :--- | :--- |
| **Architecture** | 82 | Solid monolith, desktop app strategy flawed. |
| **Backend** | 75 | Needs Event-driven DLQs and UoW pattern. |
| **Frontend** | 80 | RSC vs Client state boundary needs definition. |
| **Database** | 85 | Excellent use of UUIDv7, needs JSON validation. |
| **API** | 70 | Missing webhooks, SSE, and cursor pagination. |
| **Security** | 88 | Strong concepts, but KMS rotation is missing. |
| **DevOps** | 85 | Good overall, CI/CD is standard. |
| **AI** | 78 | Pre-flight cost checks and fallback tuning needed. |
| **Overall Product** | **80** | **Viable, but requires targeted remediation.** |

---

## 17. FINAL DECISION

**B) APPROVED WITH REQUIRED CHANGES**

**Explanation:** The architecture is fundamentally sound for an enterprise SaaS but lacks the operational rigor required for billing consistency (webhooks) and real-time AI UX (streaming states). The local-desktop AI sync feature introduces unacceptable risk for a v1 launch. If the improvement plan is executed—specifically locking down webhooks, SSE, and dropping offline local-LLM sync for v1—the system is cleared for implementation.

---

## 18. IMPLEMENTATION ROADMAP (Post-Remediation)

### Phase 1: Core Foundation & IAM (Weeks 1-3)
*   **Modules:** Database provisioning, Auth API (JWT/Cookies), User Profiles, RBAC middleware.
*   **Complexity:** Medium
*   **Testing Effort:** High (Security bounds)
*   **Deployment:** Setup Docker, CI/CD pipelines, and staging environments.

### Phase 2: Resume Parser & Storage Engine (Weeks 4-6)
*   **Modules:** S3 Uploads, Serverless ClamAV, Celery Queues, Basic Resume CRUD.
*   **Complexity:** High (File handling, async workers)
*   **Testing Effort:** Medium (File edge cases)
*   **Deployment:** S3 Buckets, Redis Broker provisioning.

### Phase 3: Intelligence & AI Gateway (Weeks 7-9)
*   **Modules:** Universal AI Gateway, Prompt Library, SSE Streaming, Token Cost Tracker.
*   **Complexity:** Very High (Streaming stability, fallback logic)
*   **Testing Effort:** High (Mocking LLM latency and failures)
*   **Deployment:** Provider API key integrations, semantic caching layer.

### Phase 4: Job Matching & ATS Engine (Weeks 10-12)
*   **Modules:** Job Scraper/Ingestion, pgvector similarity matching, ATS Scoring API, Cover Letter Generator.
*   **Complexity:** High (Vector DB tuning)
*   **Testing Effort:** Medium (Algorithm relevance)
*   **Deployment:** DB vector extensions enabled.

### Phase 5: Interactive UX & Billing (Weeks 13-15)
*   **Modules:** React Resume Builder UI, Dashboard, Stripe Checkout, Stripe Webhooks, Subscriptions.
*   **Complexity:** High (Complex client state, financial transactions)
*   **Testing Effort:** Very High (Financial dry-runs, UI state recovery)
*   **Deployment:** Stripe live keys, production WAF tuning.

### Phase 6: Final Polish & Desktop Wrapper (Weeks 16-17)
*   **Modules:** Tauri Desktop Wrapper (Online-only), Auto-updater, Telemetry, Audit Logs.
*   **Complexity:** Medium
*   **Testing Effort:** Medium (Cross-platform compilation)
*   **Deployment:** NSIS Installers, Code Signing Certificates (Apple/Windows).

---
**End of Review.**
**Status:** Waiting for authorization to proceed with code generation based on remediated roadmap.

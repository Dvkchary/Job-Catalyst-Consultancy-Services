# Known Issues: Version 1.0.0 (Release Candidate 1)

This document contains the tracked known issues, expected environmental anomalies, and sandbox simulation notes for JobCatalyst AI v1.0.0-rc1.

---

## 1. Development Environment Anomalies

### Benign WebSocket Connection Warning
* **Symptom:** Browser Developer Console displays: `[vite] failed to connect to websocket`.
* **Root Cause:** Hot Module Replacement (HMR) has been disabled in the workspace dev server environment (`DISABLE_HMR=true`) to stabilize incremental builds and avoid interface flickering.
* **Impact:** None. This warning is completely benign and can be safely ignored. Static page updates and core route transitions remain fully functional.

---

## 2. Platform Sandbox & Mock Implementations

### Simulated Infrastructure in Diagnostics Probe (`/health`)
* **Symptom:** The deep system check `/health` shows `database` and `cache` status as `UP` with low latency, even if local physical Postgres or Redis instances are stopped.
* **Root Cause:** By design, to run the application in self-contained sandboxed platforms (such as basic previews), the `/backend/app/core/health.py` utilizes placeholder pings:
  ```python
  db_ok = True  # Simulated ping
  redis_ok = True  # Simulated ping
  ```
* **Impact:** Operational health metrics are simulated for sandbox baseline execution.
* **Resolution/Workaround:** Before full production deploy, these must be swapped to run active SQLAlchemy DB pings (`session.execute(text("SELECT 1"))`) and Redis `client.ping()` requests.

### Local Mock Storage Fallback for Resume Uploads
* **Symptom:** Resume files are saved to container local memory rather than remote AWS S3.
* **Root Cause:** If environment keys `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are not populated, the system automatically redirects file writes to a local temporary fallback directory.
* **Impact:** Uploaded resumes will not persist across container recreations/reboots when running on transient hosting environments without S3 parameters.

---

## 3. Browser Iframe Restrictions

### Standard Alert and Clipboard Action Restrictions
* **Symptom:** Dynamic clipboard copying (e.g., sharing a resume text format) or certain browser modals fail to trigger.
* **Root Cause:** The application is rendered in a sandboxed `<iframe>` layout inside the development preview, which blocks access to high-privileged browser features like `navigator.clipboard` or `window.alert`.
* **Workaround:** Open the application in a dedicated standalone browser window or tab via the external link icon inside the preview header.

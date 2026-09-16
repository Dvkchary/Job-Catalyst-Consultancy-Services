# JobCatalyst AI - Platform Operations & Incident Runbook Manual
## Document Version: 1.0.0-RC1 (Enterprise production Runbook)

Welcome to the **JobCatalyst AI** Operations & Runbook Manual. This document contains active procedures, incident resolution workflows, and architectural runbooks for managing the JobCatalyst AI platform.

---

## 1. System Metrics & Alerts (Prometheus & Grafana)
The built-in monitoring sidecar tracks real-time KPIs. When configuring metric threshold rules, the following alert rules MUST be maintained:

| Alert Name | Metric Query | Condition | Severity | Playbook Reference |
| :--- | :--- | :--- | :--- | :--- |
| **ApiHighLatency** | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | $> 2.0\text{s}$ | **P2 - Major** | Section 3.1 |
| **DatabasePoolSaturation**| `pg_stat_activity_count` / `max_connections` | $> 85\%$ capacity | **P1 - Critical**| Section 3.2 |
| **WorkerBacklogDelay** | `celery_queue_length{queue="ats_scans"}` | $> 250$ jobs | **P3 - Warning** | Section 3.3 |
| **HighErrorRate** | `sum(rate(http_requests_total{status=~"5.."}[5m]))` / `sum(rate(http_requests_total[5m]))` | $> 5\%$ traffic | **P1 - Critical**| Section 3.4 |

---

## 2. Standard Maintenance Runbooks

### Runbook 2.1: Graceful Log Purging & Archiving
If host disks are reaching capacity limits:
```bash
# 1. Check disk utilization profile
df -h
du -sh /var/lib/docker/containers/*

# 2. Trigger docker log rotations manually
logrotate -f /etc/logrotate.d/docker-containers

# 3. Prune dangling build images and stopped container states
docker system prune -f --volumes
```

### Runbook 2.2: Live Schema Evolution Run (Alembic)
To roll out schema changes securely on a live Postgres cluster:
1. Copy the latest generated alembic script into `backend/alembic/versions/`.
2. Execute validation check to ensure database migrations compiles:
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic check
   ```
3. Run schema migration upgrade step:
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

---

## 3. Incident Response Procedures (Level 1 / Level 2 SRE)

### Incident 3.1: API High Latency or Core Service Crash (P1/P2)
* **Symptom**: User actions hang, API response times exceed 2000ms, or Gateway returns HTTP `504 Gateway Timeout`.
* **Diagnostics Flow**:
  1. Inspect container performance metrics:
     ```bash
     docker stats --no-stream
     ```
  2. Locate slow API queries inside backend FastAPI container standard out logs:
     ```bash
     docker logs --tail=200 -f jobcatalyst_prod_backend | grep -i "latency"
     ```
* **Mitigation Protocol**:
  1. Trigger dynamic worker scaling to disperse load:
     ```bash
     docker-compose -f docker-compose.prod.yml up -d --scale backend=4 --no-recreate
     ```
  2. If memory leak is verified, perform immediate rolling container swap:
     ```bash
     docker-compose -f docker-compose.prod.yml restart backend
     ```

### Incident 3.2: PostgreSQL Connection Exhaustion (P1)
* **Symptom**: Backend FastAPI displays: `sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached`.
* **Diagnostics Flow**:
  1. View active transactions and connections in PostgreSQL:
     ```bash
     docker exec -it postgres_db psql -U postgres -d jobcatalyst_prod -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
     ```
* **Mitigation Protocol**:
  1. Kill long-lived, hanging, inactive idle transactions:
     ```bash
     docker exec -it postgres_db psql -U postgres -d jobcatalyst_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND state_change < now() - interval '5 minutes';"
     ```
  2. Temporarily raise max connections parameters in postgres configuration if host system resources allow.

### Incident 3.3: Celery Worker Stalls / Scan Backlog (P3)
* **Symptom**: ATS Scanning or Resume Rewriting status remains as `QUEUED` indefinitely.
* **Diagnostics Flow**:
  1. Verify Celery service is running:
     ```bash
     docker-compose -f docker-compose.prod.yml ps worker
     ```
  2. Probe Redis queue sizes:
     ```bash
     docker exec -it redis redis-cli -a "${REDIS_PASSWORD}" LLEN celery
     ```
* **Mitigation Protocol**:
  1. Send soft-restart signal to Celery workers:
     ```bash
     docker-compose -f docker-compose.prod.yml restart worker
     ```
  2. Scale up worker container count if tasks queue size remains above 200:
     ```bash
     docker-compose -f docker-compose.prod.yml up -d --scale worker=3 --no-recreate
     ```

### Incident 3.4: Third-Party LLM Credentials Fail / Rate Limits Exceeded (P1)
* **Symptom**: AI resume generation returns errors.
* **Diagnostics Flow**:
  1. Check backend container logs for Gemini API response status:
     ```bash
     docker logs jobcatalyst_prod_backend | grep -E "GoogleGenAI|RESOURCE_EXHAUSTED"
     ```
* **Mitigation Protocol**:
  1. Confirm `GEMINI_API_KEY` matches your Google AI Studio console credentials.
  2. Fallback secondary AI engines: If configured, edit `.env` parameters to pivot primary traffic to OpenAI or Anthropic tokens, and run:
     ```bash
     docker-compose -f docker-compose.prod.yml up -d --no-deps backend
     ```

---

## 4. Disaster Recovery & Backup Procedures
Database archives must be verified via recovery tests on a staging machine every 30 days.

### Execution 4.1: Live PostgreSQL Backup Routine
```bash
# Execute the integrated database backup script
./infrastructure/scripts/backup-db.sh
```
This routine checks data integrity, performs an encrypted export, and saves the file to `/backups/db/` with cryptographic signature verification.

### Execution 4.2: Recovery Restore Validation Test
```bash
# Restore on isolated staging network node
./infrastructure/scripts/restore-db.sh /backups/db/jobcatalyst_backup_2026-07-02.sql.gz
```

---

## 5. Security & Ingress Configuration Audit
1. **SSL/TLS Protocol**: Configure Nginx router (`/nginx/conf.d/default.conf`) to permit only TLS v1.2 and TLS v1.3. Disable legacy SSLv3, TLSv1.0, and TLSv1.1 protocols.
2. **Hardened HTTP Response Headers**:
   ```nginx
   add_header X-Frame-Options "DENY" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval';" always;
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
   ```
3. **API Rate Limiting Enforcement**: Confirm that rate-limiting parameters match security targets ($60\text{ requests/min}$ for anonymous routes, $300\text{ requests/min}$ for authenticated API calls).

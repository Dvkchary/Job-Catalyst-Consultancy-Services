# JobCatalyst AI - Platform Troubleshooting Guide
## Document Version: 1.0.0-RC1 (System & DevOps Debugging)

This guide provides step-by-step procedures to triage and resolve issues that may occur on the JobCatalyst AI platform during installation, clustering, runtime, or AI-orchestration.

---

## 1. Quick Triage Commands

Always check system health indicators first:

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Inspect backend server logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Inspect background celery worker logs
docker-compose -f docker-compose.prod.yml logs -f worker
```

---

## 2. Common Issues & Resolutions

### Issue A: "Connection refused to database" or "Postgres is not ready"
* **Symptoms**: Backend crashes on startup, or loops with database driver errors.
* **Root Cause**: PostgreSQL is booting slowly, or credentials do not match the environment parameters.
* **Resolution**:
  1. Verify the exact database credentials in `secrets.env`.
  2. Confirm the database is running: `docker-compose -f docker-compose.prod.yml exec postgres_db pg_isready -U postgres`
  3. Ensure network routing is clear: check that both backend and database share the internal `db_net` network.

### Issue B: "LLM Rate Limits Exceeded" (429 Too Many Requests)
* **Symptoms**: AI operations (Resume Rewrite, Cover Letter generation) fail with error status logs.
* **Root Cause**: The API key (Gemini, OpenAI, or Anthropic) has hit usage quotas or rate limits.
* **Resolution**:
  1. Monitor LLM usage on your provider's console.
  2. Implement backend exponential-backoff retry queues (configured via Celery options).
  3. Rotate keys or request higher tier quotas.

### Issue C: "Stripe Webhook Signatures Fail" (400 Bad Request)
* **Symptoms**: Credit checkout finishes successfully, but billing plans are not updated.
* **Root Cause**: The webhook signing secret (`STRIPE_WEBHOOK_SECRET`) in `secrets.env` is stale or mismatches the Stripe Developer settings.
* **Resolution**:
  1. Pull the fresh webhook signing secret from your Stripe Dashboard under "Webhooks -> jobcatalyst webhook endpoints".
  2. Update the secret in `secrets.env` and run: `docker-compose -f docker-compose.prod.yml restart backend`

### Issue D: Celery Worker Stalling / Queue Backlog
* **Symptoms**: Workflows and scans remain in "PENDING" or "RUNNING" state indefinitely.
* **Root Cause**: Redis broker is full, or celery worker is stalled.
* **Resolution**:
  1. Inspect the Redis broker queue: `docker-compose -f docker-compose.prod.yml exec redis redis-cli -a <REDIS_PASSWORD> LLEN celery`
  2. Restart the worker node: `docker-compose -f docker-compose.prod.yml restart worker`
  3. Increase concurrency parameters (`CELERY_CONCURRENCY`) if system CPU/Memory permit.

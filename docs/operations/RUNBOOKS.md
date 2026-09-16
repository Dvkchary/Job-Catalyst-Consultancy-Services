# Enterprise Runbooks

## 1. Purpose
This document serves as the central directory for JobCatalyst AI Operational Runbooks. Runbooks are step-by-step procedures to resolve specific, known issues or perform complex operational tasks safely.

## 2. General Rules for Executing Runbooks
- **Never guess**: If a runbook step fails or produces unexpected output, STOP. Escalate to a domain expert.
- **Log everything**: Run commands in a shared terminal (like `tmux` or Slack integrations) or copy output into the incident ticket.
- **Dry run**: Where possible, test commands with `--dry-run` or similar flags before executing them in production.

## 3. Incident Runbooks

Detailed steps for these incidents are located in the [Operations Manual](../OPERATIONS_MANUAL.md).

*   **Runbook 3.1: API High Latency / Core Service Crash**
    *   *Scenario*: FastAPI containers are unresponsive or throwing 502/504 errors.
    *   *Action*: Container scaling, memory leak verification, rolling restarts.
*   **Runbook 3.2: PostgreSQL Connection Exhaustion**
    *   *Scenario*: Database connection pool limit reached.
    *   *Action*: Identifying and terminating idle transactions.
*   **Runbook 3.3: Celery Worker Stalls / Scan Backlog**
    *   *Scenario*: Background tasks (e.g., ATS parsing) are queued indefinitely.
    *   *Action*: Redis queue inspection, worker restart, worker scaling.
*   **Runbook 3.4: Third-Party LLM Credentials Fail / Rate Limits Exceeded**
    *   *Scenario*: Gemini API returns `RESOURCE_EXHAUSTED` or authentication errors.
    *   *Action*: Credential verification, failover to secondary AI providers.

## 4. Operational Maintenance Runbooks

*   **Runbook 4.1: Graceful Log Purging & Archiving**
    *   *Scenario*: Production disks are reaching >85% capacity.
    *   *Action*: Docker log rotation, pruning dangling images/volumes. (See [Operations Manual](../OPERATIONS_MANUAL.md#runbook-21-graceful-log-purging--archiving)).
*   **Runbook 4.2: Live Schema Evolution (Alembic)**
    *   *Scenario*: Deploying a new database schema migration without downtime.
    *   *Action*: Pre-deployment validation, execution of `alembic upgrade head`. (See [Operations Manual](../OPERATIONS_MANUAL.md#runbook-22-live-schema-evolution-run-alembic)).

## 5. Security Runbooks

### Runbook 5.1: Compromised API Key Revocation
*   *Scenario*: A third-party API key (e.g., Gemini, Stripe) is leaked or compromised.
*   *Steps*:
    1. Generate a new API key in the respective provider's console.
    2. Update the encrypted secrets in GitHub Actions.
    3. Update the `.env` configuration on the production server.
    4. Perform a rolling restart of the backend containers: `docker-compose -f docker-compose.prod.yml up -d --no-deps backend`.
    5. Revoke/delete the old, compromised key in the provider's console.
    6. Audit logs for the past 7 days to identify any malicious usage.

### Runbook 5.2: Emergency User Account Lockdown
*   *Scenario*: A user account is actively exploiting the system or violating Terms of Service.
*   *Steps*:
    1. Access the Admin Portal or connect to the database directly.
    2. Set `is_active = False` on the target user record:
       `UPDATE users SET is_active = false WHERE email = 'target@example.com';`
    3. Revoke active sessions by deleting their token cache in Redis:
       `docker exec -it redis redis-cli KEYS "*target_user_id*" | xargs docker exec -it redis redis-cli DEL`

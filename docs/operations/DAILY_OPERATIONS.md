# Daily Operations Guide

## 1. Purpose
This document outlines the standard daily operating procedures (SOPs) for the JobCatalyst AI platform. These tasks ensure the platform runs smoothly, issues are caught early, and performance remains optimal.

## 2. Morning Health Check (09:00 UTC)

### 2.1 Dashboard Review
- **Grafana Dashboards**: Review the primary "System Health" and "Business KPIs" dashboards.
- **Error Rates**: Ensure the global 5xx error rate is below 0.1%.
- **Latency**: Verify P99 API latency is under 500ms.
- **AI Gateway**: Check Gemini API success rates and quota usage limits.

### 2.2 Log Triage
- **Sentry / Error Tracking**: Review any new unresolved errors from the past 24 hours.
- **Prioritization**: Create Jira/Linear tickets for any repeated exceptions (more than 10 occurrences).

### 2.3 Queue Inspection
- **Celery / Redis**: Check the background worker queues (`ats_scans`, `resume_generation`, `email_notifications`).
- Verify no queue has a backlog older than 15 minutes.

## 3. Mid-Day Check-in (14:00 UTC)

### 3.1 Resource Utilization
- **Database**: Monitor PostgreSQL connection pool saturation and CPU/Memory usage.
- **Containers**: Check Docker container memory usage to ensure no memory leaks are occurring in the FastAPI backend or Celery workers.
- **Storage**: Verify disk space on logging and database volumes is below 70% capacity.

### 3.2 Customer Support Sync
- Review any escalated technical support tickets (L2/L3).
- Identify any emerging patterns of user complaints (e.g., "AI is failing to parse my resume").

## 4. End-of-Day Review (17:00 UTC)

### 4.1 Backup Verification
- Check the automated backup logs to confirm the daily snapshots (PostgreSQL, Redis) completed successfully and were uploaded to secure cold storage.

### 4.2 Handoff
- Update the Operations Log with any anomalies, minor incidents, or configuration changes made during the day.
- Brief the incoming on-call engineer on any potential watch items.

## 5. Escalation Criteria
If any daily check reveals:
- P99 Latency > 2000ms
- Error Rate > 1%
- Database CPU > 80% for more than 15 minutes
- AI Gateway quota exhausted
**Action:** Immediately transition to Incident Management protocol and page the on-call Site Reliability Engineer (SRE).

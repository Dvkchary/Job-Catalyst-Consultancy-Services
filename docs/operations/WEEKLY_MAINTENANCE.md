# Weekly Maintenance Guide

## 1. Purpose
This document outlines the weekly maintenance procedures for JobCatalyst AI. These tasks are designed to be proactive, focusing on security, performance tuning, and capacity planning.

## 2. Schedule
Maintenance should be performed during the weekly maintenance window: **Sunday 02:00 UTC - 04:00 UTC**.

## 3. Database Maintenance
- **Vacuuming & Analyze**: Ensure PostgreSQL autovacuum is functioning correctly. Manually run `VACUUM ANALYZE` on heavily updated tables (e.g., `user_sessions`, `job_matches`, `tokens`) if bloat is detected.
- **Index Health**: Review slow query logs. Identify any missing indexes or unused indexes and schedule database migrations if necessary.
- **Data Pruning**: Run scripts to soft-delete or archive old, inactive data (e.g., expired password reset tokens, old guest sessions, temporary PDF uploads).

## 4. Security & Patching
- **Dependency Updates (Backend)**: Review Dependabot/Snyk alerts for Python packages. Update non-breaking minor/patch versions.
- **Dependency Updates (Frontend)**: Review npm package updates for React/Vite.
- **Docker Images**: Rebuild base Docker images (e.g., `python:3.13-slim`, `node:20-alpine`) to pull the latest OS-level security patches.
- **Secret Rotation Prep**: Audit expiring API keys (Gemini API, Stripe, SendGrid) and plan rotations if within 30 days of expiry.

## 5. Infrastructure & Capacity
- **Disk Usage Analysis**: Review weekly disk growth trends. If log volumes are growing faster than expected, adjust log retention policies or rotation frequency.
- **Capacity Planning**: Analyze weekly peak traffic. If peak CPU or Memory utilization exceeded 75% on any tier, propose scaling up (vertical) or scaling out (horizontal) for the upcoming week.
- **Redis Cache Flush**: (Optional) If Redis memory is highly fragmented, schedule a rolling restart of the Redis cluster nodes.

## 6. AI Platform Review
- **Prompt Effectiveness**: Review logs of AI responses that resulted in user corrections or poor feedback scores.
- **Cost Analysis**: Review the weekly token usage and cost for the Gemini API. Compare against revenue metrics to ensure unit economics are healthy.

## 7. Review & Reporting
- **Weekly Uptime Report**: Generate the SLA compliance report.
- **Maintenance Log**: Document all actions taken, patches applied, and anomalies discovered during the maintenance window.

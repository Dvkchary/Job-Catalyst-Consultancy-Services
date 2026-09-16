# Incident Management Process

## 1. Purpose
This document defines the process for responding to, mitigating, and learning from service disruptions affecting JobCatalyst AI. The goal is to minimize downtime and prevent recurrence.

## 2. Incident Classification (Severity Levels)

| Severity | Description | Target Response | Target Resolution | Examples |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Core platform is down. Major feature broken for all users. | < 5 mins | < 1 hour | DB Down, AI Gateway rejecting all requests, Login broken. |
| **SEV-2 (Major)** | Core feature degraded. Performance severely impacted. | < 15 mins | < 4 hours | High API latency, ATS parsing failing for 20% of users. |
| **SEV-3 (Minor)** | Non-core feature broken or isolated user impact. | < 1 hour | < 24 hours | Intermittent timeouts, delayed email notifications. |
| **SEV-4 (Low)** | Minor bug, typo, or internal tooling issue. No customer impact. | N/A | Next Sprint | Internal dashboard glitch, incorrect text alignment. |

## 3. Incident Lifecycle

### 3.1 Detection & Alerting
- **Automated**: Prometheus/Grafana triggers an alert via PagerDuty/Slack based on predefined thresholds.
- **Manual**: Customer Support or internal team members escalate an issue via the `#incident-response` Slack channel.

### 3.2 Triage & Declaration
- The On-Call Engineer acknowledges the alert.
- The On-Call Engineer determines the Severity Level.
- If SEV-1 or SEV-2, the engineer declares an incident in Slack using `/incident start`.

### 3.3 Roles & Responsibilities (SEV-1/SEV-2)
- **Incident Commander (IC)**: Leads the response, coordinates resources, makes critical decisions. (Usually the On-Call Engineer, unless escalated).
- **Resolver**: The subject matter expert(s) actively investigating and fixing the issue.
- **Communications Lead**: Updates internal stakeholders and posts public status page updates.

### 3.4 Mitigation & Resolution
- **Priority**: The absolute priority is to stop the bleeding and restore service (Mitigation), NOT to find the perfect root cause fix immediately.
- Use documented Runbooks to attempt known fixes (e.g., scale up workers, restart containers, failover DB).

### 3.5 Post-Incident Activity
- Confirm service is fully restored and stable for at least 30 minutes.
- Resolve the incident in PagerDuty and update the Status Page.

## 4. Post-Mortem (Root Cause Analysis)
- **Requirement**: A blameless post-mortem must be written for every SEV-1 and SEV-2 incident within 48 hours of resolution.
- **Content**:
  - Timeline of events.
  - Root Cause Analysis (5 Whys).
  - What went well / What went wrong.
  - Action items to prevent recurrence (Jira tickets).

## 5. Communication Guidelines
- Be transparent but do not speculate on root causes externally until verified.
- Update the public status page every 30 minutes during a SEV-1 incident.

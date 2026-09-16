# On-Call Procedures

## 1. Purpose
This document establishes the expectations, schedules, and tools for the JobCatalyst AI engineering on-call rotation to ensure 24/7 reliability.

## 2. On-Call Structure
- **Primary On-Call**: First responder. Expected to acknowledge alerts within 5 minutes.
- **Secondary On-Call**: Backup responder. Escalated to if the Primary does not acknowledge within 5 minutes or requests assistance.
- **Rotation Shift**: 7 days (Tuesday 12:00 UTC to Tuesday 12:00 UTC). Handoff occurs during the weekly Engineering Sync.

## 3. Expectations & SLA
- **Acknowledge**: Must acknowledge PagerDuty alerts within 5 minutes.
- **Triage**: Must begin investigating within 10 minutes.
- **Availability**: Must have a reliable internet connection and laptop available at all times during the shift.
- **Sober & Fit**: Must remain fit to operate production systems.

## 4. Tools & Access
Ensure you have active and tested access to the following before your shift begins:
- **PagerDuty**: The app installed on your phone with "Critical Alerts" bypassing Do Not Disturb.
- **Slack**: Access to `#alerts`, `#incident-response`, and `#engineering`.
- **Infrastructure**: SSH keys loaded for production bastion hosts.
- **Observability**: Access to Grafana, Prometheus, and central logging (e.g., ELK/Datadog).
- **Control Plane**: Access to the CI/CD pipeline (GitHub Actions) and cloud provider console (AWS/GCP).

## 5. Shift Handoff Protocol
Every Tuesday, the outgoing and incoming engineers must complete a synchronous handoff:
1. Review any incidents that occurred during the past week.
2. Review any active or silencing alerts.
3. Discuss any ongoing deployments or risky changes planned for the upcoming week.
4. Update the schedule in PagerDuty if overrides are needed.

## 6. Escalation Policy
Do not hesitate to escalate if:
- You are unsure of the system impact of a potential fix.
- The incident spans multiple domains (e.g., both Database and Frontend are failing).
- You are overwhelmed and need a scribe or communications lead.
- **Escalation Path**: Primary -> Secondary -> Engineering Manager -> CTO.

## 7. Compensation / Time Off
- Engineers receive a standard on-call stipend for their week.
- If an engineer is woken up between 00:00 and 06:00 local time for a SEV-1/SEV-2, they are encouraged to take the next morning off to rest.

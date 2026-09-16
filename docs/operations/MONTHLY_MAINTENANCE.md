# Monthly Maintenance Guide

## 1. Purpose
This document outlines the monthly maintenance tasks for JobCatalyst AI. These are comprehensive, deep-dive activities that ensure long-term stability, compliance, and strategic alignment of the infrastructure.

## 2. Schedule
Monthly maintenance is typically performed on the **first Saturday of every month** during the designated low-traffic window (01:00 UTC - 05:00 UTC).

## 3. Disaster Recovery (DR) Drill
- **Backup Restoration Test**: Perform a full restoration of the PostgreSQL database and Redis state from cold storage into an isolated staging environment.
- **Data Integrity Verification**: Run checksums and data validation scripts against the restored database to ensure the backups are not corrupted.
- **Runbook Validation**: Ensure the documented DR runbooks accurately reflect current infrastructure and are executable within the RTO (Recovery Time Objective) of 4 hours.

## 4. Security & Compliance Audit
- **Access Review**: Audit all IAM roles, AWS/GCP access keys, and GitHub repository permissions. Remove access for offboarded employees or unused service accounts.
- **Vulnerability Scanning**: Run a full dynamic application security test (DAST) against the staging environment.
- **Compliance Check**: Verify that data retention policies are being enforced (e.g., hard-deleting user data after 30 days of account deletion to comply with GDPR/CCPA).

## 5. Major Upgrades & Infrastructure
- **Framework Upgrades**: Plan and test upgrades for major framework versions (FastAPI, React, Vite) in the staging environment.
- **Database Engine Updates**: Apply minor version updates to PostgreSQL (e.g., 15.3 to 15.4) following a blue/green deployment strategy.
- **SSL Certificate Renewal**: Verify automatic Let's Encrypt renewals. Manually renew and replace any static enterprise certificates that expire within 45 days.

## 6. Business & Financial Review
- **Infrastructure Cost Audit**: Review cloud billing (Compute, Storage, Network Egress). Identify orphaned resources (unattached volumes, unused elastic IPs) and terminate them.
- **AI Token Economics**: Analyze monthly Gemini API spend vs. Subscription Revenue. Propose rate-limit adjustments or caching optimizations if margins are decreasing.
- **SLA Review**: Review the monthly availability metrics. If the 99.9% SLA was breached, ensure post-mortems and preventative actions are fully implemented.

## 7. Documentation Update
- **Architecture Diagrams**: Update system diagrams if new microservices or infrastructure components were introduced during the month.
- **Runbook Updates**: Refine incident management runbooks based on any incidents that occurred during the month.

# JobCatalyst AI - Commercial Production Administrator Guide
## Document Version: 1.0.0-RC1 (Enterprise & SaaS Deployments)

Welcome to the **JobCatalyst AI** Production Administrator Guide. This document details strategies for configuring, scaling, monitoring, backing up, and securing the JobCatalyst AI platform.

---

## 1. High Availability Clustering
For commercial operations, deploy the container suite in a cluster model (e.g., Kubernetes, AWS ECS, GCP Cloud Run) rather than a single Docker Compose node.

* **FastAPI Gateways**: Scale horizontally to $N \ge 3$ active replicas behind a load balancer (such as Nginx, AWS ALB, or Cloudflare Tunnel).
* **Celery Workers**: Scale the `worker` pods based on task load metrics. Ensure queues like `ats_scans`, `resume_rewriting`, and `email_triggers` are scaled appropriately.
* **Database (PostgreSQL)**: Use managed database services (like GCP Cloud SQL, AWS RDS, or Azure SQL) configured with Multi-AZ replication and auto-failover.
* **Cache & Broker (Redis)**: Deploy a Redis cluster with master-replica replication and sentinel nodes.

---

## 2. Backup and Disaster Recovery

### Database Backup
Automated daily snapshots are configured via `/infrastructure/scripts/backup-db.sh`.
To run a manual database backup:
```bash
./infrastructure/scripts/backup-db.sh
```
This produces a compressed gzip SQL archive in `/backups/db/` with SHA-256 integrity sums.

### Database Restore
To restore from a snapshot:
```bash
./infrastructure/scripts/restore-db.sh /backups/db/jobcatalyst_backup_2026-07-02.sql.gz
```

---

## 3. Monitoring and Observability
The JobCatalyst AI container stack bundles a pre-configured monitoring sidecar consisting of Prometheus and Grafana.

* **Prometheus Dashboard**: Accessible on port `9090`. Monitors system metrics, API request counts, latency histograms, database transaction pools, and queue lengths.
* **Grafana Dashboard**: Accessible on port `3001` (login default: `admin/admin` - MUST be rotated on initial startup). Displays:
  1. API request volumes & response latency (99th percentile).
  2. CPU / Memory utilization of container replicas.
  3. Celery message queue delay.
  4. Database connection pool saturation.

---

## 4. Log Management & Rotation
By default, Docker container logs are output as structured JSON to standard stream channels (`stdout`/`stderr`), making them compatible with cloud aggregators (such as Datadog, AWS CloudWatch, or Google Cloud Logging).

For on-premise installations, log files are rotated automatically by Docker daemon configs:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

---

## 5. Security & Isolation Hardening
1. **Network Segregation**: The database net (`db_net`) and cache net (`cache_net`) are configured as internal-only, preventing direct access from the public internet.
2. **Non-Root Execution**: Both frontend (running as `nginx`) and backend (running as `appuser`) execute with unprivileged user IDs (UID `10001` / `101`), mitigating host-level privilege escalation risks.
3. **SSL Certificates**: Always mount legitimate Let's Encrypt certificates or enterprise CA roots to the Nginx proxy on port `443`.

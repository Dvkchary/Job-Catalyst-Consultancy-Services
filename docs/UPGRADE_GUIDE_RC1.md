# Upgrade Guide: Version 1.0.0 (Release Candidate 1)

This document provides step-by-step instructions for upgrading JobCatalyst AI installations from legacy pre-release builds (v0.x) to **Version 1.0.0-rc1**.

---

## Prerequisites for Upgrade

Before initiating the upgrade sequence, verify your environment meets the minimum standards:
* **Node.js:** v18.0.0 or higher (v20+ recommended)
* **Python:** v3.11 or higher (v3.13 ready)
* **PostgreSQL:** v15 or higher
* **Redis:** v6 or higher

---

## Step 1: Secure Database Backups

Always capture a raw schema and data snapshot of your existing database before applying schema migrations.

```bash
# Capture full backup from standard postgres container
docker exec -t jobcatalyst_postgres_1 pg_dumpall -U postgres > backup_pre_v1.0.0.sql
```

---

## Step 2: Update Package Dependencies

### 1. Frontend Client Package
Clear cached build caches and update dependencies to align with React 19, Tailwind CSS 4, and Motion.

```bash
# Clean lockfiles and build outputs
npm run clean

# Install declared dependencies
npm install
```

### 2. Backend FastAPI Server
Update python environments to the required dependency constraints.

```bash
# Activate virtualenv
source .venv/bin/activate

# Install requirements
pip install --upgrade -r backend/requirements.txt
```

---

## Step 3: Run Database Schema Migrations

The database models have been updated to support MFA setup and user-facing dynamic notification streams. Apply Alembic head revisions.

```bash
# Navigate to backend directory
cd backend

# Execute schema upgrades to latest HEAD migration
alembic upgrade head
```

---

## Step 4: Review Environmental Variables (.env)

Ensure your `.env` configuration contains the new variables required for security validation and AI-routing.

```env
# Ensure secure random secret key is loaded
SECRET_KEY="REPLACE_WITH_A_SECURE_RANDOM_SHA_256_STRING_IN_PROD"

# Security: CORS and Host Validation
TRUSTED_HOSTS="localhost,127.0.0.1,ais-pre-ykpgvovrk4khb2vgpag22k-168359918186.asia-east1.run.app"
ALLOWED_ORIGINS="http://localhost:3000,https://ais-pre-ykpgvovrk4khb2vgpag22k-168359918186.asia-east1.run.app"

# AI Integrations (Required for Career Coach & Resumes Sandbox)
GEMINI_API_KEY="AI_STUDIO_INJECTED_OR_MANUAL_SECRET"
```

---

## Step 5: Build production assets & Run validation

Verify the package compiles with zero warnings or errors.

```bash
# Compile and build production assets
npm run build

# Run TypeScript syntax and typing checks
npm run lint
```

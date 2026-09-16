# Installation Guide: Version 1.0.0 (Release Candidate 1)

This guide provides instructions for deploying **JobCatalyst AI v1.0.0-rc1** on local workstations or hosting infrastructure.

---

## Architecture Overview

JobCatalyst AI is designed as a modular full-stack application:
1. **Frontend Client:** React 19 (TypeScript) single-page application built with Vite, styled with Tailwind CSS, and animated with Motion.
2. **Backend API:** FastAPI (Python) gateway, using Pydantic v2 for data structures, and SQLAlchemy 2.0 (asyncpg) for database routing.
3. **Database Layer:** PostgreSQL for persistent records, and Redis for rate-limiting, background queues, and session caching.

---

## Option A: Docker Compose Deployment (Recommended)

This is the easiest and most robust method. It bootstraps the React client, FastAPI server, PostgreSQL, and Redis in isolated containers.

### 1. Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Docker Compose v2.0+ installed.

### 2. Configuration Setup
Create a `.env` file at the root of the workspace using the template below:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
SECRET_KEY="YOUR_SECRET_KEY_FOR_JWT_HERE"
ENVIRONMENT="production"
```

### 3. Build & Run
Deploy the stack using the production compose configuration:

```bash
# Build images and boot the service stack in detached mode
docker-compose -f docker-compose.prod.yml up --build -d
```

The gateway reverse proxy routes external traffic as follows:
* **React Web App:** `http://localhost:3000`
* **FastAPI Docs:** `http://localhost:8000/docs` (if non-production mode)

---

## Option B: Native Manual Deployment

Use this option if you wish to run the client and server directly on your operating system without containerization.

### 1. Setup Backend (FastAPI)

#### Prerequisites
* Python 3.11+ (Python 3.13 ready)
* PostgreSQL running locally with database `jobcatalyst`.
* Redis running locally on port 6379.

#### Installation Steps
```bash
# 1. Navigate to backend workspace
cd backend

# 2. Establish python virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Apply migrations
alembic upgrade head

# 5. Boot the webserver
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 2. Setup Frontend (React + Vite)

#### Prerequisites
* Node.js v18.0.0 or higher
* npm v9.0.0 or higher

#### Installation Steps
```bash
# 1. Navigate to root folder
cd ..

# 2. Install dependencies
npm install

# 3. Compile and launch development server
npm run dev
```

Your browser will automatically open to: `http://localhost:3000`

---

## Post-Installation Verification

To confirm that the platform is operational:
1. Load the landing page at `http://localhost:3000`.
2. Click **Get Started Free** or **Log In** to test user account screens.
3. Run an active system diagnostics check:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   Verify that `"status": "UP"` is returned.

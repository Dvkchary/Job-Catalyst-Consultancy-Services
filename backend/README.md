# JobCatalyst AI - Backend Core Service (FastAPI)

Welcome to the backend engine of **JobCatalyst AI**, an enterprise-grade SaaS application designed to optimize resume analysis, applicant tracking matching, and AI career counseling.

This repository holds the high-performance, asynchronous FastAPI application that powers all core AI transformations, resume extraction workers, and data ingestion processes.

---

## 🚀 Key Architectural Features
- **FastAPI Application Factory:** Unified configuration setup, secure shutdown lifecycles, and isolated router configurations.
- **Microsecond Request Tracking:** Standardizes distributed correlation IDs (`X-Request-ID`) across standard routing logs.
- **Secure-by-Default Headers:** Applies browser protection standards to prevent Clickjacking, MIME-sniffing, XSS, and caching leaks.
- **Zero-Trust Exception Shields:** Gracefully handles and structures validation, application, and framework errors into unified envelopes, protecting the system from raw stack trace leaks.
- **High-Precision Time-Ordered UUIDv7:** Native implementation of time-sortable database index-friendly primary identifiers.
- **Deep Hardware Diagnostics:** Integrates `psutil` load reporting alongside active PostgreSQL, Redis, and S3 status trackers.

---

## 📁 Repository Directory Structure

The backend follows a clean, decoupled, SOLID-ready modular layout:

```text
/backend
├── README.md                 # Standard operations overview
├── DEVELOPER_GUIDE.md        # Detailed developer setup and guidelines
├── requirements.txt          # Root Python package dependencies list
├── app/
│   ├── __init__.py
│   ├── main.py               # Main factory, bindings, and core probe endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Strongly-typed Pydantic configurations loader
│   │   ├── logging_config.py # Structured JSON and stdout terminal log formatters
│   │   ├── exceptions.py     # Centralized custom business domain exceptions
│   │   ├── error_handlers.py # Standardized exception interceptors and schemas
│   │   ├── health.py         # Detailed system diagnostics and loads aggregator
│   │   └── dependencies.py   # SOLID Mockable Dependency Injection registry
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── standard.py       # Custom request ID tracking and browser security headers
│   └── utils/
│       ├── __init__.py
│       ├── uuid_utils.py     # Time-ordered UUIDv7 and UUIDv4 generation helpers
│       ├── datetime_utils.py # Timezone-aware UTC-enforced timestamp parse/formats
│       └── helpers.py        # standard envelopes, wrappers, and cursor pagination helpers
└── tests/
    ├── conftest.py           # Standard mock environments and test fixtures
    ├── test_config.py        # Configuration validator tests
    ├── test_health.py        # Probe and diagnostics tests
    └── test_middleware.py    # Request ID, security, and exception handler tests
```

---

## 🔧 Getting Started

### 1. Requirements
- Python 3.10 or 3.13
- Virtual Environment (recommended)

### 2. Quick Local Setup
Create your virtual environment and install dependencies:
```bash
# Create environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 3. Running the Server
Launch the application using Uvicorn on local port `8000`:
```bash
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

---

## 🩺 System Endpoints

| Method | Endpoint | Description | Public / Private |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | API Welcome Landing | Public |
| **GET** | `/live` | Liveness Probe (container process alive?) | Public (K8s/Cloud Run) |
| **GET** | `/ready` | Readiness Probe (accepting traffic?) | Public (K8s/Cloud Run) |
| **GET** | `/health` | Deep Diagnostics (CPU, RAM, DB, Redis latency) | Private / Internal |
| **GET** | `/api/v1/version` | Current software build version details | Public |
| **GET** | `/docs` | Interactive Swagger API documentation | Public (Dev/Staging Only) |

---

## 🧪 Running the Test Suite
We utilize `pytest` to execute unified verification sweeps:
```bash
pytest -v
```
To calculate test coverage:
```bash
coverage run -m pytest
coverage report -m
```

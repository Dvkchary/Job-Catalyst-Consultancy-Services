# JobCatalyst AI - Backend Developer & Contribution Guide

This document defines the core standards, operational conventions, and architectural rules to be followed by the engineering team when expanding the backend codebase.

---

## 🏛️ Architecture & SOLID Principles

We adhere strictly to a **decoupled, modular architecture**:
1. **Separation of Concerns:** Business logic belongs exclusively in the **Service Layer**. Handlers and Routers are thin and only map transport requests/responses. Database queries must be encapsulated within the **Repository Layer**.
2. **Dependency Inversion:** Never hardcode or instantiate classes directly within controllers or services. Always declare dependencies using the core dependency injection container (`app.core.dependencies`) and inject them via FastAPI's `Depends()`.
3. **No Mock Infrastructure in Prod:** All connections to databases, caches, and storage must be real. Use dependency overrides ONLY inside automated testing directories (`/tests`).

---

## 📝 Coding & Styling Standards

We enforce strict formatting rules to maintain codebase consistency:
- **Python Version:** Enforced Python 3.10+ / 3.13 ready.
- **Formatting:** Code formatting is automatically verified against `Black` and `Ruff` (Python standard linters).
- **Type Hints:** Standard Python type annotations are **mandatory** on all function signatures, arguments, and return variables.
  * *Incorrect:* `def get_user(user_id):`
  * *Correct:* `def get_user(user_id: uuid.UUID) -> Optional[User]:`

---

## 🕒 Working with Dates & Times

To prevent catastrophic desynchronizations when containers scale across global cloud regions, raw naive timestamps are **strictly prohibited**.
- Always use `app.utils.datetime_utils.get_utc_now()` to acquire the current timestamp.
- All date values sent to databases or serialized to JSON must be timezone-aware UTC.
- When serializing datetimes, use `format_iso` to return compliant ISO 8601 strings terminating with an explicit UTC `Z` indicator.

---

## 🛡️ Exception Handling & Security

### 1. Raising Custom Exceptions
When an action fails, raise one of our standardized custom exceptions from `app.core.exceptions`. Never return raw, error-state dictionary response models directly from services.

*Example:*
```python
# Raise standard NotFound
raise NotFoundException(
    message=f"Resume with ID {resume_id} does not exist.",
    error_code="RESUME_NOT_FOUND",
    details={"resume_id": str(resume_id)}
)
```

The global exception handlers (`app.core.error_handlers`) will automatically catch these, map the proper HTTP status codes, log correlation details, and return a standardized JSON error envelope to the user.

### 2. Guarding Sensitive Data
- **No Raw SQL Concatenation:** Always utilize SQLAlchemy's ORM compiler or parameter bindings to completely mitigate SQL Injection vectors.
- **No Traceback Leaks:** Unhandled exceptions are masked by our exception shield. Never customize error response fields in production to return raw stack traces or internal environment variables to clients.

---

## 🧬 Extending Dependency Injection

To add a new service or repository class, follow this design pattern:

```python
# app/core/dependencies.py

class UserProfileService:
    def __init__(self, repos: RepositoryContainer = Depends(get_repository_container)):
        self.repos = repos

def get_user_profile_service(service: UserProfileService = Depends()) -> UserProfileService:
    """Dependency provider returning the user profile orchestrator."""
    return service
```

Then, inject this provider directly into your router:

```python
# app/api/v1/endpoints/users.py
from app.core.dependencies import get_user_profile_service

@router.get("/me")
async def read_current_user(
    service: UserProfileService = Depends(get_user_profile_service)
):
    user_data = await service.get_my_profile()
    return wrap_success_response(user_data)
```

---

## 🪵 Logging Standards

Our logging formatter tracks transaction contexts asynchronously.
- Always use the standard `logging.getLogger("app.<module>")` constructor.
- Include contextual information inside log messages to help with future debugging.
- High-priority logging (errors, transactions) should pass extra parameters using the custom formatter structure:

```python
logger.error(
    "Failed to communicate with Stripe API gateway",
    extra={"extra_info": {"attempt": 3, "stripe_session": session_id}}
)
```
- In production (`LOG_JSON_FORMAT=True`), this log automatically flattens into a single JSON line, matching:
```json
{"timestamp": "2026-07-02T00:00:00.000Z", "level": "ERROR", "logger": "app.stripe", "message": "Failed to communicate with Stripe API", "correlation_id": "req-98c3-42...", "extra_info": {"attempt": 3, "stripe_session": "sess_123"}}
```

---

## 🔬 Testing Standards

Unit and integration tests reside inside the `/tests` folder.
- Follow the naming pattern `test_*.py` for test files, and `def test_*():` for test cases.
- Use `pytest` to run tests locally:
  ```bash
  pytest -v
  ```
- Guard critical security middlewares and validation models with strict test assertions on headers, response schemas, and exception responses.

# JobCatalyst AI - Authentication & Authorization Specification (Module 4)

This document details the security contracts, credentials hashing protocols, token lifespan properties, and endpoints layout.

---

## 1. Authentication Lifecycle

```
      Signup (POST /register)
                 │
                 ▼
     Status: ACTIVE, Verified: False
                 │
                 ▼
       Click Verification Link (POST /verify-email)
                 │
                 ▼
     Status: ACTIVE, Verified: True
                 │
                 ▼
       Establish Session (POST /login)
                 │
  ┌──────────────┴──────────────┐
  ▼                             ▼
Access Token (15m TTL)      Refresh Token (7d TTL)
  │                             │
  ▼                             ▼
Request Resource Gate      Token Rotation Check (POST /refresh)
                                │
                        ┌───────┴───────┐
                        ▼               ▼
                     Success          Failure / Theft
                        │               │
                 Rotate Tokens      Revoke All Sessions
```

### Refresh Token Rotation (RTR)
To safeguard against token intercept and hijacking in public networks, JobCatalyst AI implements **Refresh Token Rotation (RTR)**:
1. Every successful `/login` registers an active session identifier (`UserSession`).
2. When a client requests `/refresh` using their Refresh Token, the server looks up the active `UserSession` and matches the JTI.
3. If valid: The server rotates the session Refresh Token by issuing a **new token pair** carrying a fresh JTI, invalidating the previous Refresh Token.
4. If invalid / reused: On detecting reuse of a revoked JTI, the server flags **token theft** and instantly **deactivates all active sessions for that account**, forcing full manual re-authentication on all devices.

---

## 2. API Endpoints Contract

All endpoints are mounted under `/api/v1/auth`.

| Method | Route | Auth Required | Payload | Response | Description |
|---|---|---|---|---|---|
| **POST** | `/register` | No | `UserRegister` | `UserOut` | Account registration. Dispatches verification email. |
| **POST** | `/login` | No | `UserLogin` | `TokenResponse` | Authenticates credentials, verifies lockouts, issues token pair. |
| **POST** | `/refresh` | No | `RefreshTokenRequest` | `TokenResponse` | Submits refresh token to rotate session and issue new pair. |
| **POST** | `/logout` | Yes | `RefreshTokenRequest` | Simple message | Terminates current session, blacklist access token JTI. |
| **POST** | `/logout-all` | Yes | None | Simple message | Centralized security logout. Revokes all active user sessions. |
| **POST** | `/forgot-password` | No | `PasswordResetRequest` | Simple message | Initiates password reset sequence. |
| **POST** | `/reset-password` | No | `PasswordResetConfirm` | Simple message | Commits password update after validating token. |
| **POST** | `/verify-email` | No | `VerifyEmailRequest` | Simple message | Validates registration token and activates account. |
| **POST** | `/resend-verification`| No | `PasswordResetRequest` | Simple message | Resends registration link. |
| **GET** | `/me` | Yes | None | `UserOut` | Returns current active user profile. |
| **POST** | `/mfa/setup` | Yes | None | `TOTPSetupResponse` | Generates seed and provisioning URI for Authenticator Apps. |
| **POST** | `/mfa/enable` | Yes | `TOTPVerifyRequest` | Recovery list | Validates code, activates MFA, and issues 8 backup recovery codes. |
| **POST** | `/mfa/disable`| Yes | `TOTPVerifyRequest` | Simple message | Deactivates MFA after validation. |

---

## 3. Rate Limiting & Lockouts

To prevent brute force dictionary attacks:
- **Lockout Threshold**: 5 consecutive failed login attempts locks the user account instantly.
- **Lockout Duration**: Accounts remain in a `LOCKED` status for **15 minutes** before restoring.
- **Access token blacklisting**: Upon logging out, the access token's JTI is saved in the denylist (`TokenRevocation`) for 15 minutes, rendering the token completely useless immediately.

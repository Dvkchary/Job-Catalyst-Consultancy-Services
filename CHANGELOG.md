# Changelog

All notable changes to the **JobCatalyst AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-rc1] - 2026-07-02

### Added
- **Dynamic System Alerts Dashboard**: Integrated user-facing global notification tray to receive alerts on pipeline state shifts and job alerts.
- **Enterprise SaaS Billing Hub**: Built billing state machine with visual plans picker interface, subscription tracking, and local state synchronizations.
- **AI Mock Panel Coach**: Added simulated high-fidelity conversational panel coaching with dynamic scoring criteria.
- **Advanced ATS Sandbox Simulator**: Added real-time resume parser engine checks, file uploads, keyword density analyzers, and modular resume feedback profiles.
- **Dual-Factor Security (TOTP)**: Introduced endpoint validation for TOTP setup and verification with recovery algorithms inside `/auth/mfa/totp`.
- **System Diagnostics Core**: Implemented centralized `/health`, `/live`, and `/ready` probes monitoring active components, system loads (CPU, RAM, disk), and simulated latency checking.

### Changed
- **Frontend Versioning Label**: Bumped Client Platform label from `v0.0.0` to `v1.0.0-rc1` inside `src/App.tsx`.
- **Package Manifest**: Updated root `package.json` build version specification to `1.0.0-rc1` to align with the release candidate schema.
- **FastAPI Routing Assembly**: Structured API gateways inside `/backend/app/main.py` bottom-to-top to ensure proper execution of browser defensive headers and GZip compression rules.

### Optimized
- **Static Analysis & Build Time**: Refactored Vite-bundled CSS assets and disabled Hot Module Replacement (HMR) within preview frames to speed up cold-starts and avoid console-level websocket reconnect overheads.
- **Database Threading Efficiency**: Structured clean, lazy connection pooling thresholds within settings to avoid thread leaks during concurrent stress test suites.

### Fixed
- **Unread Notification Reset bug**: Fixed notification reading behavior where clicking the notifications tray now marks all alerts as read concurrently in local memory.
- **Trusted Host Header Security Vulnerability**: Added structured validation for HTTP Host Headers inside FastAPI gateway via the `TrustedHostMiddleware` filter to block spoofing vectors.

---

## [0.9.0] - 2026-06-15

### Added
- Beta implementation of the central AI pipeline builder.
- Mock resume builder sandbox template engine.
- Dynamic job listings directory with filtering and searching parameters.

### Changed
- Refactored user profiles store to support multi-role RBAC arrays.

---

## [0.1.0] - 2026-05-10
- Initial pre-alpha bootstrap.
- FastAPI core setup and basic React client skeleton.

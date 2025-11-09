# Security Hardening Checklist

## 2025-11 Update Summary
- Added `CSRFMiddleware` enforcing `Origin`/`Referer` validation and CSRF token verification for cookie-authenticated mutations.
- Unified CSRF token management via `get_csrf_protection` and ensured workflow clients (`web-ui/lib/api.ts`) automatically request and attach `X-CSRF-Token` headers.
- Switched auth cookie to `auth_token` with `HttpOnly`, `Secure`, `SameSite=Lax`, and explicit path.
- Introduced `agents/security_audit.py` to persist structured security audit events (login success/failures, logout, registration) at `logs/security_audit.log`.
- Extended `auth_router` to log audit events for registration/login/logout and to share CSRF storage with middleware.

## Operational Guidance
- Monitor `logs/security_audit.log` for suspicious activity (e.g., repeated failed logins, invalid 2FA attempts). Integrate with SIEM if available.
- Ensure application terminates only over HTTPS in production—`auth_token` cookies include `Secure` and CSRF middleware blocks requests lacking valid Origin/Referer.
- Client applications must obtain CSRF tokens via `/api/auth/csrf-token` before emitting state-changing requests. The provided API client already automates this.
- When scaling horizontally, back CSRF token store with a shared cache (Redis, DB). Current in-memory store suffices for single-instance deployments; plan migration before adding replicas.

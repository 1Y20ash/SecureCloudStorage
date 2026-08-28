# Phase 8 — Collaboration, Security & Monitoring

## Implemented controls

- Reuses the existing `AuditLog` as the canonical security-event stream.
- Adds an administrator-only `/security/monitoring` dashboard.
- Adds lightweight in-process sliding-window request limiting.
- Adds stricter authentication request limiting for `/login` POST requests.
- Adds security response headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy.
- Adds HSTS automatically when requests are served over HTTPS.
- Records rate-limit events without storing passwords, request bodies, or document plaintext.
- Adds CI security scanning with Bandit and pip-audit reports.
- Keeps Phase 7 OCR/search and existing case authorization intact.

## Design constraints

The project remains free-resource friendly. The limiter is intentionally dependency-free and works for the current single-process deployment model. A multi-instance production deployment should replace it with a shared store such as Redis before relying on global rate-limit guarantees.

The monitoring dashboard is restricted to administrators and displays metadata only. Existing document encryption, SHA-256 integrity checks, evidence custody, digital signatures, and role-based authorization remain the source of truth for document security.

## Validation

Run locally:

```powershell
alembic upgrade head
python -m compileall -q .
pytest -q
```

CI additionally runs Bandit and pip-audit and stores their reports as workflow artifacts. Scanner findings are currently report-only so the existing application can be hardened incrementally without blocking functional regression testing.

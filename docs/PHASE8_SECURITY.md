# Phase 8 — Collaboration, Security & Monitoring

## Current status

Phase 8 is implemented on a clean branch based on the completed Phase 7 `main` baseline. The security-monitoring module is wired into the Flask application without replacing the Phase 7 encryption, evidence, digital-signature, or OCR/search functionality.

## Implemented controls

- Reuses the existing immutable `AuditLog` as the canonical security-event stream.
- Adds an administrator-only `/security/monitoring` dashboard.
- Adds lightweight in-process sliding-window request limiting.
- Adds stricter authentication request limiting for `/login` POST requests.
- Adds security response headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy.
- Adds HSTS automatically for HTTPS requests.
- Records rate-limit events without storing passwords, request bodies, or document plaintext.
- Keeps existing encryption, authorization, evidence custody, digital signatures and Phase 7 OCR/search as the source of truth.
- Integrates the monitoring registration directly into `app.py` through `register_security_monitoring(app)`.

## Design constraints

The project remains free-resource friendly. The limiter is dependency-free and suitable for the current single-process deployment model. A multi-instance deployment should use a shared store such as Redis before relying on global rate-limit guarantees.

The monitoring dashboard is intended for administrators and displays security metadata rather than document plaintext or credentials.

Security monitoring is defensive telemetry and abuse protection; it does not claim statutory, legal, forensic, or compliance certification merely because these controls are implemented.

## Validation

Run locally before merging:

```powershell
python -m compileall -q .
python -m pytest -q
```

Bandit and pip-audit findings should remain visible in CI. Functional tests remain the blocking quality gate unless a specific security finding is deliberately reviewed and addressed.

## Phase 8 completion criteria

Phase 8 should be considered complete only after:

1. The complete test suite passes.
2. The application compiles cleanly.
3. The security-monitoring route is reachable only by administrators.
4. Security headers are present on application responses.
5. Rate limiting behaves correctly and does not mix clients.
6. Existing Phase 1–7 functionality remains intact.
7. Git history remains phase-isolated and the branch is reviewed before merge.

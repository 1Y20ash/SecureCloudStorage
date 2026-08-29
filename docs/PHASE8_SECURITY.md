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
- Documents the local Tesseract subprocess as an intentional, non-shell execution path with Bandit suppression comments for B404/B603.

## Design constraints

The project remains free-resource friendly. The limiter is intentionally dependency-free and works for the current single-process deployment model. A multi-instance production deployment should replace it with a shared store such as Redis before relying on global rate-limit guarantees.

The monitoring dashboard is restricted to administrators and displays metadata only. Existing document encryption, SHA-256 integrity checks, evidence custody, digital signatures, and role-based authorization remain the source of truth for document security.

OCR remains local: the configured Tesseract executable is resolved on the host, invoked without a shell, and receives a fixed argument structure. Temporary OCR files are isolated in a temporary directory and are removed automatically after processing.

## CI security policy

Bandit and pip-audit are currently **report-only** in CI. Scanner failures do not block the functional test matrix; instead, the generated JSON reports are uploaded as workflow artifacts on every security-job run. This policy is intentional for incremental hardening and is not equivalent to claiming that the repository has zero scanner findings.

The application currently has two legacy Bandit findings in `app.py`: cleanup `except: pass` blocks (B110) and the development-only `app.run(debug=True)` entry point (B201). These are retained as tracked hardening items rather than hidden from the report. The Phase 7 OCR subprocess findings (B404/B603) are explicitly documented and suppressed because execution is local, non-shell, and restricted to the configured Tesseract executable.

## Validation

Run locally:

```powershell
alembic upgrade head
python -m compileall -q .
pytest -q
```

CI additionally runs Bandit and pip-audit and stores their reports as workflow artifacts. Functional regression tests remain blocking, while security scanner findings remain visible for incremental remediation.

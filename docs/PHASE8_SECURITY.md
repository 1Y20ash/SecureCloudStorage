# Phase 8 — Collaboration, Security & Monitoring

## Current scope

Phase 8 is being rebuilt from the current `main` baseline rather than merging the older divergent Phase 8 branch. This preserves the completed Phase 7 history and avoids reintroducing stale changes.

## Security monitoring controls brought forward

- Reuses the existing `AuditLog` as the canonical security-event stream.
- Adds an administrator-only `/security/monitoring` dashboard.
- Adds lightweight in-process sliding-window request limiting.
- Adds stricter authentication request limiting for `/login` POST requests.
- Adds security response headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy.
- Adds HSTS automatically when requests are served over HTTPS.
- Records rate-limit events without storing passwords, request bodies, or document plaintext.
- Keeps existing encryption, authorization, evidence custody, digital signatures and Phase 7 OCR/search as the source of truth.

## Design constraints

The project remains free-resource friendly. The limiter is dependency-free and suitable for the current single-process deployment model. A multi-instance deployment should use a shared store such as Redis before relying on global rate-limit guarantees.

The monitoring dashboard is intended for administrators and displays security metadata rather than document plaintext or credentials.

## Important implementation note

The monitoring module has been added to this clean Phase 8 branch, but application registration is intentionally the next integration step. It must be wired into the current `app.py` without overwriting the completed Phase 7 storage/OCR changes.

## Validation target

Before Phase 8 is finalized, run:

```powershell
python -m compileall -q .
python -m pytest -q
```

The security scanner policy will be finalized after integration. Bandit and pip-audit findings must remain visible rather than being hidden merely to obtain a green report.

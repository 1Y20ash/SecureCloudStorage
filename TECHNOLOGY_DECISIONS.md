# Technology Decisions

## PS 26190 Resource Policy

The project must use only free resources or open-source software. A feature must not create a mandatory paid dependency.

Before adopting any external service, the team must check:
- Current cost and free-tier limits
- Open-source/license status where applicable
- Privacy and data-handling implications
- Whether local execution is possible
- Whether a free fallback exists

If a required service becomes paid, replace it or redesign the feature rather than introducing a paid dependency.

## Current Foundation and Decisions

| Technology | Purpose | Cost / status | Decision |
|---|---|---|---|
| Python + Flask | Backend | Free/open source | Retain |
| Flask-Login | Authentication/session integration | Free/open source | Retain |
| SQLAlchemy / Flask-SQLAlchemy | ORM/database integration | Free/open source | Retain |
| PostgreSQL | Production metadata/application database | Open source; deployment tier must remain free under project policy | Retain where available; local PostgreSQL is fallback |
| SQLite | Local development/test database | Public-domain/free | Retain as local fallback |
| Alembic | Ordered schema migrations | Free/open source | Retain |
| cryptography | Cryptographic primitives | Free/open source | Retain |
| AES-256-GCM | File encryption | Standard cryptographic primitive | Retain |
| PBKDF2-HMAC-SHA256 | Password-based key derivation | Standard cryptographic primitive | Retain |
| Ed25519 | Digital signatures | Standard cryptographic primitive | Retain |
| SHA-256 | Integrity/hash verification | Standard cryptographic primitive | Retain |
| Tesseract | Local OCR | Free/open source | Retain; avoids paid OCR APIs |
| pytest | Automated testing | Free/open source | Retain |
| Git + GitHub | Version control/CI | Git is free/open source; repository/CI usage must remain within available free allowance | Retain |
| GitHub Actions | CI and dependency auditing | Free allowance for this repository; no paid dependency required | Retain |
| Supabase Storage | Encrypted object storage deployment option | Free-tier status must be checked before deployment use | Retain only while compliant with project policy |
| Vercel | Existing web deployment option | Free-tier status/limits must be checked before deployment use | Retain only while compliant with project policy |
| OWASP ZAP | Optional security testing | Free/open source | Optional; no mandatory dependency |

## Privacy Decisions

- OCR is local/open-source rather than a paid external OCR API.
- Sensitive legal/investigation documents are not required for development or testing.
- Development/demo environments use synthetic data only.
- Encryption keys, database credentials, session secrets and backup keys remain environment/deployment secrets and must never be committed.

## Backup Decision

The project implements an encrypted backup container and tested restore path locally. Backup storage itself must not introduce a paid dependency. External object-storage production backups require a deployment-specific export/restore procedure before production recovery is claimed.

## Digital-Signature Decision

Ed25519 was selected because it is a well-established, free/open-source cryptographic implementation available through the existing `cryptography` dependency. The feature provides technical signature generation/verification only and does not assert statutory/legal validity.

## OCR Decision

Tesseract was selected for the implemented OCR foundation because it is free/open source and can run locally. No paid OCR API is required. Production OCR migration and live verification are tracked separately from source-level implementation.

## Data Rule

Real legal documents, real evidence, real personal information, credentials, and confidential case data must not be used in development or demonstration environments unless the team formally establishes an appropriate secure environment and legal authorization.

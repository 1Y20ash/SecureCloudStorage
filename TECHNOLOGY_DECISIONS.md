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

## Current Foundation

| Technology | Purpose | Decision |
|---|---|---|
| Python + Flask | Backend | Retain existing stack |
| SQLAlchemy | ORM | Retain existing stack |
| PostgreSQL / existing database | Metadata and application data | Retain existing architecture where practical |
| AES-256-GCM | File encryption | Retain and protect existing implementation |
| PBKDF2-HMAC-SHA256 | Key derivation | Retain existing implementation |
| Git + GitHub | Version control | Mandatory |

## Preferred Free/Open-Source Additions

Potential additions include pytest for testing, Tesseract/PaddleOCR for OCR, OWASP ZAP for security testing, SHA-256 for integrity verification, and local/open-source solutions for advanced search or AI where feasible.

These are candidates only. Each must be evaluated before implementation.

## Data Rule

Real legal documents, real evidence, real personal information, credentials, and confidential case data must not be used in development or demonstration environments unless the team formally establishes an appropriate secure environment and legal authorization.

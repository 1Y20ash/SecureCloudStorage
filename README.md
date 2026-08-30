# 🔐 SecureCloudStorage — PS-26190 Secure Digital Document Management System

SecureCloudStorage has evolved from a privacy-first encrypted cloud-storage application into a **case-centric Secure Digital Document Management System (DMS)** for legal and investigation-document workflows, developed against **Problem Statement PS 26190**.

> **Educational / demonstration system:** this project demonstrates security, document-management, evidence, integrity, authorization, OCR and cryptographic-signature concepts. It does **not** claim statutory or legal validity, professional security certification, or legal admissibility merely because a feature is implemented.

<p align="center">
  <a href="https://secure-cloud-storage-nine.vercel.app"><strong>🚀 Live Demo</strong></a> ·
  <a href="https://github.com/1Y20ash/SecureCloudStorage"><strong>💻 Source Code</strong></a>
</p>

## Project Status

**PS-26190 implementation:** Phase 0–10 integrated into `main`  
**Latest integration commit:** `0b7f5b2fe1343b7458e26cdaee3ad0b2a313dd9f`  
**Release target:** `v1.1-ps-26190-final`

The final compliance evidence index is maintained in [`docs/PS26190_COMPLIANCE_MATRIX.md`](docs/PS26190_COMPLIANCE_MATRIX.md).

## Core Capabilities

- 🔐 AES-256-GCM encrypted document storage
- 🔑 PBKDF2-HMAC-SHA256 key derivation
- 👥 Deny-by-default role-based access control
- 📁 Case management and case-centric document organization
- 🧾 Audit trail and SHA-256 integrity verification
- 🔄 Document versioning and lifecycle controls
- ⚖️ Evidence records and chain-of-custody tracking
- ✍️ Ed25519 digital-signature prototype and verification
- 🔎 Local Tesseract OCR and metadata/OCR-text search
- 🤝 Case assignment and controlled document sharing
- 🛡️ Security-event monitoring and session/security hardening
- 💾 Encrypted backup and tested restore workflow
- 🧪 Automated regression/security tests and dependency auditing

## PS-26190 Phase Status

| Phase | Capability | Status |
|---|---|---|
| 0 | Baseline & governance | ✅ Complete |
| 1 | Core document & case management | ✅ Complete |
| 2 | RBAC | ✅ Complete |
| 3 | Audit & integrity | ✅ Complete |
| 4 | Lifecycle & versioning | ✅ Complete |
| 5 | Evidence & chain of custody | ✅ Complete |
| 6 | Digital signatures | ✅ Complete |
| 7 | OCR & intelligent search | ⚠️ Implemented; production verification remains deployment-specific |
| 8 | Collaboration & security monitoring | ✅ Core scope complete |
| 9 | Backup, recovery & hardening | ✅ Implemented/tested; deployment restore drill remains deployment-specific |
| 10 | Final testing & PS compliance | ✅ Implemented and CI-validated |

## Security Architecture

### Document encryption

```text
File + encryption password
          ↓
PBKDF2-HMAC-SHA256
600,000 iterations
          ↓
256-bit AES key
          ↓
AES-256-GCM
          ↓
Encrypted object
          ↓
Storage
```

Each encrypted file uses a fresh 16-byte salt and 12-byte nonce. The encrypted representation includes authenticated ciphertext and its authentication tag.

### Authorization

```text
Request
  ↓
Authentication
  ↓
Role capability
  ↓
Case ownership / assignment
  ↓
Document category / permission
  ↓
Allow or deny
```

The server-side authorization layer is the security boundary; hiding a UI control does not grant or revoke permission.

## Evidence & Integrity

Important documents and evidence use SHA-256 integrity metadata. Evidence custody transitions are recorded as ordered events, and custody protections prevent silent alteration of the chain.

## Digital Signatures

The project uses **Ed25519** through the existing open-source `cryptography` dependency. A document hash is signed and the resulting signed record stores signer/timestamp/signature information.

This is a **technical signature-verification prototype**. It must not be presented as a legally recognized/statutory digital signature without the separate legal and regulatory requirements applicable to a real deployment.

## OCR & Search

OCR is designed around local/open-source processing with Tesseract. The original encrypted document is preserved while OCR text is stored separately and bound to the source document with SHA-256. Search supports filename, case, category, officer, date, metadata and OCR text.

Production OCR migration/live verification remains an explicit deployment gate and is not inferred from source code alone.

## Backup & Recovery

Backups cover application data and encrypted document objects. Backup containers are authenticated/encrypted and use a separate backup key. The automated suite verifies a SQLite round trip plus tamper, wrong-key, malformed-container and validation failures.

For deployments using external object storage, a deployment-level restore drill must verify the database and object store together before production recovery is claimed.

## Technology Stack

- **Backend:** Python, Flask, Flask-Login, Flask-SQLAlchemy, SQLAlchemy, Jinja2
- **Cryptography:** `cryptography`, AES-256-GCM, PBKDF2-HMAC-SHA256, Ed25519, SHA-256
- **Frontend:** HTML5, CSS3, JavaScript, Jinja2 templates
- **Database:** PostgreSQL-compatible deployment configuration with SQLite local fallback
- **Migrations:** Alembic
- **OCR:** Tesseract
- **Testing:** pytest
- **CI/security:** GitHub Actions dependency audit and multi-version test workflow
- **Storage/deployment:** encrypted object storage and existing deployment configuration

All project technology decisions are subject to the free/open-source policy documented in `TECHNOLOGY_DECISIONS.md`.

## Repository Structure

```text
SecureCloudStorage/
├── app.py
├── authz.py
├── audit.py
├── audit_hooks.py
├── backup.py
├── config.py
├── digital_signatures.py
├── document_lifecycle.py
├── evidence_management.py
├── integrity.py
├── lifecycle.py
├── crypto/
├── models/
├── migrations/
├── templates/
├── static/
├── tests/
├── docs/
├── .github/workflows/
├── README.md
├── CHANGELOG.md
├── DEVELOPMENT_LOG.md
├── SECURITY.md
└── TECHNOLOGY_DECISIONS.md
```

## Development & Version Control

The project follows the PDP workflow:

```text
Issue
  ↓
Feature / security branch
  ↓
Development
  ↓
Testing
  ↓
Security review
  ↓
Pull request
  ↓
Review / approval gate
  ↓
Merge
  ↓
Tag / release
```

`main` is intended to remain the stable integration branch. PS-26190 work was developed through the dedicated development line and phase-specific branches before final integration.

## Data Privacy Rule

Development and demonstration environments must use **synthetic/dummy data only**, including synthetic FIRs, police reports, witness statements, evidence records, test PDFs/images and fake accounts. Real FIRs, evidence, confidential court documents, credentials or sensitive personal information must not be uploaded to ordinary development/demo environments.

## Free-Resource Rule

The project uses only free/open-source software or genuinely free resources without a mandatory paid dependency for the implemented scope. Before adopting a new external service, cost, license, privacy, local-execution and fallback considerations must be recorded in `TECHNOLOGY_DECISIONS.md`.

## Local Development

```bash
git clone https://github.com/1Y20ash/SecureCloudStorage.git
cd SecureCloudStorage
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure required environment variables locally in `.env` (never commit the file), then run:

```bash
python app.py
```

## Security Notice

This is an educational/project implementation and has not been represented as a professionally audited production security system. Review `SECURITY.md` before deployment or demonstration.

## Documentation

- `docs/PS26190_COMPLIANCE_MATRIX.md` — final PDP compliance/evidence matrix
- `DEVELOPMENT_LOG.md` — phase history and completion boundaries
- `CHANGELOG.md` — project changes
- `SECURITY.md` — security and data-handling policy
- `TECHNOLOGY_DECISIONS.md` — free/open-source technology policy and decisions
- `docs/PHASE10_RBAC_MATRIX.md` — Phase 10 authorization matrix
- `docs/PHASE9_BACKUP_RECOVERY.md` — backup/restore design and testing
- `docs/PHASE6_DIGITAL_SIGNATURES.md` — digital-signature implementation
- `docs/PHASE5_EVIDENCE_CHAIN_OF_CUSTODY.md` — evidence/custody implementation

## Author

### Yash Chitmalwar

Computer Science & Engineering (AI/ML) Student

- GitHub: https://github.com/1Y20ash
- Project: https://github.com/1Y20ash/SecureCloudStorage
- Live Demo: https://secure-cloud-storage-nine.vercel.app

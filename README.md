# 🔐 EVIDENTIA — Secure Digital Document Management System

**EVIDENTIA** is a case-centric Secure Digital Document Management System for legal and investigation-document workflows. It has evolved from an earlier privacy-first encrypted document-storage prototype into a broader platform covering case management, controlled access, document protection, integrity, auditability, evidence custody, digital signatures, OCR/search, security monitoring, and backup/recovery.

> **Educational / demonstration system:** EVIDENTIA demonstrates security, document-management, evidence, integrity, authorization, OCR and cryptographic-signature concepts. It does **not** claim statutory or legal validity, professional security certification, or legal admissibility merely because a feature is implemented.

<p align="center">
  <a href="https://secure-cloud-storage-nine.vercel.app"><strong>🚀 Live Demo</strong></a> ·
  <a href="https://github.com/1Y20ash/SecureCloudStorage"><strong>💻 Source Code</strong></a>
</p>

## Project Status

**Current scope:** Full case-centric secure document-management workflow integrated into `main`  
**Product name:** **EVIDENTIA**  
**Repository name:** `SecureCloudStorage`  
**Deployment:** Vercel production deployment  
**Development approach:** Phase-wise implementation with CI validation and controlled integration

The repository name is retained to preserve the existing GitHub/Vercel integration. **EVIDENTIA is the application's actual product name and should be used in the user-facing product, documentation, presentations, and demonstrations.**

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

## System Workflow

```text
Case Creation
     ↓
Document Management
     ↓
Access Control & Assignment
     ↓
Encryption + Integrity
     ↓
Audit + Versioning
     ↓
Evidence + Chain of Custody
     ↓
Digital Signatures
     ↓
OCR + Search
     ↓
Security Monitoring
     ↓
Backup + Recovery
     ↓
Verified Retrieval
```

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

## Investigation & Evidence Management

EVIDENTIA supports case-centric organization of documents and evidence. Authorized users can work with case assignments, evidence records, custody transitions, document versions, audit events, and controlled sharing.

Important evidence records use SHA-256 integrity metadata. Evidence custody transitions are recorded as ordered events, helping provide a traceable chain of handling.

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

The project follows a controlled PDP workflow:

```text
Requirement
  ↓
Feature / security branch
  ↓
Development
  ↓
Local testing
  ↓
Security review
  ↓
Pull request
  ↓
CI validation
  ↓
Review / approval gate
  ↓
Merge
  ↓
Production deployment
  ↓
Validation
```

`main` is intended to remain the stable integration branch. Feature and security work is developed separately, validated, and then integrated through controlled version management.

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

- `DEVELOPMENT_LOG.md` — development history and completion boundaries
- `CHANGELOG.md` — project changes
- `SECURITY.md` — security and data-handling policy
- `TECHNOLOGY_DECISIONS.md` — free/open-source technology policy and decisions
- `docs/PHASE10_RBAC_MATRIX.md` — authorization matrix
- `docs/PHASE9_BACKUP_RECOVERY.md` — backup/restore design and testing
- `docs/PHASE6_DIGITAL_SIGNATURES.md` — digital-signature implementation
- `docs/PHASE5_EVIDENCE_CHAIN_OF_CUSTODY.md` — evidence/custody implementation

## Project Links

- **Live Demo:** https://secure-cloud-storage-nine.vercel.app
- **Source Code:** https://github.com/1Y20ash/SecureCloudStorage

## Author

### Yash Chitmalwar

Computer Science & Engineering (AI/ML) Student

- GitHub: https://github.com/1Y20ash

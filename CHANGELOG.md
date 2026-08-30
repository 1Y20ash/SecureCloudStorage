# Changelog

All notable changes for the PS-26190 development track are recorded here.

## [v1.1-ps-26190-final]

### Final PS-26190 Compliance Release
- Completed the phase-wise PS-26190 implementation through Phase 10.
- Integrated Phase 10 deny-by-default RBAC hardening into `main`.
- Added the final PS-26190 requirement-to-implementation/test evidence matrix in `docs/PS26190_COMPLIANCE_MATRIX.md`.
- Reconciled project governance, security, backup/recovery, OCR/search, evidence, lifecycle, audit/integrity, and digital-signature documentation with the implemented repository state.
- Verified the latest GitHub Actions test and dependency-audit workflows on the final `main` baseline before release preparation.
- Preserved the distinction between technical digital-signature verification and legally recognized digital signatures.
- Preserved the requirement that sensitive legal/investigation data must not be used in development or demonstration environments.

### Phase 10 — Final Testing & PS Compliance
- Added the PS-26190 RBAC permission matrix.
- Added role, ownership, assignment, specialist-category, Authority, share-bypass, and deny-by-default authorization tests.
- Verified Python 3.10 and 3.12 CI coverage.

### Phase 9 — Backup, Recovery & Deployment Hardening
- Added encrypted backup/restore workflow for application database and encrypted document objects.
- Added SHA-256 integrity verification for backup contents.
- Added restoration, tamper-rejection, wrong-key, malformed-container, and validation tests.
- Documented the remaining deployment-level restore drill requirement for external object storage deployments.

### Phase 8 — Collaboration & Security Monitoring
- Added case assignment, document sharing, permission management, security-event monitoring, and security-focused application hardening documented in the repository.

### Phase 7 — OCR & Intelligent Document Search
- Added local Tesseract OCR processing with no paid OCR API dependency.
- Added OCR persistence and Alembic migration `0010_ocr_documents`.
- Added SHA-256 binding between OCR records and source documents.
- Preserved original encrypted documents while storing extracted OCR text separately.
- Added authenticated search and OCR detail routes with case/document authorization.
- Added filename, case, category, officer, date, and OCR-text search filters.
- Added negative authorization coverage and CI validation across Python 3.10 and 3.12.
- Production migration/live OCR verification remain deployment-specific acceptance gates and are explicitly identified in the compliance matrix.

### Phase 6 — Digital Signatures
- Added Ed25519 signing and verification.
- Added SHA-256 document hashing before signing.
- Added encrypted per-user signing-key storage.
- Added immutable signing identity fields and append-only signed records.
- Added migration `0009_digital_signatures` and signing UI prototype.
- Documented the distinction between technical signature verification and legally recognized digital signatures.

### Phase 5 — Evidence Management & Chain of Custody
- Added investigation evidence records and controlled evidence lifecycle.
- Added custody transfers, receipts, ordered custody-chain retrieval, SHA-256 integrity verification, and append-only custody protections.
- Added migration `0008_evidence_management` and automated coverage.

### Phase 4 — Document Lifecycle & Versioning
- Added document lifecycle controls, version records, chained document hashes, and lifecycle transitions.

### Phase 3 — Audit Trail & Document Integrity
- Added audit logging and document integrity metadata/hash tracking.

### Phase 2 — RBAC & Secure Sharing
- Added user roles, deny-by-default authorization, case assignments, secure sharing, expiry, permission checks, and authorization/security tests.

### Phase 1 — Core DMS & Case Management
- Added case records, Case IDs, document categories, case-document relationships, document metadata, case interfaces, and case-aware upload workflow.
- Preserved the existing AES-256-GCM encrypted-storage flow and legacy encrypted-file access.

### Phase 0 — Baseline & Governance
- Created the dedicated PS-26190 development branch and governance records.
- Added the free-resource policy, security development policy, migration discipline, and secret/data handling rules.

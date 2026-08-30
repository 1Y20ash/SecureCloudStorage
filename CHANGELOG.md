# Changelog

All notable changes for the PS 26190 development track are recorded here.

## [Unreleased]

### Foundation Hardening — PS-26190 Compliance
- Activated Phase 3 Flask integrity and request-audit hooks during application initialization.
- Persisted encrypted-object SHA-256 hashes at upload and document-version creation time.
- Blocked downloads when the stored encrypted object fails integrity verification.
- Audited integrity-blocked download attempts and distinguished failed login events from successful logins.
- Made `X-Forwarded-For` trust explicitly configurable instead of implicit.
- Required an explicit production `SECRET_KEY` and hardened session/remember-me cookie settings.
- Added baseline HTTP security headers without changing the application's visual theme.
- Aligned case-detail management controls with backend authorization so unauthorized users do not see management actions.
- Preserved the password-first Decrypt & Download workflow; GET requests never attempt decryption.
- Added regression tests for Phase 3 hook registration/idempotence and security baseline behavior.

### Phase 7 — OCR & Intelligent Document Search
- Added local Tesseract OCR processing with no paid OCR API dependency.
- Added OCR document persistence and Alembic migration `0010_ocr_documents`.
- Added SHA-256 binding between OCR records and their source documents.
- Preserved original encrypted documents while storing extracted OCR text separately.
- Added authenticated document search and OCR detail routes.
- Added filename, case, category, officer, date, and OCR-text search filters.
- Enforced case-level and document-level authorization for Phase 7 search/OCR access.
- Added negative authorization coverage for inaccessible documents.
- Added Phase 7 CI validation across Python 3.10 and 3.12.

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

### Phase 2B — Role Management & Case Assignment
- Added explicit case assignments for authorized stakeholders.
- Added `0003_case_assignments` Alembic migration.
- Added case assignment uniqueness and assignment actor/timestamp tracking.
- Integrated assigned users into case authorization and dashboard visibility.
- Added case assignment management and removal UI.
- Added Admin user-role management UI with self-demotion protection.
- Added Phase 2B authorization/security tests.
- Added free pytest dependency for the test suite.

### Phase 2A — RBAC Application Integration
- Enforced deny-by-default authorization on case access, case uploads, document downloads, and document deletion.
- Added administrator access to the protected case/document operations.
- Added recipient-aware shared-document access to the dashboard.
- Added explicit download permission and expiry enforcement for shared documents.
- Added secure document sharing and share-revocation routes for case owners/administrators.
- Added future-expiry validation and recipient account validation for shares.

### Phase 2 — RBAC Foundation
- Added user roles with a safe default role.
- Added deny-by-default authorization helpers.
- Added administrator, case-owner, and shared-document authorization primitives.
- Added expiring document shares with view/download/manage permissions.
- Added Alembic migration `0002_rbac_and_sharing`.
- Added Phase 2 RBAC design documentation.

### Phase 1.1 — Database Migration System
- Added Alembic configuration and migration environment.
- Added an initial migration for the current application schema.
- Added safe handling for databases that already contain the Phase 1 tables.
- Removed automatic `db.create_all()` execution from application startup.
- Added Alembic to the free/open-source dependency set.
- Established the rule that future schema changes must use ordered migration revisions.

### Phase 1 — Core DMS & Case Management
- Added case records with unique Case IDs, titles, descriptions, departments, statuses, creators, and timestamps.
- Added case-to-document relationships.
- Added legal and investigation document categories.
- Added document metadata for case association, category, version, and lifecycle status.
- Added case creation and case detail interfaces.
- Updated the dashboard to show cases and case document counts.
- Updated document upload to require a valid case and category.
- Preserved the existing AES-256-GCM encryption and encrypted-storage flow.
- Preserved access to existing legacy encrypted files.

### Phase 0 — Baseline & Governance
- Created dedicated development branch: `feature/ps-26190-dms`.
- Added development log and project governance records.
- Added free-resource technology policy.
- Added security development policy.
- Confirmed the existing `.gitignore` excludes `.env`, virtual environments, caches, instance data, uploads, databases, and editor settings.

### Next
- Finish foundation hardening and regression/security gates.
- Verify Phase 7 production migration and live OCR/search behavior.
- Implement and restoration-test the PDP-required backup workflow.
- Only then advance the project to final PS-26190 compliance testing.

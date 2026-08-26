# Development Log

## PS 26190 — Secure Digital Document Management System

This file records the controlled development of SecureCloudStorage toward Problem Statement 26190.

## Phase 0 — Baseline & Governance

**Status:** Completed

### Baseline
- Existing stable branch: `main`
- PS-26190 development branch: `feature/ps-26190-dms`
- Baseline application: SecureCloudStorage

### Existing Security Foundation
- User authentication and protected file operations
- AES-256-GCM file encryption
- PBKDF2-HMAC-SHA256 key derivation
- Per-file salt and nonce generation
- User-scoped file operations
- Cloud-storage integration

### Phase 0 Rules
1. No direct development on `main`.
2. Use feature/fix/security branches for implementation work.
3. Pull requests are used to record and merge completed work into stable branches; teammate approval is not a blocking requirement for this project workflow.
4. Do not commit secrets, `.env` files, credentials, private keys, real legal documents, or real evidence.
5. Use synthetic/sample data for development and demonstrations.
6. Use only free or open-source resources; verify pricing before adopting external services.
7. Every completed phase must be tested, documented, and versioned.

### Phase 0 Completion Criteria
- [x] Dedicated PS-26190 development branch created.
- [x] Existing `.gitignore` protects `.env`, virtual environments, caches, instance data, uploads, databases, and editor settings.
- [x] Governance documentation added.
- [x] Technology decision policy added.
- [x] Security policy added.

## Phase 1 — Core DMS & Case Management

**Status:** Completed and merged to `main`.

### Implemented Scope
- Case model with unique Case ID, title, description, department, status, creator, and timestamp.
- Case-document relationship model.
- Legal/investigation document categories.
- Document metadata including case association, category, version, and status.
- Case creation interface.
- Case detail interface with associated documents.
- Case-centric dashboard.
- Upload workflow now requires a valid user-owned case and document category.
- Existing AES-256-GCM encryption and encrypted storage flow preserved.
- Existing files remain visible through the dashboard.

## Phase 1.1 — Database Migration System

**Status:** Completed on `feature/ps-26190-dms`; ready for merge.

### Problem Addressed
The Phase 1 application previously called `db.create_all()` during application startup. That is suitable for initial table creation but is not a controlled schema-evolution mechanism because it does not provide ordered, reviewable, reversible migrations.

### Implemented
- Added Alembic migration configuration in `alembic.ini`.
- Added migration environment in `migrations/env.py` using the application's SQLAlchemy metadata.
- Added a reusable migration template.
- Added an initial schema migration covering the current `user`, `stored_files`, `cases`, and `case_documents` tables.
- The initial migration safely leaves already-existing Phase 1 tables intact while creating missing tables on a new database.
- Added Alembic as a free/open-source dependency.
- Removed runtime `db.create_all()` from `app.py`.
- Application startup no longer changes database schema implicitly.

### Migration Workflow
```text
Model Change
    ↓
Create Alembic Migration
    ↓
Review Migration
    ↓
Run: alembic upgrade head
    ↓
Test Application
    ↓
Commit + PR
```

### Important Operational Rule
Database schema changes must now be delivered through Alembic migrations. Developers must not reintroduce `db.create_all()` into application startup.

## Phase 2 — RBAC Foundation

**Status:** Completed and merged to `main`.

### Implemented Scope
- User roles and safe default role.
- Deny-by-default authorization helpers.
- Administrator, case-owner, and shared-document authorization primitives.
- Expiring document shares with view/download/manage permissions.
- Alembic migration `0002_rbac_and_sharing`.

## Phase 2A — RBAC Application Integration

**Status:** Completed and merged to `main`.

### Implemented Scope
- Protected case access and case uploads.
- Protected document downloads and deletion.
- Secure document sharing and revocation.
- Recipient-aware shared-document dashboard.
- Expiry and explicit download-permission enforcement.

## Phase 2B — Role Management & Case Assignment

**Status:** Implementation completed on `feature/ps-26190-phase2-rbac`; pending final merge after verification.

### Implemented Scope
- Added `CaseAssignment` model.
- Added Alembic migration `0003_case_assignments`.
- Added unique case/user assignment constraint.
- Recorded assignment actor and timestamp.
- Case assignments now participate in deny-by-default case authorization.
- Assigned users can see assigned cases on the dashboard and upload to authorized cases.
- Added case assignment management UI.
- Added assignment removal workflow.
- Added Admin user-role management UI.
- Prevented non-admin users from assigning Admin-role accounts.
- Prevented users from removing their own Admin role.
- Added Phase 2B authorization tests for assigned/unassigned access, assignment management, share expiry, and download permissions.
- Added pytest as a free test dependency.

### Security Boundary
Case assignment grants case-level access. It does not bypass independent document-share permissions for users accessing a document outside their assigned case relationship.

### Phase 2B Completion Criteria
- [x] Assignment model and migration.
- [x] Assignment-aware authorization.
- [x] Assigned-case dashboard visibility.
- [x] Assignment management UI.
- [x] Assignment removal.
- [x] Admin role management UI.
- [x] Negative authorization tests added.
- [x] Free-only dependency policy preserved.
- [ ] Execute test suite in the deployment/CI environment.
- [ ] Final PR merge and version tag.

## Next Phase

**Phase 3 — Audit Trail & Document Integrity**

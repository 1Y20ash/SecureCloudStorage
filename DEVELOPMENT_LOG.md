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

### Current Limitation Resolved
- [x] Runtime `db.create_all()` removed.
- [x] Migration framework established.
- [x] Existing Phase 1 database compatibility considered.
- [x] New installations have a migration path for the current schema.
- [ ] Future schema changes will add ordered migration revisions rather than modifying the initial revision.

## Next Phase

**Phase 2 — Role-Based Access Control & Secure Sharing**

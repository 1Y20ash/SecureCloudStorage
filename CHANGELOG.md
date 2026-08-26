# Changelog

All notable changes for the PS 26190 development track are recorded here.

## [Unreleased]

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
- Phase 3: Audit Trail & Document Integrity.

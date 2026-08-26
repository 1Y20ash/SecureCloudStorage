# Changelog

All notable changes for the PS 26190 development track are recorded here.

## [Unreleased]

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
- Phase 2: Role-Based Access Control and Secure Sharing.

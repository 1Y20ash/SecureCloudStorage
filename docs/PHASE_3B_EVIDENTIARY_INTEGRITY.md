# PS 26190 — Phase 3B: Advanced Audit & Evidentiary Integrity

## Objective

Extend the secure DMS with legally useful evidence history while keeping the implementation free-only and auditable.

## Foundation introduced

### Document versions

`document_versions` preserves an immutable record for each document version:
- case document
- sequential version number
- stored encrypted file
- SHA-256 hash
- previous version hash
- creator
- creation timestamp

The `(case_document_id, version)` pair is unique so a version cannot silently be replaced.

### Evidence chain of custody

`evidence_custody` records evidence-handling events with:
- document
- action
- actor
- optional transfer from/to users
- SHA-256 hash snapshot
- notes
- timestamp

This provides the data model for acquisition, transfer, access, return and other evidence events.

## Security rules

1. Case/document authorization remains deny-by-default.
2. Version history is append-only at the application layer; existing versions must never be edited in normal workflows.
3. A version references an existing stored file and its recorded SHA-256 hash.
4. A custody event records the hash observed at the time of the event.
5. Evidence data must use synthetic/test data during development.
6. No paid service is required.
7. All schema changes use Alembic; `db.create_all()` remains prohibited.

## Remaining Phase 3B integration

The next implementation step must wire these models into upload/update/evidence workflows, expose authorized audit/custody views, and add tests for append-only behavior, version sequencing, hash continuity, custody authorization and tamper detection.

# Phase 5 — Evidence Management & Chain of Custody

## Status

**Completed** on `feature/phase5-evidence-chain-of-custody`.

Phase 5 is complete at the service, data-model, migration, integrity, audit, test, CI, and documentation layers. The branch is ready for final local verification and the project's normal merge workflow.

## Scope

Phase 5 establishes a controlled evidence lifecycle and an append-only chain-of-custody record for investigation evidence.

### Evidence record

The `Evidence` model stores:

- immutable public evidence identifier (`EVD-...`)
- case association
- evidence type and description
- collector and current holder
- collection location and UTC collection time
- lifecycle status
- immutable SHA-256 integrity value
- optional link to the encrypted stored file

The supported lifecycle is:

```text
Collected → Uploaded → Transferred → Examined → Stored → Presented
```

Transitions are enforced one step at a time by `evidence_management.py`.

## Chain of custody

`EvidenceCustody` is the append-only custody event model. It remains compatible with the earlier document-custody records while allowing evidence-specific events through `evidence_id`.

Phase 5 records:

- initial `COLLECTED` acquisition
- `TRANSFERRED` custody changes
- explicit `RECEIVED` acceptance by the recipient
- SHA-256 value on every evidence custody event
- actor, previous holder, recipient, timestamp, and optional notes
- corresponding application audit records for transfer and receipt

Custody events are protected from application-level update and delete operations. Corrections are represented by new events rather than rewriting history.

A transfer is authorized only for the current holder and only after the evidence reaches `Uploaded`. The recipient must also have access to the case.

## Integrity verification

`verify_evidence_integrity()` computes SHA-256 over supplied evidence bytes and compares it with the immutable evidence hash using constant-time comparison. Every check is recorded in `AuditLog` with `success=True` for a match and `success=False` for a mismatch.

Evidence SHA-256 values and public evidence identifiers cannot be rewritten after creation through the SQLAlchemy model layer. Malformed SHA-256 values are rejected when evidence is created.

## Database migration

Migration `0008_evidence_management` creates the evidence table and links `evidence_custody.evidence_id` to it with cascading deletion. Schema changes continue to use Alembic rather than runtime table creation.

## Testing

The Phase 5 test suite covers:

- lifecycle transition rules
- invalid transition rejection
- current-holder transfer authorization
- transfer custody and audit events
- evidence creation and initial custody event
- SHA-256 format validation
- explicit receipt and receipt authorization
- integrity pass/fail audit records
- custody-chain retrieval
- append-only custody protection
- immutable evidence identity and integrity hash

The local verification baseline for this branch is **45 passing tests** before the final immutability hardening commits; the added tests must also remain green.

## CI

The repository test workflow runs on pushes to the Phase 5 branch and on pull requests. The workflow installs the pinned project requirements and executes `pytest -q`.

## Version-control controls

- Work is isolated on `feature/phase5-evidence-chain-of-custody`.
- Phase 5 changes are committed separately from `main`.
- The test workflow runs on the Phase 5 branch.
- Only synthetic evidence/data is permitted for development and demonstrations.
- No secrets, real evidence, or credentials belong in the repository.

## Completion checklist

- [x] Evidence model and unique evidence identifier
- [x] Evidence-to-case relationship
- [x] Evidence lifecycle and one-step transition enforcement
- [x] Initial acquisition custody event
- [x] Current-holder custody transfer authorization
- [x] Explicit recipient receipt event
- [x] Custody-chain retrieval
- [x] SHA-256 validation and integrity verification
- [x] Integrity pass/fail audit records
- [x] Immutable evidence identity and SHA-256
- [x] Application-level append-only custody enforcement
- [x] Alembic migration
- [x] Model registration
- [x] Automated test coverage
- [x] CI workflow coverage
- [x] Phase 5 documentation

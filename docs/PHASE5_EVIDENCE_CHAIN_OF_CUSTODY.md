# Phase 5 — Evidence Management & Chain of Custody

## Status

Implementation complete on `feature/phase5-evidence-chain-of-custody`, pending final local verification and merge to the stable development line.

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
- SHA-256 integrity value
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

A transfer is authorized only for the current holder and only after the evidence reaches `Uploaded`. The recipient must also have access to the case.

## Integrity verification

`verify_evidence_integrity()` computes SHA-256 over supplied evidence bytes and compares it with the immutable evidence hash using constant-time comparison. Every check is recorded in `AuditLog` with `success=True` for a match and `success=False` for a mismatch.

Malformed SHA-256 values are rejected when evidence is created.

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

All existing tests must remain green before the Phase 5 branch is merged.

## Version-control controls

- Work is isolated on `feature/phase5-evidence-chain-of-custody`.
- Phase 5 changes are committed separately from `main`.
- The test workflow also runs on the Phase 5 branch.
- Only synthetic evidence/data is permitted for development and demonstrations.
- No secrets, real evidence, or credentials belong in the repository.

# Phase 6 — Digital Signatures

## Objective
Provide a prototype mechanism for verifying the authenticity and integrity of important documents using free/open-source cryptographic implementations.

## Workflow

```text
Document
   ↓
SHA-256 hash
   ↓
Ed25519 digital signature
   ↓
Signed record
   ├── Signer
   ├── Timestamp
   ├── Document hash
   ├── Signature
   └── Verification status
```

## Implementation

- SHA-256 is calculated over the exact document bytes supplied to the signing workflow.
- The SHA-256 digest is signed with Ed25519 using the Python `cryptography` library already present in the project.
- Each application user receives an Ed25519 signing key pair on first use.
- The private key is encrypted at rest with a Fernet key derived from the application's `SECRET_KEY` and is never exposed in the UI or committed to source control.
- The public key, signature, signer snapshot, timestamp, document hash, and verification status are stored in the signed-record table.
- Signed-record cryptographic identity fields are immutable and signed records are append-only.
- Verification recalculates SHA-256 and then verifies the Ed25519 signature against the stored public key.

## Verification outcomes

- `UNVERIFIED`: record exists but has not yet been checked against supplied document bytes.
- `VALID`: supplied document hash matches the stored hash and the Ed25519 signature verifies.
- `INVALID`: the document hash or signature verification fails.

## UI

- `/signatures` — signed-record list.
- `/signatures/new` — sign a document.
- `/signatures/<id>` — inspect a signed record and verify it.
- `/signatures/<id>/verify` — verify supplied document bytes.

## Important legal restriction

This is a **technical cryptographic signature verification prototype**. A valid result does **not** claim statutory, regulatory, court, or legally recognized digital-signature validity. Legal recognition can depend on jurisdiction, identity assurance, certificates, trust-service providers, signature formats, and applicable law.

## Migration

Phase 6 uses Alembic migration `0009_digital_signatures`, following `0008_evidence_management`.

## Version target

`v0.7-digital-signatures`

The version tag must only be created after the Phase 6 test suite, migration check, CI workflow, security review, and final branch verification are all green.

# PS 26190 — Phase 3: Audit Trail & Document Integrity

## Objective

Provide a traceable document lifecycle and cryptographic integrity verification without weakening the existing AES-256-GCM encryption model.

## Implemented Foundation

- `AuditLog` database model
- SHA-256 hashing helper
- SHA-256 verification helper
- Alembic migration `0004_audit_integrity`
- Integrity unit tests
- Audit recorder that stores actor, action, resource, case, result, IP address and timestamp without storing passwords, encryption keys or file contents

## Audit Event Design

Supported event vocabulary includes:

- LOGIN_SUCCESS
- LOGIN_FAILURE
- LOGOUT
- CASE_VIEW
- CASE_CREATE
- DOCUMENT_UPLOAD
- DOCUMENT_VIEW
- DOCUMENT_DOWNLOAD
- DOCUMENT_DELETE
- DOCUMENT_SHARE
- DOCUMENT_SHARE_REVOKE
- ACCESS_DENIED
- CASE_ASSIGN
- CASE_UNASSIGN
- ROLE_CHANGE
- INTEGRITY_FAILURE

The final application integration must record both successful security-sensitive operations and denied/failed access attempts.

## Integrity Design

The SHA-256 digest is stored for the encrypted object currently persisted in storage. This detects changes to the stored ciphertext before decryption. A mismatch must be treated as an integrity failure and the application must not continue with decryption/download.

## Privacy Rules

Audit logs must never contain:

- Passwords
- Encryption passwords
- Secret keys
- Decrypted file contents
- Full uploaded documents
- Sensitive legal data in development

## Phase 3 Completion Criteria

- Audit events persisted for all critical routes
- Audit records visible to authorized administrators
- Integrity hash generated at upload
- Stored object verified before download/decryption
- Integrity failures audited and blocked
- Unauthorized access attempts audited
- Unit/integration tests cover success and failure paths
- Migration tested with the existing Alembic chain

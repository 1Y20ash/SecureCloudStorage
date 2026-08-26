# Phase 2 — RBAC and Secure Sharing Design

## Security model

Authorization is deny-by-default. Authentication alone never grants access to a case or document.

## Roles

- Admin
- Investigating Officer
- Police Officer
- Legal Officer
- Forensic Officer
- Authority

The initial role assigned to a newly registered account is `Police Officer`. Administrative role assignment will be added through controlled functionality rather than accepting arbitrary roles from public registration.

## Access levels

- Case owner: full management of cases/documents they own.
- Admin: system-wide management access.
- Shared recipient: access only to explicitly shared documents and only for the granted permissions.

## Document share permissions

- `can_view`: view/access metadata and document content through the authorized workflow.
- `can_download`: permission to download the decrypted original.
- `can_manage`: reserved for later controlled management operations.
- `expires_at`: optional expiry for temporary access.

## Rules

1. Never trust a role or permission supplied by a client form.
2. Check authorization on the server for every protected operation.
3. Do not expose storage object paths directly to unauthorized users.
4. Expired shares are denied.
5. A share does not grant access to unrelated documents in the same case.
6. Future authorization changes must have migration and negative-test coverage.
7. Real legal/investigation documents must not be used during development.

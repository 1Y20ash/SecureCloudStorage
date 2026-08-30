# Phase 10 RBAC Permission Matrix

The authorization layer is deny-by-default and combines role capability with case ownership/assignment.

| Role | Case review | Case management | Assignment management | Upload | Download | Document scope |
|---|---:|---:|---:|---:|---:|---|
| Admin | Yes | Yes | Yes | Yes | Yes | All |
| Investigating Officer | Yes | Yes (owned) | Yes (owned) | Yes | Yes | Assigned/owned cases |
| Police Officer | Yes | Yes (owned) | No | Yes | Yes | Assigned/owned cases |
| Legal Officer | Yes | No | No | Yes* | Yes* | Legal Notice, Court Filing, Judgment |
| Forensic Officer | Yes | No | No | Yes* | Yes* | Evidence, Forensic Report |
| Authority | Yes | No | No | No | No by default | Review only |

`*` Upload/download for specialist roles is constrained to their document categories by the authorization layer; case assignment remains a prerequisite for case access.

## Security rules

- Admin is the only role with unrestricted access.
- Non-admin case access requires ownership or an explicit case assignment.
- Legal Officer cannot use a share to bypass legal-document category restrictions.
- Forensic Officer cannot use a share to bypass evidence/forensic-document category restrictions.
- Authority has review capability only and does not receive download capability by default.
- Unknown roles receive no permissions because permissions are looked up from a closed role map.
- UI visibility is not the security boundary; server-side authorization remains authoritative.

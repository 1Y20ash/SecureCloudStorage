# PS 26190 — Phase 2B: Role Management & Case Assignment

## Scope

Phase 2B extends the Phase 2A authorization foundation with explicit case assignments. A case can be assigned to authorized stakeholders without changing the existing encryption or sharing model.

## Roles

Supported application roles remain:
- Admin
- Investigating Officer
- Police Officer
- Legal Officer
- Forensic Officer
- Authority

## Assignment Rules

- Admins may manage assignments.
- Case creators/owners may manage assignments for their cases, subject to application authorization rules.
- A user may have at most one assignment per case.
- Assignment records retain who assigned the user and when.
- Assignment deletion removes the user's case assignment; it does not delete the user or case.
- Assignment does not automatically grant permissions outside the case/document authorization policy.
- Existing document shares remain independent and must continue to obey their own expiry and permission rules.

## Security Principle

Case access remains deny-by-default. Assignment is an explicit authorization relationship, not a blanket administrative privilege.

## Database

Migration `0003_case_assignments` creates the `case_assignments` table with foreign keys, indexes, uniqueness on `(case_id, user_id)`, and assignment audit metadata (`assigned_by`, `assigned_at`).

## Free-Only Constraint

No paid service, API, SaaS product, or mandatory subscription is introduced by Phase 2B.

## Testing Requirements

Before Phase 2B is considered complete, test:
- Admin assignment
- Case-owner assignment
- Duplicate assignment rejection
- Unauthorized assignment attempts
- Assigned-user case access
- Unassigned-user denial
- Assignment removal
- Cascade behavior when a case is removed

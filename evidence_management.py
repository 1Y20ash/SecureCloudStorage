"""Phase 5 evidence lifecycle and chain-of-custody service."""

import hashlib
import re
import secrets
from datetime import datetime, timezone

from authz import can_access_case
from extensions import db
from models.audit_log import AuditLog
from models.case import Case
from models.evidence import Evidence
from models.evidence_custody import EvidenceCustody
from models.user import User


TRANSITIONS = {
    Evidence.STATUS_COLLECTED: Evidence.STATUS_UPLOADED,
    Evidence.STATUS_UPLOADED: Evidence.STATUS_TRANSFERRED,
    Evidence.STATUS_TRANSFERRED: Evidence.STATUS_EXAMINED,
    Evidence.STATUS_EXAMINED: Evidence.STATUS_STORED,
    Evidence.STATUS_STORED: Evidence.STATUS_PRESENTED,
}

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _utc_now():
    return datetime.now(timezone.utc)


def _require_case_access(actor_user_id, case):
    actor = db.session.get(User, actor_user_id)
    if actor is None or not can_access_case(actor, case):
        raise PermissionError("User is not authorized to access this case")
    return actor


def _new_evidence_id():
    return f"EVD-{secrets.token_hex(6).upper()}"


def _validate_sha256(sha256_hash):
    if not isinstance(sha256_hash, str) or not SHA256_RE.fullmatch(sha256_hash):
        raise ValueError("A valid SHA-256 evidence hash is required")
    return sha256_hash.lower()


def _add_custody_event(evidence, action, actor_user_id, *, from_user_id=None, to_user_id=None, notes=None):
    event = EvidenceCustody(
        evidence_id=evidence.id,
        action=action,
        actor_user_id=actor_user_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        sha256_hash=evidence.sha256_hash,
        notes=notes,
    )
    db.session.add(event)
    return event


def create_evidence(*, case_id, evidence_type, description, collected_by, collection_location, collection_datetime, sha256_hash, actor_user_id, stored_file_id=None):
    """Create an evidence record and its initial COLLECTED custody event."""
    case = db.session.get(Case, case_id)
    if case is None:
        raise ValueError("Case not found")
    _require_case_access(actor_user_id, case)

    if not evidence_type or not evidence_type.strip():
        raise ValueError("Evidence type is required")
    sha256_hash = _validate_sha256(sha256_hash)
    if collected_by is None:
        raise ValueError("Collected by is required")
    if db.session.get(User, collected_by) is None:
        raise ValueError("Collector not found")

    collection_datetime = collection_datetime or _utc_now()
    evidence = Evidence(
        evidence_id=_new_evidence_id(),
        case_id=case_id,
        evidence_type=evidence_type.strip(),
        description=description.strip() if description else None,
        collected_by=collected_by,
        collection_location=collection_location.strip() if collection_location else None,
        collection_datetime=collection_datetime,
        current_holder=collected_by,
        status=Evidence.STATUS_COLLECTED,
        sha256_hash=sha256_hash,
        stored_file_id=stored_file_id,
    )
    db.session.add(evidence)
    db.session.flush()
    _add_custody_event(evidence, Evidence.STATUS_COLLECTED.upper(), actor_user_id, to_user_id=collected_by, notes="Evidence collected")
    db.session.commit()
    return evidence


def transition_evidence(evidence_id, target_status, actor_user_id, notes=None):
    """Advance an evidence item exactly one step in the defined lifecycle."""
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None:
        raise ValueError("Evidence not found")
    _require_case_access(actor_user_id, evidence.case)

    expected_status = TRANSITIONS.get(evidence.status)
    if expected_status != target_status:
        raise ValueError(f"Invalid evidence transition: {evidence.status} -> {target_status}")

    evidence.status = target_status
    _add_custody_event(evidence, target_status.upper(), actor_user_id, notes=notes)
    db.session.commit()
    return evidence


def transfer_evidence(evidence_id, to_user_id, actor_user_id, notes=None):
    """Transfer custody and atomically record the mandatory audit event."""
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None:
        raise ValueError("Evidence not found")
    _require_case_access(actor_user_id, evidence.case)

    if evidence.status != Evidence.STATUS_UPLOADED:
        raise ValueError("Evidence can only be transferred after upload")
    if evidence.current_holder is None:
        raise ValueError("Evidence has no current holder")
    if evidence.current_holder != actor_user_id:
        raise PermissionError("Only the current holder can transfer evidence")
    if to_user_id is None or db.session.get(User, to_user_id) is None:
        raise ValueError("Recipient not found")
    if to_user_id == evidence.current_holder:
        raise ValueError("Evidence is already held by this user")
    _require_case_access(to_user_id, evidence.case)

    from_user_id = evidence.current_holder
    evidence.current_holder = to_user_id
    evidence.status = Evidence.STATUS_TRANSFERRED
    _add_custody_event(evidence, Evidence.STATUS_TRANSFERRED.upper(), actor_user_id, from_user_id=from_user_id, to_user_id=to_user_id, notes=notes or "Evidence custody transferred")
    db.session.add(AuditLog(user_id=actor_user_id, action="EVIDENCE_TRANSFER", resource_type="Evidence", resource_id=evidence.id, case_id=evidence.case_id, success=True, details=(f"Evidence {evidence.evidence_id} transferred from user {from_user_id} to user {to_user_id}")[:500]))
    db.session.commit()
    return evidence


def receive_evidence(evidence_id, actor_user_id, notes=None):
    """Record explicit acceptance by the current holder after a transfer."""
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None:
        raise ValueError("Evidence not found")
    _require_case_access(actor_user_id, evidence.case)
    if evidence.status != Evidence.STATUS_TRANSFERRED:
        raise ValueError("Evidence can only be received after transfer")
    if evidence.current_holder != actor_user_id:
        raise PermissionError("Only the current holder can receive evidence")

    event = _add_custody_event(
        evidence,
        "RECEIVED",
        actor_user_id,
        to_user_id=actor_user_id,
        notes=notes or "Evidence custody received",
    )
    db.session.add(AuditLog(user_id=actor_user_id, action="EVIDENCE_RECEIVED", resource_type="Evidence", resource_id=evidence.id, case_id=evidence.case_id, success=True, details=f"Evidence {evidence.evidence_id} received by user {actor_user_id}"))
    db.session.commit()
    return event


def verify_evidence_integrity(evidence_id, file_bytes, actor_user_id):
    """Verify supplied plaintext bytes against the immutable evidence SHA-256."""
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None:
        raise ValueError("Evidence not found")
    _require_case_access(actor_user_id, evidence.case)
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise ValueError("Evidence bytes are required")

    actual_hash = hashlib.sha256(file_bytes).hexdigest()
    verified = secrets.compare_digest(actual_hash, evidence.sha256_hash)
    db.session.add(AuditLog(user_id=actor_user_id, action="EVIDENCE_INTEGRITY_CHECK", resource_type="Evidence", resource_id=evidence.id, case_id=evidence.case_id, success=verified, details=(f"SHA-256 integrity check: {'passed' if verified else 'failed'}; expected={evidence.sha256_hash}; actual={actual_hash}")[:500]))
    db.session.commit()
    return verified


def get_custody_chain(evidence_id):
    evidence = db.session.get(Evidence, evidence_id)
    if evidence is None:
        raise ValueError("Evidence not found")
    return list(evidence.custody_events)

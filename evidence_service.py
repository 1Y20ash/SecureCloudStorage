from datetime import datetime, timezone

from extensions import db
from integrity import verify_sha256
from models.evidence import Evidence
from models.evidence_custody_event import EvidenceCustodyEvent


EVIDENCE_STATUSES = (
    "Collected",
    "In Custody",
    "Transferred",
    "Released",
    "Archived",
)

CUSTODY_ACTIONS = (
    "ACQUIRED",
    "TRANSFERRED",
    "RECEIVED",
    "RELEASED",
)


def create_evidence(
    case_id,
    evidence_type,
    sha256_hash,
    collected_by,
    description=None,
    collection_location=None,
    collected_at=None,
):
    """Create an evidence record and its initial custody event."""

    if not case_id:
        raise ValueError("case_id is required")

    if not evidence_type or not evidence_type.strip():
        raise ValueError("evidence_type is required")

    if not sha256_hash or len(sha256_hash) != 64:
        raise ValueError("A valid SHA-256 hash is required")

    if not collected_by:
        raise ValueError("collected_by is required")

    collected_at = collected_at or datetime.now(timezone.utc)

    evidence = Evidence(
        case_id=case_id,
        evidence_type=evidence_type.strip(),
        description=description,
        collected_by=collected_by,
        collection_location=collection_location,
        collected_at=collected_at,
        current_holder=collected_by,
        status="Collected",
        sha256_hash=sha256_hash.lower(),
    )

    db.session.add(evidence)
    db.session.flush()

    db.session.add(
        EvidenceCustodyEvent(
            evidence_id=evidence.id,
            action="ACQUIRED",
            actor_user_id=collected_by,
            from_user_id=None,
            to_user_id=collected_by,
            sha256_hash=evidence.sha256_hash,
            notes="Evidence initially acquired.",
        )
    )

    return evidence


def transfer_custody(evidence, actor_user_id, to_user_id, notes=None):
    """Transfer evidence from its current holder to another user."""

    if evidence is None:
        raise ValueError("Evidence not found")

    if not actor_user_id:
        raise ValueError("actor_user_id is required")

    if not to_user_id:
        raise ValueError("to_user_id is required")

    if evidence.status == "Archived":
        raise ValueError("Archived evidence cannot be transferred")

    if evidence.current_holder != actor_user_id:
        raise ValueError("Only the current holder can transfer custody")

    if evidence.current_holder == to_user_id:
        raise ValueError("Evidence is already held by this user")

    previous_holder = evidence.current_holder

    evidence.current_holder = to_user_id
    evidence.status = "Transferred"

    db.session.add(
        EvidenceCustodyEvent(
            evidence_id=evidence.id,
            action="TRANSFERRED",
            actor_user_id=actor_user_id,
            from_user_id=previous_holder,
            to_user_id=to_user_id,
            sha256_hash=evidence.sha256_hash,
            notes=notes,
        )
    )

    return evidence


def verify_evidence_integrity(evidence, file_bytes):
    """Verify supplied evidence bytes against the recorded SHA-256 hash."""

    if evidence is None:
        return False

    return verify_sha256(file_bytes, evidence.sha256_hash)
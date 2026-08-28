"""Application-level document lifecycle operations for Phase 4."""

from sqlalchemy.exc import IntegrityError

from extensions import db
from lifecycle import transition_status
from models.audit_log import AuditLog
from models.case_document import CaseDocument
from models.document_version import DocumentVersion


def get_current_version(document):
    """Return the current version record for a case document."""
    return db.session.scalar(
        db.select(DocumentVersion)
        .where(DocumentVersion.case_document_id == document.id)
        .order_by(DocumentVersion.version.desc())
    )


def transition_document(document, new_status, actor_user_id, change_description=None):
    """Transition the current document version and keep the legacy document status in sync."""
    version = get_current_version(document)
    if version is None:
        raise ValueError("Document has no version history.")

    old_status = version.lifecycle_status
    transition_status(version, new_status)
    version.change_description = change_description or version.change_description
    document.status = new_status

    db.session.add(AuditLog(
        user_id=actor_user_id,
        action="LIFECYCLE_TRANSITION",
        resource_type="DocumentVersion",
        resource_id=version.id,
        case_id=document.case_id,
        success=True,
        details=f"Lifecycle transition {old_status} -> {new_status}"[:500],
    ))
    return version


def restore_document_version(document, version_number, actor_user_id, reason=None):
    """Restore a previous stored file as the current document without deleting history.

    Restoration creates a new version pointing to the selected historical file,
    preserving the complete version chain. The restored version starts in Draft.
    """
    current = get_current_version(document)
    if current is None:
        raise ValueError("Requested document version does not exist.")
    if current.lifecycle_status == DocumentVersion.LIFECYCLE_ARCHIVED:
        raise ValueError("Archived documents cannot be restored.")

    target = db.session.scalar(
        db.select(DocumentVersion).where(
            DocumentVersion.case_document_id == document.id,
            DocumentVersion.version == version_number,
        )
    )
    if target is None:
        raise ValueError("Requested document version does not exist.")
    if target.id == current.id:
        raise ValueError("The current document version cannot be restored.")

    next_version_number = current.version + 1
    restored = DocumentVersion(
        case_document_id=document.id,
        version=next_version_number,
        stored_file_id=target.stored_file_id,
        sha256_hash=target.sha256_hash,
        previous_hash=current.sha256_hash,
        created_by=actor_user_id,
        change_description=reason or f"Restored from version {version_number}",
        lifecycle_status=DocumentVersion.LIFECYCLE_DRAFT,
    )
    db.session.add(restored)
    document.stored_file_id = target.stored_file_id
    document.version = next_version_number
    document.status = DocumentVersion.LIFECYCLE_DRAFT

    db.session.add(AuditLog(
        user_id=actor_user_id,
        action="VERSION_RESTORED",
        resource_type="DocumentVersion",
        resource_id=target.id,
        case_id=document.case_id,
        success=True,
        details=f"Restored version {version_number} as version {next_version_number}"[:500],
    ))
    return restored

from models.document_version import DocumentVersion
from extensions import db


def get_next_version(case_document_id):
    """Return the next sequential version number for a case document."""
    latest = db.session.scalar(
        db.select(DocumentVersion)
        .where(DocumentVersion.case_document_id == case_document_id)
        .order_by(DocumentVersion.version.desc())
    )

    if latest is None:
        return 1

    return latest.version + 1


def get_previous_hash(case_document_id):
    """Return the SHA-256 hash of the latest document version."""
    latest = db.session.scalar(
        db.select(DocumentVersion)
        .where(DocumentVersion.case_document_id == case_document_id)
        .order_by(DocumentVersion.version.desc())
    )

    if latest is None:
        return None

    return latest.sha256_hash
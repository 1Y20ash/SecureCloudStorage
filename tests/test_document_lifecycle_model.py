from datetime import datetime, timezone

from app import app
from extensions import db
from models.document_version import DocumentVersion


def test_document_version_defaults_and_constraints():
    with app.app_context():
        assert DocumentVersion.__table__.c.lifecycle_status.default.arg == "Draft"
        assert DocumentVersion.__table__.c.lifecycle_status.server_default.arg == "Draft"
        assert DocumentVersion.__table__.c.change_description.type.length == 500
        assert DocumentVersion.__table__.c.lifecycle_status.type.length == 20
        assert any(
            constraint.name == "uq_document_version"
            for constraint in DocumentVersion.__table__.constraints
        )


def test_document_version_can_store_lifecycle_metadata():
    with app.app_context():
        version = DocumentVersion(
            case_document_id=999999,
            version=1,
            stored_file_id=999999,
            sha256_hash="a" * 64,
            previous_hash=None,
            created_by=None,
            created_at=datetime.now(timezone.utc),
            change_description="Initial document version",
            lifecycle_status="Draft",
        )
        assert version.lifecycle_status == "Draft"
        assert version.change_description == "Initial document version"

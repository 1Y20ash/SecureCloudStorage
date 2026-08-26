from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from document_lifecycle import restore_document_version, transition_document
from models.document_version import DocumentVersion


def test_transition_document_updates_version_and_document():
    version = SimpleNamespace(
        id=7,
        lifecycle_status=DocumentVersion.LIFECYCLE_DRAFT,
        change_description=None,
    )
    document = SimpleNamespace(id=3, case_id=9, status=DocumentVersion.LIFECYCLE_DRAFT)

    with patch("document_lifecycle.get_current_version", return_value=version), \
         patch("document_lifecycle.db.session.add") as add:
        result = transition_document(
            document,
            DocumentVersion.LIFECYCLE_REVIEWED,
            actor_user_id=12,
            change_description="Submitted for review",
        )

    assert result is version
    assert version.lifecycle_status == DocumentVersion.LIFECYCLE_REVIEWED
    assert version.change_description == "Submitted for review"
    assert document.status == DocumentVersion.LIFECYCLE_REVIEWED
    add.assert_called_once()


def test_transition_document_requires_existing_version():
    document = SimpleNamespace(id=3, case_id=9, status="Draft")
    with patch("document_lifecycle.get_current_version", return_value=None):
        with pytest.raises(ValueError, match="no version history"):
            transition_document(document, "Reviewed", actor_user_id=1)


def test_restore_creates_new_version_without_destroying_history():
    current = SimpleNamespace(
        id=10,
        version=3,
        sha256_hash="c" * 64,
        lifecycle_status=DocumentVersion.LIFECYCLE_REVIEWED,
    )
    target = SimpleNamespace(id=8, version=1, stored_file_id=55, sha256_hash="a" * 64)
    document = SimpleNamespace(
        id=3,
        case_id=9,
        stored_file_id=99,
        version=3,
        status=DocumentVersion.LIFECYCLE_REVIEWED,
    )

    fake_session = Mock()
    fake_session.scalar.side_effect = [target]

    with patch("document_lifecycle.get_current_version", return_value=current), \
         patch("document_lifecycle.db.session", fake_session):
        restored = restore_document_version(document, 1, actor_user_id=12, reason="Rollback after review")

    assert restored.version == 4
    assert restored.stored_file_id == 55
    assert restored.sha256_hash == "a" * 64
    assert restored.previous_hash == "c" * 64
    assert restored.lifecycle_status == DocumentVersion.LIFECYCLE_DRAFT
    assert document.stored_file_id == 55
    assert document.version == 4
    assert document.status == DocumentVersion.LIFECYCLE_DRAFT
    assert fake_session.add.call_count == 2


def test_archived_document_cannot_be_restored():
    current = SimpleNamespace(
        id=10,
        version=3,
        sha256_hash="c" * 64,
        lifecycle_status=DocumentVersion.LIFECYCLE_ARCHIVED,
    )
    document = SimpleNamespace(id=3, case_id=9)

    with patch("document_lifecycle.get_current_version", return_value=current):
        with pytest.raises(ValueError, match="Archived documents cannot be restored"):
            restore_document_version(document, 1, actor_user_id=12)

import pytest

from app import app
from models.document_version import DocumentVersion
from lifecycle import can_transition, transition_status


def test_lifecycle_transition_matrix():
    assert can_transition("Draft", "Reviewed")
    assert can_transition("Reviewed", "Approved")
    assert can_transition("Approved", "Archived")

    assert not can_transition("Draft", "Approved")
    assert not can_transition("Reviewed", "Archived")
    assert not can_transition("Approved", "Draft")
    assert not can_transition("Archived", "Draft")
    assert not can_transition("Unknown", "Draft")


def test_transition_status_updates_valid_state():
    version = DocumentVersion(lifecycle_status="Draft")
    transition_status(version, "Reviewed")
    assert version.lifecycle_status == "Reviewed"


def test_transition_status_rejects_invalid_transition():
    version = DocumentVersion(lifecycle_status="Draft")
    with pytest.raises(ValueError, match="Invalid document lifecycle transition"):
        transition_status(version, "Approved")


def test_archived_version_is_terminal():
    version = DocumentVersion(lifecycle_status="Archived")
    with pytest.raises(ValueError):
        transition_status(version, "Draft")

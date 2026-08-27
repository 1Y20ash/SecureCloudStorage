from types import SimpleNamespace

import pytest

from evidence_service import (
    create_evidence,
    transfer_custody,
    verify_evidence_integrity,
)
from extensions import db


def test_create_evidence_creates_acquisition_event(monkeypatch):
    added = []

    monkeypatch.setattr(db.session, "add", lambda obj: added.append(obj))
    monkeypatch.setattr(db.session, "flush", lambda: setattr(added[0], "id", 1))

    evidence = create_evidence(
        case_id=10,
        evidence_type="Digital Evidence",
        sha256_hash="a" * 64,
        collected_by=5,
        description="Test evidence",
    )

    assert evidence.case_id == 10
    assert evidence.evidence_type == "Digital Evidence"
    assert evidence.collected_by == 5
    assert evidence.current_holder == 5
    assert evidence.status == "Collected"
    assert evidence.sha256_hash == "a" * 64

    events = [obj for obj in added if obj.__class__.__name__ == "EvidenceCustodyEvent"]

    assert len(events) == 1
    assert events[0].action == "ACQUIRED"
    assert events[0].actor_user_id == 5
    assert events[0].from_user_id is None
    assert events[0].to_user_id == 5
    assert events[0].sha256_hash == "a" * 64


def test_transfer_requires_current_holder():
    evidence = SimpleNamespace(
        id=1,
        current_holder=5,
        status="Collected",
        sha256_hash="a" * 64,
    )

    with pytest.raises(ValueError, match="current holder"):
        transfer_custody(
            evidence,
            actor_user_id=9,
            to_user_id=10,
        )


def test_transfer_updates_holder_and_creates_event(monkeypatch):
    added = []

    monkeypatch.setattr(db.session, "add", lambda obj: added.append(obj))

    evidence = SimpleNamespace(
        id=1,
        current_holder=5,
        status="Collected",
        sha256_hash="a" * 64,
    )

    result = transfer_custody(
        evidence,
        actor_user_id=5,
        to_user_id=9,
        notes="Transferred for forensic examination.",
    )

    assert result is evidence
    assert evidence.current_holder == 9
    assert evidence.status == "Transferred"

    event = added[0]

    assert event.action == "TRANSFERRED"
    assert event.actor_user_id == 5
    assert event.from_user_id == 5
    assert event.to_user_id == 9
    assert event.sha256_hash == "a" * 64
    assert event.notes == "Transferred for forensic examination."


def test_archived_evidence_cannot_be_transferred():
    evidence = SimpleNamespace(
        id=1,
        current_holder=5,
        status="Archived",
        sha256_hash="a" * 64,
    )

    with pytest.raises(ValueError, match="Archived"):
        transfer_custody(
            evidence,
            actor_user_id=5,
            to_user_id=9,
        )


def test_evidence_integrity_verification():
    evidence = SimpleNamespace(
        sha256_hash=(
            "e879342a6cf6ef8b17671f8e5653276d519e82e361d30c9d8a27118bedcbdfa4"
        )
    )

    original = b"PS 26190 synthetic document"
    tampered = b"PS 26190 modified document"

    assert verify_evidence_integrity(evidence, original)
    assert not verify_evidence_integrity(evidence, tampered)
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from evidence_management import (
    TRANSITIONS,
    create_evidence,
    get_custody_chain,
    receive_evidence,
    transfer_evidence,
    transition_evidence,
    verify_evidence_integrity,
)
from extensions import db
from models.case import Case
from models.evidence import Evidence, _prevent_evidence_identity_change
from models.evidence_custody import (
    EvidenceCustody,
    _prevent_custody_event_delete,
    _prevent_custody_event_update,
)
from models.user import User


def test_phase5_lifecycle_transitions_match_pdp():
    assert TRANSITIONS == {
        Evidence.STATUS_COLLECTED: Evidence.STATUS_UPLOADED,
        Evidence.STATUS_UPLOADED: Evidence.STATUS_TRANSFERRED,
        Evidence.STATUS_TRANSFERRED: Evidence.STATUS_EXAMINED,
        Evidence.STATUS_EXAMINED: Evidence.STATUS_STORED,
        Evidence.STATUS_STORED: Evidence.STATUS_PRESENTED,
    }


def test_invalid_evidence_transition_is_rejected():
    evidence = SimpleNamespace(id=10, status=Evidence.STATUS_COLLECTED, case=SimpleNamespace(id=9))
    with patch("evidence_management.db.session.get", return_value=evidence), patch("evidence_management._require_case_access"):
        with pytest.raises(ValueError, match="Invalid evidence transition"):
            transition_evidence(10, Evidence.STATUS_EXAMINED, actor_user_id=12)


def test_transfer_rejects_non_holder():
    evidence = SimpleNamespace(id=10, case=SimpleNamespace(id=9), status=Evidence.STATUS_UPLOADED, current_holder=12, sha256_hash="a" * 64)
    recipient = SimpleNamespace(id=15)
    def get_record(model, record_id):
        if model is Evidence:
            return evidence
        if model is User and record_id == 15:
            return recipient
        return None
    with patch("evidence_management.db.session.get", side_effect=get_record), patch("evidence_management._require_case_access"):
        with pytest.raises(PermissionError, match="current holder"):
            transfer_evidence(10, 15, actor_user_id=99)


def test_transfer_creates_custody_event_and_audit_event():
    evidence = SimpleNamespace(id=10, evidence_id="EVD-ABC123", case_id=9, status=Evidence.STATUS_UPLOADED, current_holder=12, sha256_hash="a" * 64, case=SimpleNamespace(id=9))
    recipient = SimpleNamespace(id=15)
    def get_record(model, record_id):
        if model is Evidence:
            return evidence
        if model is User:
            return recipient
        return None
    with patch("evidence_management.db.session.get", side_effect=get_record), patch("evidence_management._require_case_access"), patch.object(db.session, "add") as add, patch.object(db.session, "commit") as commit:
        result = transfer_evidence(10, 15, actor_user_id=12, notes="Handed to forensic officer")
    assert result is evidence
    assert evidence.status == Evidence.STATUS_TRANSFERRED
    assert evidence.current_holder == 15
    assert commit.called
    added = [call.args[0] for call in add.call_args_list]
    custody = next(item for item in added if item.__class__.__name__ == "EvidenceCustody")
    audit = next(item for item in added if item.__class__.__name__ == "AuditLog")
    assert custody.action == "TRANSFERRED"
    assert custody.from_user_id == 12
    assert custody.to_user_id == 15
    assert custody.sha256_hash == "a" * 64
    assert audit.action == "EVIDENCE_TRANSFER"
    assert audit.resource_type == "Evidence"
    assert audit.resource_id == 10
    assert audit.case_id == 9
    assert audit.success is True


def test_create_evidence_records_initial_custody_event():
    case = SimpleNamespace(id=9)
    collector = SimpleNamespace(id=12)
    added = []
    def get_record(model, record_id):
        if model is Case:
            return case
        if model is User and record_id == 12:
            return collector
        return None
    with patch("evidence_management.db.session.get", side_effect=get_record), patch("evidence_management._require_case_access"), patch.object(db.session, "add", side_effect=added.append), patch.object(db.session, "flush", side_effect=lambda: setattr(added[0], "id", 21)), patch.object(db.session, "commit"):
        evidence = create_evidence(case_id=9, evidence_type="Digital Evidence", description="Disk image", collected_by=12, collection_location="Lab", collection_datetime=None, sha256_hash="A" * 64, actor_user_id=12)
    assert evidence.evidence_id.startswith("EVD-")
    assert evidence.status == Evidence.STATUS_COLLECTED
    assert evidence.current_holder == 12
    assert evidence.sha256_hash == "a" * 64
    event = next(item for item in added if item.__class__.__name__ == "EvidenceCustody")
    assert event.action == "COLLECTED"
    assert event.to_user_id == 12
    assert event.sha256_hash == "a" * 64


def test_create_evidence_rejects_malformed_hash():
    with patch("evidence_management.db.session.get", side_effect=lambda model, record_id: SimpleNamespace(id=9) if model is Case else SimpleNamespace(id=12)), patch("evidence_management._require_case_access"):
        with pytest.raises(ValueError, match="SHA-256"):
            create_evidence(case_id=9, evidence_type="Digital Evidence", description=None, collected_by=12, collection_location=None, collection_datetime=None, sha256_hash="not-a-hash", actor_user_id=12)


def test_receive_requires_current_holder_and_records_event():
    evidence = SimpleNamespace(id=10, evidence_id="EVD-ABC123", case_id=9, status=Evidence.STATUS_TRANSFERRED, current_holder=15, sha256_hash="a" * 64, case=SimpleNamespace(id=9))
    added = []
    with patch("evidence_management.db.session.get", return_value=evidence), patch("evidence_management._require_case_access"), patch.object(db.session, "add", side_effect=added.append), patch.object(db.session, "commit"):
        event = receive_evidence(10, actor_user_id=15, notes="Received intact")
    assert event.action == "RECEIVED"
    assert event.actor_user_id == 15
    assert event.to_user_id == 15
    audit = next(item for item in added if item.__class__.__name__ == "AuditLog")
    assert audit.action == "EVIDENCE_RECEIVED"
    assert audit.success is True


def test_receive_rejects_non_holder():
    evidence = SimpleNamespace(id=10, status=Evidence.STATUS_TRANSFERRED, current_holder=15, case=SimpleNamespace(id=9))
    with patch("evidence_management.db.session.get", return_value=evidence), patch("evidence_management._require_case_access"):
        with pytest.raises(PermissionError, match="current holder"):
            receive_evidence(10, actor_user_id=12)


def test_verify_evidence_integrity_records_pass_or_fail():
    original = b"PS 26190 synthetic document"
    expected_hash = "e879342a6cf6ef8b17671f8e5653276d519e82e361d30c9d8a27118bedcbdfa4"
    evidence = SimpleNamespace(id=10, case_id=9, sha256_hash=expected_hash, case=SimpleNamespace(id=9))
    added = []
    with patch("evidence_management.db.session.get", return_value=evidence), patch("evidence_management._require_case_access"), patch.object(db.session, "add", side_effect=added.append), patch.object(db.session, "commit"):
        assert verify_evidence_integrity(10, original, actor_user_id=12) is True
    assert added[0].action == "EVIDENCE_INTEGRITY_CHECK"
    assert added[0].success is True
    added.clear()
    with patch("evidence_management.db.session.get", return_value=evidence), patch("evidence_management._require_case_access"), patch.object(db.session, "add", side_effect=added.append), patch.object(db.session, "commit"):
        assert verify_evidence_integrity(10, b"PS 26190 modified document", actor_user_id=12) is False
    assert added[0].action == "EVIDENCE_INTEGRITY_CHECK"
    assert added[0].success is False


def test_get_custody_chain_returns_events_in_model_order():
    events = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    evidence = SimpleNamespace(id=10, custody_events=events)
    with patch("evidence_management.db.session.get", return_value=evidence):
        assert get_custody_chain(10) == events


def test_custody_event_update_is_rejected():
    with pytest.raises(ValueError, match="append-only"):
        _prevent_custody_event_update(None, None, SimpleNamespace())


def test_custody_event_delete_is_rejected():
    with pytest.raises(ValueError, match="append-only"):
        _prevent_custody_event_delete(None, None, SimpleNamespace())


def test_evidence_identity_and_hash_are_immutable():
    evidence = Evidence(evidence_id="EVD-ABC123", sha256_hash="a" * 64)
    evidence.evidence_id = "EVD-CHANGED"
    with pytest.raises(ValueError, match="identifiers are immutable"):
        _prevent_evidence_identity_change(None, None, evidence)

    evidence = Evidence(evidence_id="EVD-ABC123", sha256_hash="a" * 64)
    evidence.sha256_hash = "b" * 64
    with pytest.raises(ValueError, match="SHA-256 hashes are immutable"):
        _prevent_evidence_identity_change(None, None, evidence)

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from evidence_management import TRANSITIONS, transfer_evidence, transition_evidence
from extensions import db
from models.evidence import Evidence
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
    evidence = SimpleNamespace(
        id=10,
        status=Evidence.STATUS_COLLECTED,
        case=SimpleNamespace(id=9),
    )

    with patch("evidence_management.db.session.get", return_value=evidence), patch(
        "evidence_management._require_case_access"
    ):
        with pytest.raises(ValueError, match="Invalid evidence transition"):
            transition_evidence(10, Evidence.STATUS_EXAMINED, actor_user_id=12)


def test_transfer_creates_custody_event_and_audit_event():
    evidence = SimpleNamespace(
        id=10,
        evidence_id="EVD-ABC123",
        case_id=9,
        status=Evidence.STATUS_UPLOADED,
        current_holder=12,
        sha256_hash="a" * 64,
        case=SimpleNamespace(id=9),
    )
    recipient = SimpleNamespace(id=15)

    def get_record(model, record_id):
        if model is Evidence:
            return evidence
        if model is User:
            return recipient
        return None

    with patch("evidence_management.db.session.get", side_effect=get_record), patch(
        "evidence_management._require_case_access"
    ), patch.object(db.session, "add") as add, patch.object(db.session, "commit") as commit:
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

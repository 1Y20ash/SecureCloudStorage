from types import SimpleNamespace

import pytest

from authz import (
    can_access_case,
    can_access_document,
    can_download_document,
    can_manage_case,
    can_manage_case_assignments,
)


ROLES = (
    "Admin",
    "Investigating Officer",
    "Police Officer",
    "Legal Officer",
    "Forensic Officer",
    "Authority",
)


def user(role, user_id=1):
    return SimpleNamespace(is_authenticated=True, role=role, id=user_id)


def case(created_by=1, assigned_ids=()):
    return SimpleNamespace(
        id=10,
        created_by=created_by,
        assignments=[SimpleNamespace(user_id=uid) for uid in assigned_ids],
    )


def document(category, case_obj):
    return SimpleNamespace(
        category=category,
        case=case_obj,
        shares=[],
    )


def test_all_pdp_roles_are_known():
    from models.user import ROLES as MODEL_ROLES

    assert MODEL_ROLES == ROLES


@pytest.mark.parametrize("role", ["Investigating Officer", "Police Officer"])
def test_investigation_roles_can_manage_owned_case(role):
    assert can_manage_case(user(role), case(created_by=1))


@pytest.mark.parametrize("role", ["Investigating Officer", "Police Officer"])
def test_investigation_roles_can_manage_assignments_on_owned_case(role):
    assert can_manage_case_assignments(user(role), case(created_by=1))


def test_admin_can_manage_any_case():
    assert can_manage_case(user("Admin"), case(created_by=99))
    assert can_manage_case_assignments(user("Admin"), case(created_by=99))


def test_assigned_investigation_roles_can_access_case():
    assert can_access_case(user("Investigating Officer"), case(created_by=99, assigned_ids=(1,)))
    assert can_access_case(user("Police Officer"), case(created_by=99, assigned_ids=(1,)))


@pytest.mark.parametrize("role", ["Legal Officer", "Forensic Officer", "Authority"])
def test_specialist_roles_can_review_assigned_case(role):
    assert can_access_case(user(role), case(created_by=99, assigned_ids=(1,)))


def test_unassigned_non_admin_cannot_access_case():
    assert not can_access_case(user("Police Officer"), case(created_by=99, assigned_ids=(2,)))


@pytest.mark.parametrize("category", ["Legal Notice", "Court Filing", "Judgment"])
def test_legal_officer_is_restricted_to_legal_documents(category):
    assert can_access_document(user("Legal Officer"), document(category, case(created_by=99, assigned_ids=(1,))))


def test_legal_officer_cannot_access_investigation_document():
    assert not can_access_document(
        user("Legal Officer"),
        document("Police Report", case(created_by=99, assigned_ids=(1,))),
    )


@pytest.mark.parametrize("category", ["Evidence", "Forensic Report"])
def test_forensic_officer_is_restricted_to_evidence_documents(category):
    assert can_access_document(user("Forensic Officer"), document(category, case(created_by=99, assigned_ids=(1,))))


def test_forensic_officer_cannot_access_legal_document():
    assert not can_access_document(
        user("Forensic Officer"),
        document("Legal Notice", case(created_by=99, assigned_ids=(1,))),
    )


def test_authority_can_review_but_cannot_download_by_default():
    doc = document("Police Report", case(created_by=99, assigned_ids=(1,)))
    assert can_access_document(user("Authority"), doc)
    assert not can_download_document(user("Authority"), doc)


def test_admin_can_access_and_download_any_document():
    doc = document("Judgment", case(created_by=99))
    assert can_access_document(user("Admin"), doc)
    assert can_download_document(user("Admin"), doc)


def test_document_share_does_not_bypass_specialist_category_restriction():
    doc = document("Police Report", case(created_by=99, assigned_ids=(2,)))
    doc.shares = [
        SimpleNamespace(
            shared_with_user_id=1,
            can_view=True,
            can_download=True,
            expires_at=None,
        )
    ]
    assert not can_access_document(user("Legal Officer"), doc)

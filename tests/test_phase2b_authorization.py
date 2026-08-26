from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from authz import can_access_case, can_download_document, can_manage_case_assignments, share_is_active


def user(user_id, role="Police Officer"):
    return SimpleNamespace(id=user_id, role=role, is_authenticated=True)


def case(owner_id, assignments=()):
    return SimpleNamespace(created_by=owner_id, assignments=list(assignments))


def assignment(user_id):
    return SimpleNamespace(user_id=user_id)


def test_assigned_user_can_access_case():
    assigned = user(2)
    target_case = case(1, [assignment(2)])
    assert can_access_case(assigned, target_case) is True


def test_unassigned_user_is_denied_case_access():
    unassigned = user(3)
    target_case = case(1, [assignment(2)])
    assert can_access_case(unassigned, target_case) is False


def test_case_owner_can_manage_assignments():
    owner = user(1)
    assert can_manage_case_assignments(owner, case(1)) is True


def test_non_owner_cannot_manage_assignments():
    other_user = user(2)
    assert can_manage_case_assignments(other_user, case(1)) is False


def test_admin_can_manage_assignments():
    admin = user(9, "Admin")
    assert can_manage_case_assignments(admin, case(1)) is True


def test_expired_share_is_inactive():
    share = SimpleNamespace(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert share_is_active(share) is False


def test_active_download_share_allows_download():
    viewer = user(2)
    owner = user(1)
    target_case = case(1)
    share = SimpleNamespace(
        shared_with_user_id=2,
        can_view=True,
        can_download=True,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    document = SimpleNamespace(case=target_case, shares=[share])
    assert can_download_document(viewer, document) is True


def test_view_only_share_denies_download():
    viewer = user(2)
    target_case = case(1)
    share = SimpleNamespace(
        shared_with_user_id=2,
        can_view=True,
        can_download=False,
        expires_at=None,
    )
    document = SimpleNamespace(case=target_case, shares=[share])
    assert can_download_document(viewer, document) is False

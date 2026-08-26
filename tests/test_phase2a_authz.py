from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from authz import can_access_case, can_access_document, can_download_document, share_is_active


def user(user_id, role="Police Officer"):
    return SimpleNamespace(id=user_id, role=role, is_authenticated=True)


def case(owner_id=1):
    return SimpleNamespace(id=10, created_by=owner_id)


def document(owner_id=1, shares=None):
    return SimpleNamespace(
        id=20,
        case=case(owner_id),
        shares=shares or [],
    )


def share(recipient_id, can_view=True, can_download=False, expires_at=None):
    return SimpleNamespace(
        shared_with_user_id=recipient_id,
        can_view=can_view,
        can_download=can_download,
        expires_at=expires_at,
    )


def test_case_owner_can_access_case():
    assert can_access_case(user(1), case(1)) is True


def test_other_user_cannot_access_case():
    assert can_access_case(user(2), case(1)) is False


def test_admin_can_access_any_case():
    assert can_access_case(user(2, "Admin"), case(1)) is True


def test_shared_view_user_can_access_document():
    assert can_access_document(user(2), document(1, [share(2, can_view=True)])) is True


def test_shared_user_without_view_cannot_access_document():
    assert can_access_document(user(2), document(1, [share(2, can_view=False)])) is False


def test_download_requires_download_permission():
    doc = document(1, [share(2, can_view=True, can_download=False)])
    assert can_download_document(user(2), doc) is False
    doc = document(1, [share(2, can_view=True, can_download=True)])
    assert can_download_document(user(2), doc) is True


def test_expired_share_is_rejected():
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    doc = document(1, [share(2, can_view=True, can_download=True, expires_at=expired)])
    assert share_is_active(doc.shares[0]) is False
    assert can_access_document(user(2), doc) is False
    assert can_download_document(user(2), doc) is False


def test_admin_can_download_any_case_document():
    assert can_download_document(user(9, "Admin"), document(1)) is True

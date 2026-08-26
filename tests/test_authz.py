from datetime import datetime, timedelta, timezone

from authz import can_access_case, can_access_document, can_download_document


def test_case_owner_can_access(case_factory, user_factory):
    user = user_factory(id=1, role="Police Officer")
    case = case_factory(created_by=1)
    assert can_access_case(user, case) is True


def test_non_owner_cannot_access_case(case_factory, user_factory):
    user = user_factory(id=2, role="Police Officer")
    case = case_factory(created_by=1)
    assert can_access_case(user, case) is False


def test_admin_can_access_case(case_factory, user_factory):
    user = user_factory(id=99, role="Admin")
    case = case_factory(created_by=1)
    assert can_access_case(user, case) is True


def test_expired_share_cannot_access_document(document_factory, user_factory, share_factory):
    user = user_factory(id=2, role="Forensic Officer")
    document = document_factory(case_owner_id=1)
    share_factory(case_document=document, shared_with_user_id=2, can_view=True,
                  expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert can_access_document(user, document) is False


def test_view_share_without_download_cannot_download(document_factory, user_factory, share_factory):
    user = user_factory(id=2, role="Forensic Officer")
    document = document_factory(case_owner_id=1)
    share_factory(case_document=document, shared_with_user_id=2, can_view=True, can_download=False)
    assert can_download_document(user, document) is False

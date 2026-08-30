from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from cryptography.exceptions import InvalidTag

from authz import can_access_case, can_download_document, can_manage_case, share_is_active
from crypto.encryption import decrypt_file, encrypt_file
from digital_signatures import calculate_document_hash


def user(user_id, role="Police Officer", authenticated=True):
    return SimpleNamespace(id=user_id, role=role, is_authenticated=authenticated)


def test_rbac_denies_unassigned_user_and_allows_case_owner():
    owner = user(1)
    outsider = user(2)
    case = SimpleNamespace(id=10, created_by=1, assignments=[])

    assert can_access_case(owner, case) is True
    assert can_manage_case(owner, case) is True
    assert can_access_case(outsider, case) is False
    assert can_manage_case(outsider, case) is False


def test_rbac_admin_can_access_but_unauthenticated_cannot():
    case = SimpleNamespace(id=10, created_by=1, assignments=[])
    assert can_access_case(user(99, "Admin"), case) is True
    assert can_access_case(user(99, "Admin", authenticated=False), case) is False


def test_expired_share_cannot_download():
    outsider = user(2)
    owner_case = SimpleNamespace(id=10, created_by=1, assignments=[])
    share = SimpleNamespace(
        shared_with_user_id=2,
        can_view=True,
        can_download=True,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    document = SimpleNamespace(case=owner_case, shares=[share])
    assert share_is_active(share) is False
    assert can_download_document(outsider, document) is False


def test_encryption_round_trip_and_wrong_password_rejection():
    plaintext = b"synthetic legal test document"
    encrypted = encrypt_file(plaintext, "correct-password")
    assert encrypted != plaintext
    assert decrypt_file(encrypted, "correct-password") == plaintext
    with pytest.raises(InvalidTag):
        decrypt_file(encrypted, "wrong-password")


def test_encryption_tampering_is_rejected():
    encrypted = bytearray(encrypt_file(b"synthetic evidence", "password"))
    encrypted[-1] ^= 0x01
    with pytest.raises(InvalidTag):
        decrypt_file(bytes(encrypted), "password")


def test_signature_hash_changes_when_document_changes():
    first = calculate_document_hash(b"document version 1")
    second = calculate_document_hash(b"document version 2")
    assert first != second

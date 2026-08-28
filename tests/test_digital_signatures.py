from types import SimpleNamespace
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from digital_signatures import calculate_document_hash, sign_document, verify_signature
from models.digital_signature import DigitalSignature, _prevent_signature_delete, _prevent_signature_identity_change


def _record_for(data=b"phase6 document"):
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    digest = calculate_document_hash(data)
    signature = private.sign(digest.encode("ascii"))
    return SimpleNamespace(
        id=1,
        signer_name="Test Signer",
        signed_at=None,
        document_hash=digest,
        signature=signature,
        public_key=public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw),
        verification_status="UNVERIFIED",
        case_document_id=None,
        signer_id=1,
    )


def test_sha256_hash_is_deterministic():
    assert calculate_document_hash(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_valid_ed25519_signature_verifies():
    record = _record_for()
    with patch("digital_signatures.db.session.commit"):
        assert verify_signature(record, b"phase6 document") is True
    assert record.verification_status == "VALID"


def test_modified_document_fails_hash_verification():
    record = _record_for()
    with patch("digital_signatures.db.session.commit"):
        assert verify_signature(record, b"tampered document") is False
    assert record.verification_status == "INVALID"


def test_modified_signature_fails_verification():
    record = _record_for()
    record.signature = b"0" * len(record.signature)
    with patch("digital_signatures.db.session.commit"):
        assert verify_signature(record, b"phase6 document") is False
    assert record.verification_status == "INVALID"


def test_sign_document_creates_record_with_hash_and_signature():
    signer = SimpleNamespace(id=7, name="Alice")
    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    key_record = SimpleNamespace(public_key=public, encrypted_private_key=None)
    with patch("digital_signatures._get_or_create_signing_key", return_value=key_record), \
         patch("digital_signatures._decrypt_private_key", return_value=raw_private), \
         patch("digital_signatures.db.session.add"), \
         patch("digital_signatures.db.session.commit"):
        record = sign_document(b"signed bytes", signer)
    assert record.signer_id == 7
    assert record.signer_name == "Alice"
    assert record.document_hash == calculate_document_hash(b"signed bytes")
    private.public_key().verify(record.signature, record.document_hash.encode("ascii"))


def test_signed_record_identity_is_immutable():
    record = DigitalSignature()
    record.document_hash = "a" * 64
    record.signature = b"signature"
    record.public_key = b"public"
    record.signer_id = 1
    record.signer_name = "Signer"
    with pytest.raises(ValueError, match="Digital signature records are immutable"):
        record.document_hash = "b" * 64
        _prevent_signature_identity_change(None, None, record)


def test_signed_record_delete_is_blocked():
    with pytest.raises(ValueError, match="append-only"):
        _prevent_signature_delete(None, None, SimpleNamespace())

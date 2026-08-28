"""Phase 6 technical digital-signature service.

This module deliberately implements cryptographic authenticity/integrity only.
It does not establish statutory or legally recognized digital-signature status.
"""

import base64
import hashlib
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.fernet import Fernet

from extensions import db
from models.digital_signature import DigitalSignature, DigitalSigningKey


SIGNATURE_ALGORITHM = "Ed25519"
VERIFICATION_VALID = "VALID"
VERIFICATION_INVALID = "INVALID"


def _key_encryption_key():
    secret = os.getenv("SECRET_KEY", "dev-secret-key-change-this").encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(secret).digest())


def _encrypt_private_key(raw_private_key):
    return Fernet(_key_encryption_key()).encrypt(raw_private_key)


def _decrypt_private_key(encrypted_private_key):
    return Fernet(_key_encryption_key()).decrypt(encrypted_private_key)


def _get_or_create_signing_key(user):
    key_record = db.session.scalar(
        db.select(DigitalSigningKey).where(DigitalSigningKey.user_id == user.id)
    )
    if key_record is not None:
        return key_record

    private_key = Ed25519PrivateKey.generate()
    raw_private = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_record = DigitalSigningKey(
        user_id=user.id,
        public_key=raw_public,
        encrypted_private_key=_encrypt_private_key(raw_private),
    )
    db.session.add(key_record)
    db.session.flush()
    return key_record


def calculate_document_hash(document_bytes):
    """Return the SHA-256 digest that is cryptographically signed."""
    return hashlib.sha256(document_bytes).hexdigest()


def sign_document(document_bytes, signer, case_document_id=None):
    """Hash and sign document bytes, creating an immutable signed record."""
    if not document_bytes:
        raise ValueError("The document must contain data.")
    key_record = _get_or_create_signing_key(signer)
    private_key = Ed25519PrivateKey.from_private_bytes(_decrypt_private_key(key_record.encrypted_private_key))
    document_hash = calculate_document_hash(document_bytes)
    signature = private_key.sign(document_hash.encode("ascii"))
    record = DigitalSignature(
        case_document_id=case_document_id,
        signer_id=signer.id,
        signer_name=signer.name or signer.email,
        signed_at=db.func.now(),
        document_hash=document_hash,
        signature=signature,
        public_key=key_record.public_key,
        verification_status="UNVERIFIED",
    )
    db.session.add(record)
    db.session.commit()
    return record


def verify_signature(record, document_bytes):
    """Verify both the document hash and Ed25519 signature.

    The record's verification status is updated for observability; its
    cryptographic identity remains immutable.
    """
    if record is None:
        raise ValueError("Signed record not found.")
    document_hash = calculate_document_hash(document_bytes)
    if document_hash != record.document_hash:
        record.verification_status = VERIFICATION_INVALID
        db.session.commit()
        return False
    try:
        public_key = Ed25519PublicKey.from_public_bytes(record.public_key)
        public_key.verify(record.signature, record.document_hash.encode("ascii"))
    except (ValueError, TypeError, InvalidSignature):
        record.verification_status = VERIFICATION_INVALID
        db.session.commit()
        return False
    record.verification_status = VERIFICATION_VALID
    db.session.commit()
    return True


def signature_payload(record):
    """Return display-safe values without exposing private key material."""
    return {
        "id": record.id,
        "signer": record.signer_name,
        "timestamp": record.signed_at.isoformat() if record.signed_at else None,
        "document_hash": record.document_hash,
        "signature": base64.b64encode(record.signature).decode("ascii"),
        "public_key": base64.b64encode(record.public_key).decode("ascii"),
        "verification_status": record.verification_status,
        "algorithm": SIGNATURE_ALGORITHM,
    }

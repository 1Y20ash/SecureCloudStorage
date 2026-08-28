import hashlib

from audit_hooks import _sha256
from crypto.encryption import decrypt_file, encrypt_file


def test_plaintext_and_encrypted_storage_hashes_are_distinct():
    plaintext = b"synthetic legal document"
    encrypted = encrypt_file(plaintext, "test-password")

    plaintext_hash = _sha256(plaintext)
    encrypted_hash = _sha256(encrypted)

    assert plaintext_hash == hashlib.sha256(plaintext).hexdigest()
    assert encrypted_hash == hashlib.sha256(encrypted).hexdigest()
    assert encrypted_hash != plaintext_hash


def test_encrypted_storage_hash_detects_storage_tampering():
    plaintext = b"synthetic evidence record"
    encrypted = encrypt_file(plaintext, "test-password")
    expected_hash = _sha256(encrypted)

    tampered = bytearray(encrypted)
    tampered[-1] ^= 0x01

    assert _sha256(bytes(tampered)) != expected_hash


def test_plaintext_hash_is_verified_after_decryption():
    plaintext = b"synthetic witness statement"
    encrypted = encrypt_file(plaintext, "test-password")

    decrypted = decrypt_file(encrypted, "test-password")

    assert _sha256(decrypted) == _sha256(plaintext)

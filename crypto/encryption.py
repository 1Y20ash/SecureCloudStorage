import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 600_000
MAGIC = b"SCS1"


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a user password and random salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(file_bytes: bytes, password: str) -> bytes:
    """Encrypt bytes using AES-256-GCM.

    Stored format:
        magic | salt | nonce | ciphertext + authentication tag
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, file_bytes, None)
    return MAGIC + salt + nonce + ciphertext


def decrypt_file(encrypted_data: bytes, password: str) -> bytes:
    """Decrypt data produced by encrypt_file.

    Invalid passwords or modified ciphertext raise InvalidTag.
    """
    minimum_size = len(MAGIC) + SALT_SIZE + NONCE_SIZE + 16
    if len(encrypted_data) < minimum_size:
        raise ValueError("Invalid encrypted file.")

    if encrypted_data[: len(MAGIC)] != MAGIC:
        raise ValueError("Invalid encrypted file format.")

    offset = len(MAGIC)
    salt = encrypted_data[offset : offset + SALT_SIZE]
    offset += SALT_SIZE
    nonce = encrypted_data[offset : offset + NONCE_SIZE]
    offset += NONCE_SIZE
    ciphertext = encrypted_data[offset:]

    key = derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)

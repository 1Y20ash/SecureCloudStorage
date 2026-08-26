import hashlib


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_sha256(data: bytes, expected_hash: str) -> bool:
    if not expected_hash:
        return False
    return hashlib.sha256(data).hexdigest() == expected_hash

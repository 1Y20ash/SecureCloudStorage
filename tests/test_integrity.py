from integrity import sha256_bytes, verify_sha256


def test_sha256_hash_is_deterministic():
    data = b"PS 26190 synthetic document"
    digest = sha256_bytes(data)
    assert len(digest) == 64
    assert digest == sha256_bytes(data)


def test_sha256_detects_tampering():
    original = b"original evidence content"
    tampered = b"modified evidence content"
    original_hash = sha256_bytes(original)
    assert verify_sha256(original, original_hash)
    assert not verify_sha256(tampered, original_hash)


def test_empty_data_is_supported():
    digest = sha256_bytes(b"")
    assert verify_sha256(b"", digest)

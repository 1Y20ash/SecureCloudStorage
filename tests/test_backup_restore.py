import base64
import sqlite3

import pytest

from backup import create_backup, restore_backup


def _key(seed=b"0123456789abcdef0123456789abcdef"):
    return base64.urlsafe_b64encode(seed).decode("ascii")


def _create_db(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE cases (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    connection.execute("INSERT INTO cases(title) VALUES ('Synthetic FIR case')")
    connection.commit()
    connection.close()


def test_sqlite_backup_restore_round_trip(tmp_path):
    source_db = tmp_path / "source.db"
    _create_db(source_db)
    encrypted_files = tmp_path / "encrypted"
    encrypted_files.mkdir()
    (encrypted_files / "evidence.enc").write_bytes(b"synthetic encrypted evidence")

    backup = tmp_path / "backup.scsb"
    create_backup(backup, f"sqlite:///{source_db}", encrypted_files, _key())

    restored_db = tmp_path / "restored.db"
    restored_files = tmp_path / "restored-encrypted"
    result = restore_backup(backup, f"sqlite:///{restored_db}", restored_files, _key())

    assert result["restored_files"] == 1
    restored = sqlite3.connect(restored_db)
    row = restored.execute("SELECT title FROM cases").fetchone()
    restored.close()
    assert row == ("Synthetic FIR case",)
    assert (restored_files / "evidence.enc").read_bytes() == b"synthetic encrypted evidence"


def test_backup_tampering_is_rejected(tmp_path):
    source_db = tmp_path / "source.db"
    _create_db(source_db)
    backup = tmp_path / "backup.scsb"
    create_backup(backup, f"sqlite:///{source_db}", key=_key())
    data = bytearray(backup.read_bytes())
    data[-1] ^= 0x01
    backup.write_bytes(data)

    with pytest.raises(Exception):
        restore_backup(backup, f"sqlite:///{tmp_path / 'restored.db'}", key=_key())


def test_wrong_backup_key_is_rejected(tmp_path):
    source_db = tmp_path / "source.db"
    _create_db(source_db)
    backup = tmp_path / "backup.scsb"
    create_backup(backup, f"sqlite:///{source_db}", key=_key())

    with pytest.raises(Exception):
        restore_backup(backup, f"sqlite:///{tmp_path / 'restored.db'}", key=_key(b"fedcba9876543210fedcba9876543210"))


def test_backup_requires_a_real_256_bit_key(tmp_path):
    source_db = tmp_path / "source.db"
    _create_db(source_db)
    with pytest.raises(ValueError, match="32 bytes"):
        create_backup(tmp_path / "backup.scsb", f"sqlite:///{source_db}", key=_key(b"short"))


def test_restore_rejects_unknown_database_scheme(tmp_path):
    source_db = tmp_path / "source.db"
    _create_db(source_db)
    backup = tmp_path / "backup.scsb"
    create_backup(backup, f"sqlite:///{source_db}", key=_key())

    with pytest.raises(ValueError, match="only SQLite and PostgreSQL"):
        restore_backup(backup, "mysql://example.invalid/db", key=_key())


def test_restore_rejects_missing_backup(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_backup(tmp_path / "missing.scsb", f"sqlite:///{tmp_path / 'restored.db'}", key=_key())


def test_restore_rejects_malformed_container(tmp_path):
    backup = tmp_path / "malformed.scsb"
    backup.write_bytes(b"not-a-securecloudstorage-backup")

    with pytest.raises(ValueError, match="Invalid SecureCloudStorage backup"):
        restore_backup(backup, f"sqlite:///{tmp_path / 'restored.db'}", key=_key())

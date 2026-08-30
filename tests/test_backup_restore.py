import base64
import sqlite3

import pytest

from backup import create_backup, restore_backup


def _key():
    return base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode("ascii")


def test_sqlite_backup_restore_round_trip(tmp_path):
    source_db = tmp_path / "source.db"
    source = sqlite3.connect(source_db)
    source.execute("CREATE TABLE cases (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    source.execute("INSERT INTO cases(title) VALUES ('Synthetic FIR case')")
    source.commit()
    source.close()

    encrypted_files = tmp_path / "encrypted"
    encrypted_files.mkdir()
    (encrypted_files / "evidence.enc").write_bytes(b"synthetic encrypted evidence")

    backup = tmp_path / "backup.scsb"
    create_backup(
        backup,
        f"sqlite:///{source_db}",
        encrypted_files,
        _key(),
    )

    restored_db = tmp_path / "restored.db"
    restored_files = tmp_path / "restored-encrypted"
    result = restore_backup(
        backup,
        f"sqlite:///{restored_db}",
        restored_files,
        _key(),
    )

    assert result["restored_files"] == 1
    restored = sqlite3.connect(restored_db)
    row = restored.execute("SELECT title FROM cases").fetchone()
    restored.close()
    assert row == ("Synthetic FIR case",)
    assert (restored_files / "evidence.enc").read_bytes() == b"synthetic encrypted evidence"


def test_backup_tampering_is_rejected(tmp_path):
    source_db = tmp_path / "source.db"
    source = sqlite3.connect(source_db)
    source.execute("CREATE TABLE t (value TEXT)")
    source.execute("INSERT INTO t VALUES ('safe')")
    source.commit()
    source.close()

    backup = tmp_path / "backup.scsb"
    create_backup(backup, f"sqlite:///{source_db}", key=_key())
    data = bytearray(backup.read_bytes())
    data[-1] ^= 0x01
    backup.write_bytes(data)

    with pytest.raises(Exception):
        restore_backup(backup, f"sqlite:///{tmp_path / 'restored.db'}", key=_key())

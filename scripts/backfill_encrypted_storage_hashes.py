"""Backfill encrypted storage-object SHA-256 hashes for legacy files.

Run after applying migration 0006. This intentionally hashes the encrypted
bytes as stored, without changing the existing plaintext document hash.

The script adds the repository root to ``sys.path`` so it can be executed
reliably from the project root with::

    python scripts\\backfill_encrypted_storage_hashes.py
"""

import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app, read_encrypted_file
from extensions import db
from models.file import StoredFile


def main():
    updated = 0
    failed = 0

    with app.app_context():
        records = db.session.scalars(
            db.select(StoredFile)
            .where(StoredFile.encrypted_sha256_hash.is_(None))
            .order_by(StoredFile.id)
        ).all()

        for record in records:
            try:
                encrypted_data = read_encrypted_file(record.encrypted_filename)
                record.encrypted_sha256_hash = hashlib.sha256(encrypted_data).hexdigest()
                updated += 1
            except (FileNotFoundError, OSError, ValueError):
                failed += 1
                print(
                    f"FAILED: StoredFile {record.id} "
                    f"({record.encrypted_filename})"
                )

        if failed:
            db.session.rollback()
            raise RuntimeError(
                f"Backfill aborted: {failed} file(s) could not be read. "
                f"No database changes were committed."
            )

        db.session.commit()

    print(f"Backfill complete: {updated} encrypted storage hash(es) populated.")


if __name__ == "__main__":
    main()

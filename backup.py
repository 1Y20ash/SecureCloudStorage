"""Encrypted backup and restore utilities for PS-26190 Phase 9.

Backups contain the application database plus the locally stored encrypted
file objects and a SHA-256 manifest. The backup container itself is encrypted
with AES-256-GCM. The backup key is supplied separately through
BACKUP_ENCRYPTION_KEY and is never written into the repository or archive.

SQLite is supported natively. PostgreSQL uses pg_dump/pg_restore when those
open-source client utilities are available on the host.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"SCSB1\0"
NONCE_SIZE = 12
KEY_SIZE = 32


def generate_backup_key() -> str:
    """Return a URL-safe base64 AES-256 key suitable for BACKUP_ENCRYPTION_KEY."""
    return base64.urlsafe_b64encode(os.urandom(KEY_SIZE)).decode("ascii")


def _key_from_env(key: str | None = None) -> bytes:
    raw = key or os.getenv("BACKUP_ENCRYPTION_KEY")
    if not raw:
        raise RuntimeError("BACKUP_ENCRYPTION_KEY must be configured for backup/restore.")
    try:
        decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
    except Exception as exc:
        raise ValueError("BACKUP_ENCRYPTION_KEY must be URL-safe base64.") from exc
    if len(decoded) != KEY_SIZE:
        raise ValueError("BACKUP_ENCRYPTION_KEY must decode to exactly 32 bytes.")
    return decoded


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(tar: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve()
    for member in tar.getmembers():
        target = (destination / member.name).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"Unsafe archive path: {member.name}")
    tar.extractall(destination)


def _sqlite_backup(source: Path, destination: Path) -> None:
    source_conn = sqlite3.connect(str(source))
    target_conn = sqlite3.connect(str(destination))
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.close()
        source_conn.close()


def _postgres_dump(database_url: str, destination: Path) -> None:
    try:
        subprocess.run(
            ["pg_dump", "--format=custom", "--no-owner", "--file", str(destination), database_url],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pg_dump is required for PostgreSQL backups on this host.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"pg_dump failed: {exc.stderr[-1000:]}") from exc


def _postgres_restore(database_url: str, dump_path: Path) -> None:
    try:
        subprocess.run(
            ["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", database_url, str(dump_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pg_restore is required for PostgreSQL restoration on this host.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"pg_restore failed: {exc.stderr[-1000:]}") from exc


def _database_scheme(database_url: str) -> str:
    return "postgresql" if database_url.startswith(("postgresql://", "postgresql+psycopg2://")) else "sqlite"


def _sqlite_path(database_url: str, app_root: Path | None = None) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Not a SQLite database URL")
    raw = database_url[len(prefix):]
    path = Path(raw)
    if not path.is_absolute():
        path = (app_root or Path.cwd()) / path
    return path.resolve()


def create_backup(output_path: str | Path, database_url: str, encrypted_files_dir: str | Path | None = None, key: str | None = None) -> Path:
    """Create an encrypted .scsb backup and return its path."""
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="scs-backup-"))
    try:
        db_dir = temp_root / "database"
        files_dir = temp_root / "encrypted_files"
        db_dir.mkdir()
        files_dir.mkdir()

        db_scheme = _database_scheme(database_url)
        db_name = "database.sqlite3" if db_scheme == "sqlite" else "database.dump"
        db_backup = db_dir / db_name
        if db_scheme == "sqlite":
            source = _sqlite_path(database_url)
            if not source.exists():
                raise FileNotFoundError(f"Database not found: {source}")
            _sqlite_backup(source, db_backup)
        else:
            _postgres_dump(database_url, db_backup)

        manifest = {
            "format": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_type": db_scheme,
            "database_file": f"database/{db_name}",
            "files": [],
        }
        manifest["database_sha256"] = _sha256(db_backup)

        if encrypted_files_dir:
            source_dir = Path(encrypted_files_dir).resolve()
            if source_dir.exists():
                for source_file in sorted(source_dir.rglob("*")):
                    if not source_file.is_file():
                        continue
                    relative = source_file.relative_to(source_dir)
                    target = files_dir / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target)
                    manifest["files"].append({
                        "path": str(Path("encrypted_files") / relative).replace(os.sep, "/"),
                        "sha256": _sha256(source_file),
                        "size": source_file.stat().st_size,
                    })

        manifest_path = temp_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        tar_path = temp_root / "payload.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(db_dir, arcname="database")
            tar.add(files_dir, arcname="encrypted_files")
            tar.add(manifest_path, arcname="manifest.json")

        plaintext = tar_path.read_bytes()
        nonce = os.urandom(NONCE_SIZE)
        ciphertext = AESGCM(_key_from_env(key)).encrypt(nonce, plaintext, MAGIC)
        destination.write_bytes(MAGIC + nonce + ciphertext)
        return destination
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def restore_backup(backup_path: str | Path, database_url: str, encrypted_files_dir: str | Path | None = None, key: str | None = None, restore_files: bool = True) -> dict:
    """Verify and restore an encrypted backup. Returns the verified manifest."""
    source = Path(backup_path).resolve()
    raw = source.read_bytes()
    if not raw.startswith(MAGIC) or len(raw) <= len(MAGIC) + NONCE_SIZE:
        raise ValueError("Invalid SecureCloudStorage backup container.")
    nonce = raw[len(MAGIC):len(MAGIC) + NONCE_SIZE]
    ciphertext = raw[len(MAGIC) + NONCE_SIZE:]
    plaintext = AESGCM(_key_from_env(key)).decrypt(nonce, ciphertext, MAGIC)

    temp_root = Path(tempfile.mkdtemp(prefix="scs-restore-"))
    try:
        tar_path = temp_root / "payload.tar.gz"
        tar_path.write_bytes(plaintext)
        with tarfile.open(tar_path, "r:gz") as tar:
            _safe_extract(tar, temp_root / "payload")

        payload = temp_root / "payload"
        manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
        db_file = payload / manifest["database_file"]
        if _sha256(db_file) != manifest["database_sha256"]:
            raise ValueError("Backup database integrity verification failed.")

        for item in manifest.get("files", []):
            file_path = payload / item["path"]
            if not file_path.is_file() or _sha256(file_path) != item["sha256"]:
                raise ValueError(f"Backup file integrity verification failed: {item['path']}")

        target_scheme = _database_scheme(database_url)
        if target_scheme != manifest["database_type"]:
            raise ValueError("Backup database type does not match restore target.")
        if target_scheme == "sqlite":
            target = _sqlite_path(database_url)
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_target = target.with_suffix(target.suffix + ".restore")
            shutil.copy2(db_file, temp_target)
            os.replace(temp_target, target)
        else:
            _postgres_restore(database_url, db_file)

        restored_files = 0
        if restore_files and encrypted_files_dir:
            target_dir = Path(encrypted_files_dir).resolve()
            target_dir.mkdir(parents=True, exist_ok=True)
            for item in manifest.get("files", []):
                relative = Path(item["path"]).relative_to("encrypted_files")
                destination = (target_dir / relative).resolve()
                if target_dir not in destination.parents and destination != target_dir:
                    raise ValueError("Unsafe restore path")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(payload / item["path"], destination)
                restored_files += 1

        return {"manifest": manifest, "restored_files": restored_files}
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SecureCloudStorage encrypted backup utility")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("output")
    create.add_argument("--database-url", default=os.getenv("DATABASE_URL", "sqlite:///secure_cloud_storage.db"))
    create.add_argument("--encrypted-files-dir", default=os.getenv("UPLOAD_FOLDER"))
    create.add_argument("--key", default=None)
    restore = sub.add_parser("restore")
    restore.add_argument("backup")
    restore.add_argument("--database-url", required=True)
    restore.add_argument("--encrypted-files-dir", default=None)
    restore.add_argument("--key", default=None)
    args = parser.parse_args()
    if args.command == "create":
        print(create_backup(args.output, args.database_url, args.encrypted_files_dir, args.key))
    else:
        print(json.dumps(restore_backup(args.backup, args.database_url, args.encrypted_files_dir, args.key), indent=2))

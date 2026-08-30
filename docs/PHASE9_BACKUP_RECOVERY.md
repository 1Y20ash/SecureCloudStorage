# Phase 9 — Backup, Recovery & Deployment Hardening

## Scope

SecureCloudStorage backups contain the application database and encrypted document objects. Backup containers are themselves encrypted with AES-256-GCM and authenticated with a SHA-256 manifest.

The backup key is separate from the application `SECRET_KEY` and must never be committed to Git.

## Required environment

```text
BACKUP_ENCRYPTION_KEY=<URL-safe-base64 encoding of exactly 32 random bytes>
```

Generate a key locally:

```bash
python backup.py --help
python -c "from backup import generate_backup_key; print(generate_backup_key())"
```

Store the resulting value only in the deployment secret manager/environment.

## Create a backup

SQLite/local encrypted-file deployment:

```bash
python backup.py create backups/securecloudstorage.scsb --database-url sqlite:///secure_cloud_storage.db --encrypted-files-dir uploads/encrypted
```

PostgreSQL deployment:

```bash
python backup.py create backups/securecloudstorage.scsb --database-url "$DATABASE_URL" --encrypted-files-dir uploads/encrypted
```

PostgreSQL hosts require the open-source `pg_dump` utility. No paid backup service is required.

## Restore

Restore to a separate/test target first:

```bash
python backup.py restore backups/securecloudstorage.scsb --database-url sqlite:///restored.db --encrypted-files-dir restored-encrypted
```

For PostgreSQL, use a dedicated empty/test database URL. `pg_restore` is required.

The restore process:

1. Authenticates and decrypts the backup container.
2. Rejects malformed containers.
3. Rejects path traversal archive members.
4. Verifies the database SHA-256 digest.
5. Verifies every backed-up encrypted file SHA-256 digest.
6. Restores the database.
7. Restores encrypted document objects.

A failed integrity check aborts restoration before the affected content is installed.

## Recovery policy

- Keep the backup encryption key separately from backup files.
- Never commit `.scsb` backups or backup keys to Git.
- Prefer restoring to a staging/test database before production.
- Preserve the original production database until the restore is verified.
- Record the restore date, backup identifier, database target, verification result and operator in the deployment log.

## Storage strategy

The application stores already-encrypted document objects. Local deployments include `uploads/encrypted` in the backup. If production uses an external object store such as Supabase Storage, its encrypted objects must also be exported into the backup file set or covered by a provider-native free export/snapshot procedure before a production restore is considered complete.

The database backup and file backup must be treated as a pair; restoring only the database can leave document metadata pointing at unavailable objects.

## Restoration test

The automated test `tests/test_backup_restore.py` creates a synthetic SQLite database and synthetic encrypted evidence file, creates an encrypted backup, restores it into a separate database/file directory, and verifies the restored content. It also mutates the backup and verifies that authenticated decryption rejects the tampered container.

This satisfies the PDP requirement that backup is not considered complete without a tested restoration path. A production deployment still requires a deployment-level restore drill using its actual PostgreSQL/object-storage configuration.

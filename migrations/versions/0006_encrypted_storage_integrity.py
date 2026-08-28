"""Add encrypted storage integrity hashes.

Revision ID: 0006_encrypted_storage_integrity
Revises: 0005_evidentiary_integrity
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_encrypted_storage_integrity"
down_revision = "0005_evidentiary_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stored_files",
        sa.Column("encrypted_sha256_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_stored_files_encrypted_sha256_hash",
        "stored_files",
        ["encrypted_sha256_hash"],
    )


def downgrade():
    op.drop_index(
        "ix_stored_files_encrypted_sha256_hash",
        table_name="stored_files",
    )
    op.drop_column("stored_files", "encrypted_sha256_hash")

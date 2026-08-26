"""Add document lifecycle metadata to document versions.

Revision ID: 0007_document_lifecycle
Revises: 0006_encrypted_storage_integrity
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_document_lifecycle"
down_revision = "0006_encrypted_storage_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "document_versions",
        sa.Column("change_description", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "document_versions",
        sa.Column(
            "lifecycle_status",
            sa.String(length=20),
            nullable=False,
            server_default="Draft",
        ),
    )
    op.create_index(
        "ix_document_versions_lifecycle_status",
        "document_versions",
        ["lifecycle_status"],
    )


def downgrade():
    op.drop_index(
        "ix_document_versions_lifecycle_status",
        table_name="document_versions",
    )
    op.drop_column("document_versions", "lifecycle_status")
    op.drop_column("document_versions", "change_description")

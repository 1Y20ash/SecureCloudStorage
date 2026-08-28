"""Add RBAC roles and document sharing.

Revision ID: 0002_rbac_and_sharing
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_rbac_and_sharing"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("role", sa.String(length=40), nullable=False, server_default="Police Officer"),
    )
    op.create_index("ix_user_role", "user", ["role"], unique=False)

    op.create_table(
        "document_shares",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_document_id", sa.Integer(), nullable=False),
        sa.Column("shared_with_user_id", sa.Integer(), nullable=False),
        sa.Column("shared_by_user_id", sa.Integer(), nullable=False),
        sa.Column("can_view", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_download", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_document_id"], ["case_documents.id"]),
        sa.ForeignKeyConstraint(["shared_with_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["shared_by_user_id"], ["user.id"]),
        sa.UniqueConstraint(
            "case_document_id",
            "shared_with_user_id",
            name="uq_document_share_recipient",
        ),
    )
    op.create_index("ix_document_shares_case_document_id", "document_shares", ["case_document_id"])
    op.create_index("ix_document_shares_shared_with_user_id", "document_shares", ["shared_with_user_id"])
    op.create_index("ix_document_shares_shared_by_user_id", "document_shares", ["shared_by_user_id"])


def downgrade():
    op.drop_index("ix_document_shares_shared_by_user_id", table_name="document_shares")
    op.drop_index("ix_document_shares_shared_with_user_id", table_name="document_shares")
    op.drop_index("ix_document_shares_case_document_id", table_name="document_shares")
    op.drop_table("document_shares")
    op.drop_index("ix_user_role", table_name="user")
    op.drop_column("user", "role")

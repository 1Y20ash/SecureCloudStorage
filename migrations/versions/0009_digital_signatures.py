"""Add Phase 6 digital signature records and signing keys.

Revision ID: 0009_digital_signatures
Revises: 0008_evidence_management
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_digital_signatures"
down_revision = "0008_evidence_management"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_signing_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("encrypted_private_key", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_digital_signing_keys_user_id"),
    )

    op.create_table(
        "digital_signatures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_document_id", sa.Integer(), nullable=True),
        sa.Column("signer_id", sa.Integer(), nullable=True),
        sa.Column("signer_name", sa.String(length=255), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_hash", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.LargeBinary(), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False, server_default="UNVERIFIED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_document_id"], ["case_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["signer_id"], ["user.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_digital_signatures_case_document_id", "digital_signatures", ["case_document_id"])
    op.create_index("ix_digital_signatures_signer_id", "digital_signatures", ["signer_id"])
    op.create_index("ix_digital_signatures_signed_at", "digital_signatures", ["signed_at"])
    op.create_index("ix_digital_signatures_document_hash", "digital_signatures", ["document_hash"])
    op.create_index("ix_digital_signatures_verification_status", "digital_signatures", ["verification_status"])


def downgrade():
    for name in (
        "ix_digital_signatures_verification_status",
        "ix_digital_signatures_document_hash",
        "ix_digital_signatures_signed_at",
        "ix_digital_signatures_signer_id",
        "ix_digital_signatures_case_document_id",
    ):
        op.drop_index(name, table_name="digital_signatures")
    op.drop_table("digital_signatures")
    op.drop_table("digital_signing_keys")

"""Add document version history and evidence chain of custody.

Revision ID: 0005_evidentiary_integrity
Revises: 0004_audit_integrity
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_evidentiary_integrity"
down_revision = "0004_audit_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_document_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stored_file_id", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_document_id"], ["case_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stored_file_id"], ["stored_files.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("case_document_id", "version", name="uq_document_version"),
    )
    for name, column in (
        ("ix_document_versions_case_document_id", "case_document_id"),
        ("ix_document_versions_stored_file_id", "stored_file_id"),
        ("ix_document_versions_sha256_hash", "sha256_hash"),
        ("ix_document_versions_created_by", "created_by"),
        ("ix_document_versions_created_at", "created_at"),
    ):
        op.create_index(name, "document_versions", [column])

    op.create_table(
        "evidence_custody",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_document_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("from_user_id", sa.Integer(), nullable=True),
        sa.Column("to_user_id", sa.Integer(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_document_id"], ["case_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_user_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_user_id"], ["user.id"], ondelete="SET NULL"),
    )
    for name, column in (
        ("ix_evidence_custody_case_document_id", "case_document_id"),
        ("ix_evidence_custody_action", "action"),
        ("ix_evidence_custody_actor_user_id", "actor_user_id"),
        ("ix_evidence_custody_sha256_hash", "sha256_hash"),
        ("ix_evidence_custody_occurred_at", "occurred_at"),
    ):
        op.create_index(name, "evidence_custody", [column])


def downgrade():
    for name in (
        "ix_evidence_custody_occurred_at",
        "ix_evidence_custody_sha256_hash",
        "ix_evidence_custody_actor_user_id",
        "ix_evidence_custody_action",
        "ix_evidence_custody_case_document_id",
    ):
        op.drop_index(name, table_name="evidence_custody")
    op.drop_table("evidence_custody")
    for name in (
        "ix_document_versions_created_at",
        "ix_document_versions_created_by",
        "ix_document_versions_sha256_hash",
        "ix_document_versions_stored_file_id",
        "ix_document_versions_case_document_id",
    ):
        op.drop_index(name, table_name="document_versions")
    op.drop_table("document_versions")

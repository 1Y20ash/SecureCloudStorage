"""Add investigation evidence records and evidence custody linkage.

Revision ID: 0008_evidence_management
Revises: 0007_document_lifecycle
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_evidence_management"
down_revision = "0007_document_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evidence_id", sa.String(length=40), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("evidence_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("collected_by", sa.Integer(), nullable=True),
        sa.Column("collection_location", sa.String(length=255), nullable=True),
        sa.Column("collection_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_holder", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Collected"),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("stored_file_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collected_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["current_holder"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["stored_file_id"], ["stored_files.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("evidence_id", name="uq_evidence_evidence_id"),
    )
    for name, column in (
        ("ix_evidence_evidence_id", "evidence_id"),
        ("ix_evidence_case_id", "case_id"),
        ("ix_evidence_evidence_type", "evidence_type"),
        ("ix_evidence_collected_by", "collected_by"),
        ("ix_evidence_collection_datetime", "collection_datetime"),
        ("ix_evidence_current_holder", "current_holder"),
        ("ix_evidence_status", "status"),
        ("ix_evidence_sha256_hash", "sha256_hash"),
        ("ix_evidence_stored_file_id", "stored_file_id"),
    ):
        op.create_index(name, "evidence", [column])

    with op.batch_alter_table("evidence_custody") as batch_op:
        batch_op.alter_column("case_document_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("evidence_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_evidence_custody_evidence_id",
            "evidence",
            ["evidence_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_evidence_custody_evidence_id", ["evidence_id"])


def downgrade():
    with op.batch_alter_table("evidence_custody") as batch_op:
        batch_op.drop_index("ix_evidence_custody_evidence_id")
        batch_op.drop_constraint("fk_evidence_custody_evidence_id", type_="foreignkey")
        batch_op.drop_column("evidence_id")
        batch_op.alter_column("case_document_id", existing_type=sa.Integer(), nullable=False)

    for name in (
        "ix_evidence_stored_file_id",
        "ix_evidence_sha256_hash",
        "ix_evidence_status",
        "ix_evidence_current_holder",
        "ix_evidence_collection_datetime",
        "ix_evidence_collected_by",
        "ix_evidence_evidence_type",
        "ix_evidence_case_id",
        "ix_evidence_evidence_id",
    ):
        op.drop_index(name, table_name="evidence")
    op.drop_table("evidence")

"""Add evidence records and evidence-specific chain-of-custody events.

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
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("evidence_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("collected_by", sa.Integer(), nullable=True),
        sa.Column("collection_location", sa.String(length=255), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_holder", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="Collected"),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collected_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["current_holder"], ["user.id"], ondelete="SET NULL"),
    )
    for name, column in (
        ("ix_evidence_case_id", "case_id"),
        ("ix_evidence_evidence_type", "evidence_type"),
        ("ix_evidence_collected_by", "collected_by"),
        ("ix_evidence_collected_at", "collected_at"),
        ("ix_evidence_current_holder", "current_holder"),
        ("ix_evidence_status", "status"),
        ("ix_evidence_sha256_hash", "sha256_hash"),
        ("ix_evidence_created_at", "created_at"),
    ):
        op.create_index(name, "evidence", [column])

    op.create_table(
        "evidence_custody_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("from_user_id", sa.Integer(), nullable=True),
        sa.Column("to_user_id", sa.Integer(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_user_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_user_id"], ["user.id"], ondelete="SET NULL"),
    )
    for name, column in (
        ("ix_evidence_custody_events_evidence_id", "evidence_id"),
        ("ix_evidence_custody_events_action", "action"),
        ("ix_evidence_custody_events_actor_user_id", "actor_user_id"),
        ("ix_evidence_custody_events_sha256_hash", "sha256_hash"),
        ("ix_evidence_custody_events_occurred_at", "occurred_at"),
    ):
        op.create_index(name, "evidence_custody_events", [column])


def downgrade():
    for name in (
        "ix_evidence_custody_events_occurred_at",
        "ix_evidence_custody_events_sha256_hash",
        "ix_evidence_custody_events_actor_user_id",
        "ix_evidence_custody_events_action",
        "ix_evidence_custody_events_evidence_id",
    ):
        op.drop_index(name, table_name="evidence_custody_events")
    op.drop_table("evidence_custody_events")

    for name in (
        "ix_evidence_created_at",
        "ix_evidence_sha256_hash",
        "ix_evidence_status",
        "ix_evidence_current_holder",
        "ix_evidence_collected_at",
        "ix_evidence_collected_by",
        "ix_evidence_evidence_type",
        "ix_evidence_case_id",
    ):
        op.drop_index(name, table_name="evidence")
    op.drop_table("evidence")

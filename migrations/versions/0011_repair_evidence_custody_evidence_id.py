"""Repair evidence custody schema drift for evidence_id.

Revision ID: 0011_repair_evidence_custody_evidence_id
Revises: 0010_ocr_documents

Migration 0008 defines evidence_custody.evidence_id, but a database that was
previously stamped at a later revision can still have the old physical schema.
This repair migration makes the expected column, foreign key, and index
explicitly reproducible while remaining safe for databases where they already
exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0011_repair_evidence_custody_evidence_id"
down_revision = "0010_ocr_documents"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("evidence_custody")}

    if "evidence_id" not in columns:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.add_column(sa.Column("evidence_id", sa.Integer(), nullable=True))

    foreign_keys = inspector.get_foreign_keys("evidence_custody")
    fk_names = {fk.get("name") for fk in foreign_keys}
    indexes = inspector.get_indexes("evidence_custody")
    index_names = {index.get("name") for index in indexes}

    if "fk_evidence_custody_evidence_id" not in fk_names:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.create_foreign_key(
                "fk_evidence_custody_evidence_id",
                "evidence",
                ["evidence_id"],
                ["id"],
                ondelete="CASCADE",
            )

    if "ix_evidence_custody_evidence_id" not in index_names:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.create_index("ix_evidence_custody_evidence_id", ["evidence_id"])


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("evidence_custody")}
    foreign_keys = inspector.get_foreign_keys("evidence_custody")
    fk_names = {fk.get("name") for fk in foreign_keys}
    indexes = inspector.get_indexes("evidence_custody")
    index_names = {index.get("name") for index in indexes}

    if "ix_evidence_custody_evidence_id" in index_names:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.drop_index("ix_evidence_custody_evidence_id")

    if "fk_evidence_custody_evidence_id" in fk_names:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.drop_constraint("fk_evidence_custody_evidence_id", type_="foreignkey")

    if "evidence_id" in columns:
        with op.batch_alter_table("evidence_custody") as batch_op:
            batch_op.drop_column("evidence_id")

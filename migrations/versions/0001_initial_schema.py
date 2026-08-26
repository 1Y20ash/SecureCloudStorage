"""Create the current SecureCloudStorage schema under Alembic control.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-26

The migration is intentionally idempotent for existing installations: tables
already created by the Phase 1 db.create_all() bootstrap are left untouched.
New installations receive the same schema through Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables():
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing = _tables()

    if "user" not in existing:
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=120), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_user_email", "user", ["email"], unique=True)

    existing = _tables()
    if "stored_files" not in existing:
        op.create_table(
            "stored_files",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("encrypted_filename", sa.String(length=255), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("encrypted_filename"),
        )
        op.create_index("ix_stored_files_user_id", "stored_files", ["user_id"], unique=False)

    existing = _tables()
    if "cases" not in existing:
        op.create_table(
            "cases",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("case_number", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("department", sa.String(length=150), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("case_number"),
        )
        op.create_index("ix_cases_case_number", "cases", ["case_number"], unique=True)
        op.create_index("ix_cases_created_by", "cases", ["created_by"], unique=False)

    existing = _tables()
    if "case_documents" not in existing:
        op.create_table(
            "case_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("stored_file_id", sa.Integer(), nullable=False),
            sa.Column("category", sa.String(length=80), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
            sa.ForeignKeyConstraint(["stored_file_id"], ["stored_files.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stored_file_id"),
        )
        op.create_index("ix_case_documents_case_id", "case_documents", ["case_id"], unique=False)
        op.create_index("ix_case_documents_stored_file_id", "case_documents", ["stored_file_id"], unique=True)


def downgrade() -> None:
    existing = _tables()
    if "case_documents" in existing:
        op.drop_table("case_documents")
    existing = _tables()
    if "cases" in existing:
        op.drop_table("cases")
    existing = _tables()
    if "stored_files" in existing:
        op.drop_table("stored_files")
    existing = _tables()
    if "user" in existing:
        op.drop_table("user")

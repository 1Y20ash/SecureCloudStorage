"""Add Phase 7 OCR extraction metadata.

Revision ID: 0010_ocr_documents
Revises: 0009_digital_signatures
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_ocr_documents"
down_revision = "0009_digital_signatures"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ocr_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_document_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("engine", sa.String(length=32), nullable=False, server_default="tesseract"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_document_id"], ["case_documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_document_id", name="uq_ocr_documents_case_document_id"),
    )
    op.create_index("ix_ocr_documents_source_sha256", "ocr_documents", ["source_sha256"])
    op.create_index("ix_ocr_documents_status", "ocr_documents", ["status"])


def downgrade():
    op.drop_index("ix_ocr_documents_status", table_name="ocr_documents")
    op.drop_index("ix_ocr_documents_source_sha256", table_name="ocr_documents")
    op.drop_table("ocr_documents")

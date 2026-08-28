"""Persistent OCR extraction metadata for Phase 7.

The original encrypted document is never replaced by OCR output. Extracted text
is a derived search artifact and is always tied to the SHA-256 hash of the
source document that produced it.
"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db


class OCRDocument(db.Model):
    __tablename__ = "ocr_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_document_id: Mapped[int] = mapped_column(
        ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    engine: Mapped[str] = mapped_column(String(32), nullable=False, default="tesseract")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ocr_documents_source_sha256", "source_sha256"),
        Index("ix_ocr_documents_status", "status"),
    )

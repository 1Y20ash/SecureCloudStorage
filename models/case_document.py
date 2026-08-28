from datetime import datetime, timezone

from extensions import db


class CaseDocument(db.Model):
    __tablename__ = "case_documents"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False, index=True)
    stored_file_id = db.Column(
        db.Integer,
        db.ForeignKey("stored_files.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    category = db.Column(db.String(80), nullable=False, default="Other")
    version = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(40), nullable=False, default="Draft")
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", back_populates="documents")
    stored_file = db.relationship("StoredFile", backref=db.backref("case_document", uselist=False))
    ocr_document = db.relationship(
        "OCRDocument", back_populates="case_document", uselist=False, cascade="all, delete-orphan"
    )

from datetime import datetime, timezone

from extensions import db


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"
    __table_args__ = (
        db.UniqueConstraint("case_document_id", "version", name="uq_document_version"),
    )

    id = db.Column(db.Integer, primary_key=True)
    case_document_id = db.Column(
        db.Integer, db.ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version = db.Column(db.Integer, nullable=False)
    stored_file_id = db.Column(
        db.Integer, db.ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    case_document = db.relationship("CaseDocument", backref=db.backref("versions", lazy=True, order_by="DocumentVersion.version"))
    stored_file = db.relationship("StoredFile", backref=db.backref("document_versions", lazy=True))
    creator = db.relationship("User", backref=db.backref("document_versions", lazy=True))

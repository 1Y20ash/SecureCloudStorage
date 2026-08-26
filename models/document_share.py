from datetime import datetime, timezone

from extensions import db


class DocumentShare(db.Model):
    __tablename__ = "document_shares"

    id = db.Column(db.Integer, primary_key=True)
    case_document_id = db.Column(
        db.Integer,
        db.ForeignKey("case_documents.id"),
        nullable=False,
        index=True,
    )
    shared_with_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    shared_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    can_view = db.Column(db.Boolean, nullable=False, default=True)
    can_download = db.Column(db.Boolean, nullable=False, default=False)
    can_manage = db.Column(db.Boolean, nullable=False, default=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case_document = db.relationship(
        "CaseDocument",
        backref=db.backref("shares", lazy=True, cascade="all, delete-orphan"),
    )
    shared_with = db.relationship(
        "User",
        foreign_keys=[shared_with_user_id],
        backref=db.backref("document_shares_received", lazy=True),
    )
    shared_by = db.relationship(
        "User",
        foreign_keys=[shared_by_user_id],
        backref=db.backref("document_shares_created", lazy=True),
    )

from datetime import datetime, timezone

from extensions import db


class EvidenceCustody(db.Model):
    __tablename__ = "evidence_custody"

    id = db.Column(db.Integer, primary_key=True)
    case_document_id = db.Column(
        db.Integer, db.ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action = db.Column(db.String(40), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    notes = db.Column(db.String(500), nullable=True)
    occurred_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    case_document = db.relationship("CaseDocument", backref=db.backref("custody_events", lazy=True, order_by="EvidenceCustody.occurred_at"))
    actor = db.relationship("User", foreign_keys=[actor_user_id])
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

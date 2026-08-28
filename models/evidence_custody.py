from datetime import datetime, timezone

from extensions import db
from models.evidence import Evidence
from sqlalchemy import event


class EvidenceCustody(db.Model):
    """Append-only custody event record for documents and investigation evidence."""

    __tablename__ = "evidence_custody"

    id = db.Column(db.Integer, primary_key=True)
    # Retained for Phase 3/4 document custody compatibility.
    case_document_id = db.Column(
        db.Integer, db.ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    evidence_id = db.Column(
        db.Integer, db.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=True, index=True
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
    evidence = db.relationship("Evidence", back_populates="custody_events", foreign_keys=[evidence_id])
    actor = db.relationship("User", foreign_keys=[actor_user_id])
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])


@event.listens_for(EvidenceCustody, "before_update")
def _prevent_custody_event_update(mapper, connection, target):
    """Custody history is immutable once written; corrections require a new event."""
    raise ValueError("Evidence custody events are append-only and cannot be updated")


@event.listens_for(EvidenceCustody, "before_delete")
def _prevent_custody_event_delete(mapper, connection, target):
    """Prevent application-level deletion of custody history."""
    raise ValueError("Evidence custody events are append-only and cannot be deleted")

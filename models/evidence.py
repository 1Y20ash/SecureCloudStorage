from datetime import datetime, timezone

from extensions import db
from sqlalchemy import event, inspect


class Evidence(db.Model):
    """Investigation evidence record with immutable identity and current custody state."""

    __tablename__ = "evidence"

    STATUS_COLLECTED = "Collected"
    STATUS_UPLOADED = "Uploaded"
    STATUS_TRANSFERRED = "Transferred"
    STATUS_EXAMINED = "Examined"
    STATUS_STORED = "Stored"
    STATUS_PRESENTED = "Presented"
    STATUSES = (
        STATUS_COLLECTED,
        STATUS_UPLOADED,
        STATUS_TRANSFERRED,
        STATUS_EXAMINED,
        STATUS_STORED,
        STATUS_PRESENTED,
    )

    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.String(40), unique=True, nullable=False, index=True)
    case_id = db.Column(
        db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    collected_by = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    collection_location = db.Column(db.String(255), nullable=True)
    collection_datetime = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    current_holder = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = db.Column(db.String(20), nullable=False, default=STATUS_COLLECTED, index=True)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    stored_file_id = db.Column(
        db.Integer, db.ForeignKey("stored_files.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    case = db.relationship("Case", backref=db.backref("evidence_items", lazy=True))
    collector = db.relationship("User", foreign_keys=[collected_by])
    holder = db.relationship("User", foreign_keys=[current_holder])
    stored_file = db.relationship("StoredFile", backref=db.backref("evidence_item", uselist=False))
    custody_events = db.relationship(
        "EvidenceCustody",
        back_populates="evidence",
        foreign_keys="EvidenceCustody.evidence_id",
        order_by="EvidenceCustody.occurred_at",
        lazy=True,
        cascade="all, delete-orphan",
    )


@event.listens_for(Evidence, "before_update")
def _prevent_evidence_identity_change(mapper, connection, target):
    """Evidence identity and its recorded integrity hash cannot be rewritten."""
    history = inspect(target)

    if history.attrs.evidence_id.history.has_changes():
        raise ValueError("Evidence identifiers are immutable")

    if history.attrs.sha256_hash.history.has_changes():
        raise ValueError("SHA-256 hashes are immutable")
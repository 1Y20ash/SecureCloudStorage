from datetime import datetime, timezone

from extensions import db


class Evidence(db.Model):
    __tablename__ = "evidence"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(
        db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    collected_by = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    collection_location = db.Column(db.String(255), nullable=True)
    collected_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    current_holder = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = db.Column(db.String(30), nullable=False, default="Collected", index=True)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    case = db.relationship("Case", backref=db.backref("evidence_items", lazy=True, cascade="all, delete-orphan"))
    collector = db.relationship("User", foreign_keys=[collected_by])
    holder = db.relationship("User", foreign_keys=[current_holder])
    custody_events = db.relationship(
        "EvidenceCustodyEvent",
        back_populates="evidence",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="EvidenceCustodyEvent.occurred_at",
    )

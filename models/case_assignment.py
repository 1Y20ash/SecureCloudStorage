from datetime import datetime, timezone

from extensions import db


class CaseAssignment(db.Model):
    __tablename__ = "case_assignments"
    __table_args__ = (
        db.UniqueConstraint("case_id", "user_id", name="uq_case_assignment"),
    )

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    assigned_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", backref=db.backref("assignments", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("case_assignments", lazy=True))
    assigner = db.relationship("User", foreign_keys=[assigned_by])

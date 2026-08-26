from datetime import datetime, timezone

from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    resource_type = db.Column(db.String(40), nullable=False, index=True)
    resource_id = db.Column(db.Integer, nullable=True, index=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    success = db.Column(db.Boolean, nullable=False, default=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = db.relationship("User", backref=db.backref("audit_logs", lazy=True))
    case = db.relationship("Case", backref=db.backref("audit_logs", lazy=True))

from datetime import datetime, timezone

from extensions import db


class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    department = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="Open")
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    creator = db.relationship("User", backref=db.backref("cases_created", lazy=True))
    documents = db.relationship(
        "CaseDocument",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy=True,
    )

from datetime import datetime, timezone

from extensions import db


class StoredFile(db.Model):
    __tablename__ = "stored_files"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    encrypted_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    # SHA-256 of the original plaintext document.
    sha256_hash = db.Column(db.String(64), nullable=True, index=True)
    # SHA-256 of the exact encrypted bytes persisted in storage.
    encrypted_sha256_hash = db.Column(db.String(64), nullable=True, index=True)
    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("stored_files", lazy=True))

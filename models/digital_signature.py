"""Database models for the Phase 6 digital-signature prototype."""

from datetime import datetime, timezone

from sqlalchemy import event, inspect

from extensions import db


class DigitalSigningKey(db.Model):
    """Per-user Ed25519 key pair with the private key encrypted at rest."""

    __tablename__ = "digital_signing_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    public_key = db.Column(db.LargeBinary, nullable=False)
    encrypted_private_key = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = db.relationship("User", backref=db.backref("digital_signing_key", uselist=False))


class DigitalSignature(db.Model):
    """Immutable technical signature record for a document byte sequence."""

    __tablename__ = "digital_signatures"

    id = db.Column(db.Integer, primary_key=True)
    case_document_id = db.Column(
        db.Integer, db.ForeignKey("case_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    signer_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    signer_name = db.Column(db.String(255), nullable=False)
    signed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    document_hash = db.Column(db.String(64), nullable=False, index=True)
    signature = db.Column(db.LargeBinary, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    verification_status = db.Column(db.String(20), nullable=False, default="UNVERIFIED", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    case_document = db.relationship("CaseDocument", backref=db.backref("digital_signatures", lazy=True))
    signer = db.relationship("User", foreign_keys=[signer_id])


@event.listens_for(DigitalSigningKey, "before_update")
def _prevent_signing_key_change(mapper, connection, target):
    """Signing key material is fixed for the life of the key record."""
    history = inspect(target)
    for field in ("user_id", "public_key", "encrypted_private_key", "created_at"):
        if history.attrs[field].history.has_changes():
            raise ValueError("Digital signing keys are immutable")


@event.listens_for(DigitalSigningKey, "before_delete")
def _prevent_signing_key_delete(mapper, connection, target):
    """Do not silently destroy the key that authenticates existing signatures."""
    raise ValueError("Digital signing keys are append-only")


@event.listens_for(DigitalSignature, "before_update")
def _prevent_signature_identity_change(mapper, connection, target):
    """A signed record's cryptographic identity cannot be rewritten."""
    history = inspect(target)
    immutable = ("signer_id", "signer_name", "signed_at", "document_hash", "signature", "public_key")
    for field in immutable:
        if history.attrs[field].history.has_changes():
            raise ValueError("Digital signature records are immutable")


@event.listens_for(DigitalSignature, "before_delete")
def _prevent_signature_delete(mapper, connection, target):
    """Signed records are append-only; retain the forensic record."""
    raise ValueError("Digital signature records are append-only")

"""Phase 3 audit, integrity and security-event hooks.

This module contains two kinds of protection:
1. SQLAlchemy mutation auditing, registered at import time.
2. Flask request hooks for download integrity and request-level audit events.

The Flask hooks are registered lazily when the application's context is first
pushed. This keeps the model import cycle safe while ensuring the hooks are
actually attached to the running Flask application.
"""

import hashlib
import os

from flask import appcontext_pushed, flash, g, has_request_context, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from config import Config
from crypto.encryption import decrypt_file
from extensions import db
from models.audit_log import AuditLog
from models.case import Case
from models.case_document import CaseDocument
from models.case_assignment import CaseAssignment
from models.document_share import DocumentShare
from models.file import StoredFile
from models.user import User

AUDITED_MODELS = (Case, CaseDocument, CaseAssignment, DocumentShare, StoredFile, User)


def _request_user_id():
    if has_request_context() and getattr(current_user, "is_authenticated", False):
        return current_user.id
    return None


def _ip_address():
    if not has_request_context():
        return None
    # Do not blindly trust arbitrary X-Forwarded-For values. A deployment can
    # explicitly enable proxy trust through TRUST_PROXY_HEADERS.
    if Config.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.remote_addr


def _resource_case_id(target):
    if isinstance(target, Case):
        return target.id
    if isinstance(target, CaseDocument):
        return target.case_id
    if isinstance(target, CaseAssignment):
        return target.case_id
    if isinstance(target, DocumentShare):
        return target.case_document.case_id if target.case_document else None
    if isinstance(target, StoredFile):
        return target.case_document.case_id if target.case_document else None
    return None


def _record(session, action, target, success=True, details=None):
    session.add(AuditLog(
        user_id=_request_user_id(),
        action=action,
        resource_type=target.__class__.__name__ if target is not None else "REQUEST",
        resource_id=getattr(target, "id", None),
        case_id=_resource_case_id(target) if target is not None else None,
        success=success,
        ip_address=_ip_address(),
        details=(details or "")[:500] or None,
    ))


@event.listens_for(Session, "before_flush")
def audit_model_mutations(session, flush_context, instances):
    for target in list(session.new):
        if isinstance(target, AUDITED_MODELS):
            _record(session, "CREATE", target)
    for target in list(session.dirty):
        if isinstance(target, AUDITED_MODELS) and session.is_modified(target, include_collections=False):
            _record(session, "UPDATE", target)
    for target in list(session.deleted):
        if isinstance(target, AUDITED_MODELS):
            _record(session, "DELETE", target)


def _storage_bytes(filename):
    supabase_url = Config.SUPABASE_URL
    supabase_key = Config.SUPABASE_SECRET_KEY
    bucket = Config.SUPABASE_STORAGE_BUCKET or "encrypted-files"
    if supabase_url and supabase_key:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        return client.storage.from_(bucket).download(filename)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "encrypted", filename)
    with open(path, "rb") as encrypted_file:
        return encrypted_file.read()


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _write_integrity_failure(file_record, expected, actual, check_type="encrypted storage"):
    db.session.add(AuditLog(
        user_id=_request_user_id(),
        action="INTEGRITY_FAILURE",
        resource_type="StoredFile",
        resource_id=file_record.id,
        case_id=file_record.case_document.case_id if file_record.case_document else None,
        success=False,
        ip_address=_ip_address(),
        details=f"{check_type} SHA-256 mismatch: expected {expected}, received {actual}"[:500],
    ))
    db.session.commit()


def _verify_download_integrity():
    if request.endpoint != "download" or request.method != "POST":
        return None
    file_id = request.view_args.get("file_id") if request.view_args else None
    if not file_id or not current_user.is_authenticated:
        return None

    stored_file = db.session.get(StoredFile, file_id)
    if stored_file is None or not stored_file.encrypted_sha256_hash:
        # Legacy records without the new storage-object hash are handled by the
        # migration/backfill process rather than silently claiming integrity.
        return None

    from authz import can_download_document
    document = stored_file.case_document
    if document is None or not can_download_document(current_user, document):
        return None

    try:
        encrypted_data = _storage_bytes(stored_file.encrypted_filename)
        actual_encrypted_hash = _sha256(encrypted_data)
    except (FileNotFoundError, OSError, ValueError):
        _write_integrity_failure(
            stored_file,
            stored_file.encrypted_sha256_hash,
            "MISSING_OR_UNREADABLE",
        )
        flash("Document integrity could not be verified. Download blocked.", "error")
        return redirect(url_for("dashboard"))

    if actual_encrypted_hash != stored_file.encrypted_sha256_hash:
        _write_integrity_failure(
            stored_file,
            stored_file.encrypted_sha256_hash,
            actual_encrypted_hash,
        )
        flash("Document integrity verification failed. Download blocked.", "error")
        return redirect(url_for("dashboard"))

    # Do not decrypt twice. The download view performs the password-based
    # decryption. This hook verifies the immutable encrypted storage object
    # before the password is consumed by the view.
    return None


def _backfill_encrypted_storage_hash(response):
    """Populate encrypted_sha256_hash for newly created storage objects."""
    if request.endpoint not in ("upload", "create_document_version"):
        return
    if request.method != "POST" or response.status_code not in (302, 303):
        return
    if not getattr(current_user, "is_authenticated", False):
        return

    uploaded = request.files.get("file")
    filename = secure_filename(uploaded.filename) if uploaded else ""
    if not filename:
        return

    if request.endpoint == "upload":
        case_id = request.form.get("case_id", type=int)
        if not case_id:
            return
        document = db.session.scalar(
            db.select(CaseDocument)
            .join(StoredFile, StoredFile.id == CaseDocument.stored_file_id)
            .where(
                CaseDocument.case_id == case_id,
                StoredFile.user_id == current_user.id,
                StoredFile.original_filename == filename,
            )
            .order_by(StoredFile.uploaded_at.desc())
        )
    else:
        document_id = request.view_args.get("document_id") if request.view_args else None
        document = db.session.get(CaseDocument, document_id) if document_id else None

    if document is None or document.stored_file.encrypted_sha256_hash:
        return

    try:
        encrypted_data = _storage_bytes(document.stored_file.encrypted_filename)
        document.stored_file.encrypted_sha256_hash = _sha256(encrypted_data)
        db.session.commit()
    except (FileNotFoundError, OSError, ValueError):
        db.session.rollback()


EVENT_MAP = {
    ("login", "POST"): "LOGIN",
    ("logout", "GET"): "LOGOUT",
    ("upload", "POST"): "UPLOAD",
    ("download", "POST"): "DOWNLOAD",
    ("delete_file", "POST"): "DELETE",
    ("share_document", "POST"): "SHARE",
    ("revoke_share", "POST"): "REVOKE_SHARE",
    ("manage_case_assignments", "POST"): "CASE_ASSIGNMENT",
    ("remove_case_assignment", "POST"): "CASE_ASSIGNMENT_REMOVE",
    ("manage_users", "POST"): "ROLE_CHANGE",
}


def _record_request_event(response):
    if not has_request_context():
        return
    action = EVENT_MAP.get((request.endpoint, request.method))
    if not action:
        return
    success = response.status_code < 400
    details = f"HTTP {response.status_code}"
    if action == "DOWNLOAD" and response.status_code in (302, 303):
        success = False
        details = "Download request redirected or denied"
    db.session.add(AuditLog(
        user_id=_request_user_id(),
        action=action,
        resource_type="REQUEST",
        resource_id=None,
        case_id=request.view_args.get("case_id") if request.view_args else None,
        success=success,
        ip_address=_ip_address(),
        details=details,
    ))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def _register_app_hooks(app):
    """Attach Phase 3 Flask hooks exactly once to a Flask application."""
    if app.extensions.get("phase3_audit_hooks_registered"):
        return

    @app.before_request
    def phase3_integrity_guard():
        result = _verify_download_integrity()
        if result is not None:
            g.phase3_blocked = True
            return result

    @app.after_request
    def phase3_audit_events(response):
        if not getattr(g, "phase3_blocked", False):
            _backfill_encrypted_storage_hash(response)
            _record_request_event(response)
        return response

    app.extensions["phase3_audit_hooks_registered"] = True


@appcontext_pushed.connect
def _register_when_app_context_is_pushed(sender, **extra):
    """Register request hooks once the real Flask application exists."""
    _register_app_hooks(sender)

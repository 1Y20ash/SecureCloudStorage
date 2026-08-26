"""Automatic Phase 3 audit hooks for database-level security events."""

from flask import has_request_context, request
from flask_login import current_user
from sqlalchemy import event

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
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def _resource_case_id(target):
    if isinstance(target, Case):
        return target.id
    if isinstance(target, CaseDocument):
        return target.case_id
    if isinstance(target, CaseAssignment):
        return target.case_id
    if isinstance(target, DocumentShare):
        return getattr(target, "case_id", None)
    return None


def _resource_id(target):
    return getattr(target, "id", None)


def _resource_type(target):
    return target.__class__.__name__


def _record(session, action, target):
    # Do not audit AuditLog itself; otherwise the listener would recurse.
    session.add(AuditLog(
        user_id=_request_user_id(),
        action=action,
        resource_type=_resource_type(target),
        resource_id=_resource_id(target),
        case_id=_resource_case_id(target),
        success=True,
        ip_address=_ip_address(),
    ))


@event.listens_for(db.session, "before_flush")
def audit_model_mutations(session, flush_context, instances):
    for target in session.new:
        if isinstance(target, AUDITED_MODELS):
            _record(session, "CREATE", target)
    for target in session.dirty:
        if isinstance(target, AUDITED_MODELS) and session.is_modified(target, include_collections=False):
            _record(session, "UPDATE", target)
    for target in session.deleted:
        if isinstance(target, AUDITED_MODELS):
            _record(session, "DELETE", target)

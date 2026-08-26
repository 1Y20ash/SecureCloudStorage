from flask import request
from flask_login import current_user

from extensions import db
from models.audit_log import AuditLog


def record_audit(action, resource_type="system", resource_id=None, case_id=None,
                 success=True, details=None, user=None):
    """Record a security-relevant event without storing secrets or file contents."""
    actor = user if user is not None else current_user
    user_id = actor.id if getattr(actor, "is_authenticated", False) else None
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",", 1)[0].strip()
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        case_id=case_id,
        success=bool(success),
        ip_address=ip,
        details=(details[:500] if details else None),
    )
    db.session.add(log)
    return log

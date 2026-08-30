"""Phase 8 security monitoring and lightweight abuse protection.

Uses the existing immutable audit log as the source of truth. No plaintext
file contents or passwords are logged by this module.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from flask import abort, request
from flask_login import current_user
from sqlalchemy import func

from extensions import db
from models.audit_log import AuditLog


class SlidingWindowLimiter:
    """Small-process limiter suitable for development and single-instance deployments."""

    def __init__(self, limit=60, window_seconds=60):
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self._events = defaultdict(deque)
        self._lock = Lock()

    def allowed(self, key):
        now = datetime.now(timezone.utc)
        with self._lock:
            events = self._events[key]
            cutoff = now - self.window
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


REQUEST_LIMITER = SlidingWindowLimiter(limit=120, window_seconds=60)
AUTH_LIMITER = SlidingWindowLimiter(limit=10, window_seconds=300)


def client_key():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")


def record_security_event(action, success, details=None, case_id=None):
    """Record a security event without storing credentials or request bodies."""
    db.session.add(AuditLog(
        user_id=current_user.id if getattr(current_user, "is_authenticated", False) else None,
        action=action,
        resource_type="SECURITY",
        resource_id=None,
        case_id=case_id,
        success=success,
        ip_address=client_key(),
        details=(details or "")[:500] or None,
    ))
    db.session.commit()


def security_summary(hours=24):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    total = db.session.scalar(
        db.select(func.count(AuditLog.id)).where(AuditLog.created_at >= since)
    ) or 0
    failures = db.session.scalar(
        db.select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= since, AuditLog.success.is_(False)
        )
    ) or 0
    integrity = db.session.scalar(
        db.select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= since,
            AuditLog.action == "INTEGRITY_FAILURE",
        )
    ) or 0
    return {"total_events": total, "failed_events": failures, "integrity_failures": integrity}


def recent_security_events(limit=50):
    return db.session.scalars(
        db.select(AuditLog)
        .where(AuditLog.resource_type == "SECURITY")
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()


def register_security_monitoring(app):
    """Register Phase 8 security middleware and admin monitoring endpoint."""
    @app.before_request
    def phase8_request_guard():
        if request.endpoint in {"static", "home"}:
            return None
        if not REQUEST_LIMITER.allowed(client_key()):
            if getattr(current_user, "is_authenticated", False):
                record_security_event("RATE_LIMIT", False, "Request rate limit exceeded")
            abort(429)
        if request.endpoint == "login" and request.method == "POST":
            if not AUTH_LIMITER.allowed(client_key()):
                record_security_event("AUTH_RATE_LIMIT", False, "Authentication rate limit exceeded")
                abort(429)
        return None

    @app.after_request
    def phase8_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    from flask import Blueprint, render_template
    from flask_login import login_required
    from authz import is_admin

    phase8 = Blueprint("phase8_security", __name__)

    @phase8.route("/security/monitoring")
    @login_required
    def monitoring_dashboard():
        if not is_admin(current_user):
            abort(403)
        return render_template(
            "security_monitoring.html",
            summary=security_summary(),
            events=recent_security_events(),
        )

    if "phase8_security" not in app.blueprints:
        app.register_blueprint(phase8)

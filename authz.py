from datetime import datetime, timezone
from functools import wraps

from flask import abort
from flask_login import current_user


# Phase 2/10 authorization is deny-by-default.
ROLE_PERMISSIONS = {
    "Admin": {"manage_cases", "manage_assignments", "upload", "download", "review"},
    "Investigating Officer": {"manage_cases", "manage_assignments", "upload", "download", "review"},
    "Police Officer": {"manage_cases", "upload", "download", "review"},
    "Legal Officer": {"review", "upload", "download"},
    "Forensic Officer": {"review", "upload", "download"},
    "Authority": {"review"},
}

ROLE_DOCUMENT_CATEGORIES = {
    "Legal Officer": {"Legal Notice", "Court Filing", "Judgment"},
    "Forensic Officer": {"Evidence", "Forensic Report"},
}


def roles_required(*roles):
    allowed = set(roles)

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in allowed:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def is_admin(user):
    return user.is_authenticated and user.role == "Admin"


def has_permission(user, permission):
    if not user.is_authenticated:
        return False
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def share_is_active(share):
    if share.expires_at is None:
        return True

    expires_at = share.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at > datetime.now(timezone.utc)


def has_case_assignment(user, case):
    if not user.is_authenticated or case is None:
        return False
    assignments = getattr(case, "assignments", ()) or ()
    return any(assignment.user_id == user.id for assignment in assignments)


def can_manage_case(user, case):
    if not user.is_authenticated or case is None:
        return False
    return has_permission(user, "manage_cases") and (
        is_admin(user) or case.created_by == user.id
    )


def can_manage_case_assignments(user, case):
    if not user.is_authenticated or case is None:
        return False
    return has_permission(user, "manage_assignments") and (
        is_admin(user) or case.created_by == user.id
    )


def can_access_case(user, case):
    if not user.is_authenticated or case is None:
        return False
    if is_admin(user):
        return True
    return has_permission(user, "review") and (
        case.created_by == user.id or has_case_assignment(user, case)
    )


def role_can_access_category(user, category):
    allowed_categories = ROLE_DOCUMENT_CATEGORIES.get(user.role)
    # Legacy/test records without category metadata retain existing semantics;
    # specialist restrictions apply whenever category metadata is present.
    return allowed_categories is None or category is None or category in allowed_categories


def can_upload_document(user, case, category):
    if not user.is_authenticated or case is None:
        return False
    if not has_permission(user, "upload"):
        return False
    if not can_access_case(user, case):
        return False
    return role_can_access_category(user, category)


def can_access_document(user, case_document):
    if not user.is_authenticated or case_document is None:
        return False
    if is_admin(user):
        return True

    category = getattr(case_document, "category", None)
    if not role_can_access_category(user, category):
        return False

    case = case_document.case
    if can_access_case(user, case):
        return True

    return any(
        share.shared_with_user_id == user.id
        and share.can_view
        and share_is_active(share)
        for share in (getattr(case_document, "shares", ()) or ())
    )


def can_download_document(user, case_document):
    if not can_access_document(user, case_document):
        return False

    shares = getattr(case_document, "shares", ()) or ()
    if not has_permission(user, "download"):
        return any(
            share.shared_with_user_id == user.id
            and share.can_download
            and share_is_active(share)
            for share in shares
        )

    case = case_document.case
    if is_admin(user) or (case and can_access_case(user, case)):
        return True

    return any(
        share.shared_with_user_id == user.id
        and share.can_download
        and share_is_active(share)
        for share in shares
    )

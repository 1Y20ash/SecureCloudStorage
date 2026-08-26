from datetime import datetime, timezone
from functools import wraps

from flask import abort
from flask_login import current_user


# Phase 2 authorization is intentionally deny-by-default.
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


def share_is_active(share):
    return share.expires_at is None or share.expires_at > datetime.now(timezone.utc)


def has_case_assignment(user, case):
    if not user.is_authenticated or case is None:
        return False
    return any(assignment.user_id == user.id for assignment in case.assignments)


def can_manage_case(user, case):
    if not user.is_authenticated or case is None:
        return False
    return is_admin(user) or case.created_by == user.id


def can_access_case(user, case):
    if not user.is_authenticated or case is None:
        return False
    if is_admin(user):
        return True
    if case.created_by == user.id:
        return True
    return has_case_assignment(user, case)


def can_access_document(user, case_document):
    if not user.is_authenticated or case_document is None:
        return False
    if is_admin(user):
        return True
    case = case_document.case
    if can_access_case(user, case):
        return True
    return any(
        share.shared_with_user_id == user.id
        and share.can_view
        and share_is_active(share)
        for share in case_document.shares
    )


def can_download_document(user, case_document):
    if not can_access_document(user, case_document):
        return False
    case = case_document.case
    if is_admin(user) or (case and can_access_case(user, case)):
        return True
    return any(
        share.shared_with_user_id == user.id
        and share.can_download
        and share_is_active(share)
        for share in case_document.shares
    )

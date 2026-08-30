import inspect
from types import SimpleNamespace

from authz import is_admin
from security_monitoring import register_security_monitoring


def user(user_id=1, role="Police Officer", authenticated=True):
    return SimpleNamespace(id=user_id, role=role, is_authenticated=authenticated)


def test_admin_role_is_explicit_and_fail_closed():
    assert is_admin(user(role="Admin")) is True
    assert is_admin(user(role="Police Officer")) is False
    assert is_admin(user(role="Admin", authenticated=False)) is False
    assert is_admin(user(role="Administrator")) is False


def test_admin_guard_is_registered_for_every_admin_path():
    source = inspect.getsource(register_security_monitoring)
    assert 'request.path.startswith("/admin")' in source
    assert "admin_route_allowed(current_user)" in source
    assert "abort(403)" in source
    assert "abort(401)" in source


def test_admin_role_audit_is_security_only_and_does_not_capture_request_body():
    source = inspect.getsource(register_security_monitoring)
    assert 'action="ADMIN_ROLE_CHANGE"' in source
    assert 'resource_type="SECURITY"' in source
    assert 'request.form.get("user_id"' in source
    assert 'request.form.get("role"' in source
    assert "request.data" not in source
    assert "request.get_data" not in source

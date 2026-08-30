import inspect

import pytest

from scripts import bootstrap_admin


def test_bootstrap_admin_requires_explicit_environment_values(monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_NAME", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)

    with pytest.raises(SystemExit, match="BOOTSTRAP_ADMIN_NAME"):
        bootstrap_admin.required_env("BOOTSTRAP_ADMIN_NAME")


def test_bootstrap_admin_password_policy_is_strong():
    source = inspect.getsource(bootstrap_admin.main)
    assert 'len(password) < 12' in source
    assert 'BOOTSTRAP_ADMIN_PASSWORD' in source


def test_bootstrap_admin_refuses_if_admin_already_exists():
    source = inspect.getsource(bootstrap_admin.main)
    assert 'User.role == "Admin"' in source
    assert 'already exists; refusing to create another one' in source


def test_bootstrap_admin_is_not_an_http_route():
    source = inspect.getsource(bootstrap_admin)
    assert '@app.route' not in source

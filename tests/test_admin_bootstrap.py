import runpy

import pytest


def test_bootstrap_admin_refuses_when_admin_exists(monkeypatch, app, db, user_factory):
    existing = user_factory(email="existing-admin@example.test", role="Admin")
    db.session.add(existing)
    db.session.commit()

    monkeypatch.setenv("BOOTSTRAP_ADMIN_NAME", "Bootstrap Admin")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "new-admin@example.test")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "a-strong-bootstrap-password")

    with pytest.raises(SystemExit, match="already exists"):
        with app.app_context():
            runpy.run_module("scripts.bootstrap_admin", run_name="__main__")


def test_bootstrap_admin_requires_strong_password(monkeypatch, app):
    monkeypatch.setenv("BOOTSTRAP_ADMIN_NAME", "Bootstrap Admin")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "new-admin@example.test")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "too-short")

    with pytest.raises(SystemExit, match="at least 12 characters"):
        with app.app_context():
            runpy.run_module("scripts.bootstrap_admin", run_name="__main__")

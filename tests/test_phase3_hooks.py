from flask import g

from app import app


def test_phase3_hooks_register_on_application_context():
    assert not app.extensions.get("phase3_audit_hooks_registered", False)

    with app.app_context():
        assert app.extensions.get("phase3_audit_hooks_registered") is True

    assert any(
        getattr(func, "__name__", "") == "phase3_integrity_guard"
        for func in app.before_request_funcs.get(None, [])
    )
    assert any(
        getattr(func, "__name__", "") == "phase3_audit_events"
        for func in app.after_request_funcs.get(None, [])
    )


def test_phase3_registration_is_idempotent():
    with app.app_context():
        before_count = sum(
            getattr(func, "__name__", "") == "phase3_integrity_guard"
            for func in app.before_request_funcs.get(None, [])
        )
        after_count = sum(
            getattr(func, "__name__", "") == "phase3_audit_events"
            for func in app.after_request_funcs.get(None, [])
        )

    assert before_count == 1
    assert after_count == 1

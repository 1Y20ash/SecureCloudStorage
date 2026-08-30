import importlib


def test_security_headers_are_present():
    from app import app

    with app.test_request_context("/"):
        response = app.make_response("ok")
        for handler in app.after_request_funcs.get(None, []):
            response = handler(response)

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"


def test_config_requires_secret_in_production(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    import config

    try:
        importlib.reload(config)
        assert False, "Production configuration must reject a missing SECRET_KEY"
    except RuntimeError as exc:
        assert "SECRET_KEY" in str(exc)
    finally:
        monkeypatch.delenv("VERCEL", raising=False)
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        importlib.reload(config)

import json
from pathlib import Path

from config import Config


ROOT = Path(__file__).resolve().parents[1]


def test_production_secret_is_required(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    namespace = {}
    exec((ROOT / "config.py").read_text(encoding="utf-8"), namespace)
    try:
        namespace["Config"]
    except RuntimeError:
        raise AssertionError("production configuration should be importable")


def test_secure_session_configuration():
    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert Config.SESSION_COOKIE_SAMESITE == "Lax"
    assert Config.REMEMBER_COOKIE_HTTPONLY is True
    assert Config.REMEMBER_COOKIE_SAMESITE == "Lax"


def test_upload_request_limit_leaves_room_for_multipart_overhead():
    assert Config.MAX_CONTENT_LENGTH == 12 * 1024 * 1024


def test_postgresql_requires_tls_and_short_connection_timeout(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.test/db")
    namespace = {}
    exec((ROOT / "config.py").read_text(encoding="utf-8"), namespace)
    options = namespace["Config"].SQLALCHEMY_ENGINE_OPTIONS
    assert options["connect_args"]["sslmode"] == "require"
    assert options["connect_args"]["connect_timeout"] == 10


def test_vercel_security_headers_are_present():
    policy = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    headers = {
        item["key"]: item["value"]
        for item in policy["headers"][0]["headers"]
    }
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "SAMEORIGIN"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Strict-Transport-Security" in headers
    assert "Permissions-Policy" in headers


def test_dependency_audit_workflow_exists():
    workflow = (ROOT / ".github/workflows/dependency-audit.yml").read_text(encoding="utf-8")
    assert "pip_audit" in workflow
    assert "requirements.txt" in workflow

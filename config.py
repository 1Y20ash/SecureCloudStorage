import os

from sqlalchemy.pool import NullPool


class Config:
    _secret_key = os.getenv("SECRET_KEY")
    _production = os.getenv("FLASK_ENV", "").lower() == "production" or os.getenv("VERCEL") == "1"
    if _production and not _secret_key:
        raise RuntimeError("SECRET_KEY must be configured in production.")
    SECRET_KEY = _secret_key or "dev-only-secret-key-change-this"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///secure_cloud_storage.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in {
        "1", "true", "yes", "on"
    }

    SESSION_COOKIE_SECURE = _production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = _production
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Leave room for multipart/form-data headers while enforcing the 10 MB
    # application-level file limit in app.py.
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024

    if SQLALCHEMY_DATABASE_URI.startswith(("postgresql://", "postgresql+psycopg2://")):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "poolclass": NullPool,
            "connect_args": {
                "sslmode": "require",
                "connect_timeout": 10,
            },
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "poolclass": NullPool,
        }

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
    SUPABASE_STORAGE_BUCKET = os.getenv(
        "SUPABASE_STORAGE_BUCKET", "encrypted-files"
    )

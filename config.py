import os

from sqlalchemy.pool import NullPool


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///secure_cloud_storage.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Proxy headers must be explicitly trusted. Leaving this disabled is the
    # safe default for local development and prevents clients from spoofing
    # their address through X-Forwarded-For.
    TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in {
        "1", "true", "yes", "on"
    }

    # Use PostgreSQL-specific SSL settings only when PostgreSQL is configured.
    # SQLite does not accept sslmode or connect_timeout.
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

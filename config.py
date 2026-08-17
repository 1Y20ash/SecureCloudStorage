import os

from sqlalchemy.pool import NullPool


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///secure_cloud_storage.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase Transaction Pooler is designed for serverless workloads.
    # Disable SQLAlchemy's persistent client-side pool because Vercel
    # functions are short-lived and Supavisor handles pooling for us.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
    SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "encrypted-files")

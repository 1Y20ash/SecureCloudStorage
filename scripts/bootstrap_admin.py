"""Safely bootstrap the first SecureVault administrator.

Usage (local/CI/controlled deployment environment):
    BOOTSTRAP_ADMIN_NAME="Admin" \
    BOOTSTRAP_ADMIN_EMAIL="admin@example.test" \
    BOOTSTRAP_ADMIN_PASSWORD="a-long-random-password" \
    python scripts/bootstrap_admin.py

The command refuses to run when an Admin already exists. It is intentionally
not exposed as a Flask route, so a normal HTTP request cannot create an Admin.
Use synthetic/test credentials only during development.
"""

import os
import sys

from app import app
from extensions import db
from models.user import User


def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main():
    name = required_env("BOOTSTRAP_ADMIN_NAME")
    email = required_env("BOOTSTRAP_ADMIN_EMAIL").lower()
    password = required_env("BOOTSTRAP_ADMIN_PASSWORD")

    if len(password) < 12:
        raise SystemExit("BOOTSTRAP_ADMIN_PASSWORD must contain at least 12 characters")

    with app.app_context():
        if db.session.scalar(db.select(User).where(User.role == "Admin")):
            raise SystemExit("An Admin account already exists; refusing to create another one")

        existing = db.session.scalar(db.select(User).where(User.email == email))
        if existing:
            raise SystemExit("The requested email already belongs to an account; no changes made")

        admin = User(name=name, email=email, role="Admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin account created for {email}")


if __name__ == "__main__":
    sys.exit(main())

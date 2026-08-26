from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


ROLES = (
    "Admin",
    "Investigating Officer",
    "Police Officer",
    "Legal Officer",
    "Forensic Officer",
    "Authority",
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default="Police Officer", index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

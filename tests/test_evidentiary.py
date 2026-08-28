from app import app
from extensions import db
from evidentiary import get_next_version, get_previous_hash


def test_next_version_starts_at_one():
    with app.app_context():
        assert get_next_version(999999) == 1


def test_previous_hash_is_none_when_no_versions():
    with app.app_context():
        assert get_previous_hash(999999) is None
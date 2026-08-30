import hashlib

from app import app, db
from crypto.encryption import encrypt_file
from models.case import Case
from models.case_document import CaseDocument
from models.file import StoredFile
from models.user import User


def test_repeated_wrong_passwords_never_return_plaintext(monkeypatch):
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(name="Test User", email="retry@example.com")
        user.set_password("account-password")
        db.session.add(user)
        db.session.flush()
        case = Case(case_number="CASE-TEST-001", title="Retry Test", created_by=user.id)
        db.session.add(case)
        db.session.flush()
        plaintext = b"synthetic confidential document"
        encrypted = encrypt_file(plaintext, "correct-document-password")
        stored = StoredFile(
            user_id=user.id,
            original_filename="test.txt",
            encrypted_filename="retry-test.enc",
            file_size=len(plaintext),
            sha256_hash=hashlib.sha256(plaintext).hexdigest(),
            encrypted_sha256_hash=hashlib.sha256(encrypted).hexdigest(),
        )
        db.session.add(stored)
        db.session.flush()
        db.session.add(CaseDocument(case_id=case.id, stored_file_id=stored.id, category="Other", version=1, status="Draft"))
        db.session.commit()
        monkeypatch.setattr("app.read_encrypted_file", lambda filename: encrypted)
        with client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

        for wrong_password in ("wrong-one", "wrong-two", "wrong-three"):
            response = client.post(
                f"/documents/{stored.id}/download",
                data={"password": wrong_password},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert response.data != plaintext
            assert "Incorrect encryption password" in response.get_data(as_text=True)
            assert "attachment" not in response.headers.get("Content-Disposition", "").lower()

        response = client.post(
            f"/documents/{stored.id}/download",
            data={"password": "correct-document-password"},
        )
        assert response.status_code == 200
        assert response.data == plaintext
        assert "attachment" in response.headers.get("Content-Disposition", "").lower()

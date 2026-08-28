from types import SimpleNamespace

from app import app
from phase7_ui import _document_or_404


def test_phase7_routes_are_registered():
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/search" in routes
    assert "/documents/<int:document_id>/ocr" in routes


def test_phase7_search_requires_authentication():
    client = app.test_client()

    response = client.get("/search")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_phase7_ocr_requires_authentication():
    client = app.test_client()

    response = client.post("/documents/1/ocr", data={"encryption_password": "test"})

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_phase7_ocr_denies_document_without_document_access(monkeypatch):
    document = SimpleNamespace(id=1)

    monkeypatch.setattr("phase7_ui.db.session.get", lambda model, document_id: document)
    monkeypatch.setattr("phase7_ui.current_user", SimpleNamespace())
    monkeypatch.setattr("phase7_ui.can_access_document", lambda user, case_document: False)

    assert _document_or_404(1) is None


def test_phase7_ocr_allows_document_with_document_access(monkeypatch):
    document = SimpleNamespace(id=1)

    monkeypatch.setattr("phase7_ui.db.session.get", lambda model, document_id: document)
    monkeypatch.setattr("phase7_ui.current_user", SimpleNamespace())
    monkeypatch.setattr("phase7_ui.can_access_document", lambda user, case_document: True)

    assert _document_or_404(1) is document

from app import app


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

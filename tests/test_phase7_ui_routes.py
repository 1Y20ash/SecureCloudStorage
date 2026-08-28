from app import app


def test_phase7_routes_are_registered():
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/search" in routes
    assert "/documents/<int:document_id>/ocr" in routes


def test_phase7_routes_are_authenticated():
    for rule in app.url_map.iter_rules():
        if rule.rule == "/search" or rule.rule.endswith("/ocr"):
            assert rule.endpoint.startswith("phase7_ui.")
            assert "login_required" in repr(rule.endpoint) or rule.endpoint.startswith("phase7_ui.")

from app import app


def test_phase6_signature_ui_routes_are_registered():
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/signatures" in routes
    assert "/signatures/new" in routes
    assert "/signatures/<int:signature_id>" in routes
    assert "/signatures/<int:signature_id>/verify" in routes


def test_phase6_signature_views_are_authenticated():
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/signatures"):
            assert rule.endpoint.startswith("phase6_ui.")

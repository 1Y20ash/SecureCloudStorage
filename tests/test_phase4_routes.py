from app import app


def test_phase4_routes_are_registered():
    routes = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/documents/<int:document_id>/lifecycle" in routes
    assert "/documents/<int:document_id>/versions/<int:version>/restore" in routes

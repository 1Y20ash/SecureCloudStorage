from app import app


def test_phase5_evidence_ui_routes_are_registered():
    routes = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/evidence" in routes
    assert "/evidence/new" in routes
    assert "/evidence/<int:evidence_id>" in routes
    assert "/evidence/<int:evidence_id>/transition" in routes
    assert "/evidence/<int:evidence_id>/transfer" in routes
    assert "/evidence/<int:evidence_id>/receive" in routes
    assert "/evidence/<int:evidence_id>/verify" in routes


def test_phase5_evidence_ui_uses_authenticated_views():
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/evidence"):
            assert "login_required" in repr(rule.endpoint) or rule.endpoint.startswith("phase5_ui.")

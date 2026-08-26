from app import app


def test_phase4_lifecycle_routes_registered():
    rules = {rule.rule: set(rule.methods or ()) for rule in app.url_map.iter_rules()}

    assert "/documents/<int:document_id>/lifecycle" in rules
    assert "POST" in rules["/documents/<int:document_id>/lifecycle"]
    assert "/documents/<int:document_id>/versions/<int:version_number>/restore" in rules
    assert "POST" in rules["/documents/<int:document_id>/versions/<int:version_number>/restore"]

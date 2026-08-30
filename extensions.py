from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class ApplicationLoginManager(LoginManager):
    """Login manager that registers application extensions after app creation."""

    def init_app(self, app, add_context_processor=True):
        super().init_app(app, add_context_processor=add_context_processor)
        from phase4_routes import register_phase4_routes
        register_phase4_routes(app)
        # Phase 3 request hooks must be attached to the actual Flask app before
        # requests are served. Import lazily here to avoid model import cycles.
        from audit_hooks import _register_app_hooks
        _register_app_hooks(app)


login_manager = ApplicationLoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

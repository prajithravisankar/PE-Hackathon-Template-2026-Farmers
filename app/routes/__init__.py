from app.routes.events import events_bp
from app.routes.urls import urls_bp
from app.routes.users import users_bp


def register_routes(app):
    """Register all route blueprints with the Flask app."""
    app.register_blueprint(users_bp)
    app.register_blueprint(urls_bp)
    app.register_blueprint(events_bp)

from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import init_db
from app.routes import register_routes

from app.utils.db_init import create_tables


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    with app.app_context():
        create_tables()

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found_handler(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def request_too_large(e):
        return jsonify({"error": "Request too large. Maximum size is 1 MB."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import init_db
from app.routes import register_routes

from app.utils.db_init import create_tables


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    with app.app_context():
        create_tables()

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app

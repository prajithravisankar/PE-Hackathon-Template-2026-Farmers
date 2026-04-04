import logging
import os
import time

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from prometheus_client import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger.json import JsonFormatter

from app.database import db, init_db
from app.routes import register_routes
from app.utils.db_init import create_tables

log = logging.getLogger(__name__)
_logging_configured = False


def setup_logging():
    global _logging_configured
    if _logging_configured:
        return
    _logging_configured = True
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_app():
    load_dotenv()

    setup_logging()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

    # Use a fresh registry in testing to avoid duplicate metric errors
    # when create_app() is called multiple times by pytest fixtures.
    registry = CollectorRegistry(auto_describe=True)
    metrics = PrometheusMetrics(app, registry=registry)
    metrics.info("app_info", "URL Shortener API", version="1.0.0")

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    with app.app_context():
        create_tables()

    register_routes(app)

    @app.before_request
    def log_request():
        g.start_time = time.time()

    @app.after_request
    def log_response(response):
        duration_ms = (time.time() - g.start_time) * 1000
        level = log.warning if response.status_code >= 400 else log.info
        level(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response

    @app.route("/health")
    def health():
        checks = {"status": "ok", "db": "ok", "redis": "ok"}
        try:
            db.execute_sql("SELECT 1")
        except Exception as e:
            checks["db"] = "down"
            checks["status"] = "degraded"
            log.error("health_check_db_failed", extra={"error": str(e)})
        try:
            import redis as _redis

            r = _redis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            )
            r.ping()
        except Exception:
            checks["redis"] = "down"
        status_code = 200 if checks["status"] == "ok" else 503
        return jsonify(checks), status_code

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

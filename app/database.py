import os
from urllib.parse import parse_qs, urlparse

from peewee import DatabaseProxy, Model, PostgresqlDatabase

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        qs = parse_qs(parsed.query)
        sslmode = os.environ.get(
            "DATABASE_SSLMODE",
            qs.get("sslmode", [None])[0],
        )
        kwargs = dict(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
        )
        if sslmode:
            kwargs["sslmode"] = sslmode
        database = PostgresqlDatabase(
            parsed.path.lstrip("/"),
            **kwargs,
        )
    else:
        database = PostgresqlDatabase(
            os.environ.get("DATABASE_NAME", "hackathon_db"),
            host=os.environ.get("DATABASE_HOST", "localhost"),
            port=int(os.environ.get("DATABASE_PORT", 5432)),
            user=os.environ.get("DATABASE_USER", "postgres"),
            password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        )
    db.initialize(database)

    @app.before_request
    def _db_connect():
        db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def _db_close(exc):
        if not db.is_closed():
            db.close()

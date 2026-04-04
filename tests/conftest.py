import pytest

from app import create_app
from app.database import db
from app.models import Event, ShortURL, User


@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()




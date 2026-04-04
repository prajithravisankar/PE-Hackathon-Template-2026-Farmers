import pytest

from app.models import Event, ShortURL, User


@pytest.fixture(autouse=True)
def clean_db(app):
    # Truncate in reverse dependency order before each test
    Event.delete().execute()
    ShortURL.delete().execute()
    User.delete().execute()
    yield
    Event.delete().execute()
    ShortURL.delete().execute()
    User.delete().execute()

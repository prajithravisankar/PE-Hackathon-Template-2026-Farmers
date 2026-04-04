# Import your models here so Peewee registers them.
# Example:
#   from app.models.product import Product

from app.models.user import User
from app.models.url import ShortURL
from app.models.event import Event

__all__ = ["User", "ShortURL", "Event"]
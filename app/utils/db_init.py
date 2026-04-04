from app.database import db
from app.models import User, ShortURL, Event

def create_tables():
    with db:
        db.create_tables([User, ShortURL, Event], safe=True)
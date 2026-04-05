import logging

from app.database import db
from app.models import User, ShortURL, Event

log = logging.getLogger(__name__)

def create_tables():
    try:
        with db:
            # DigitalOcean dev DBs may restrict CREATE on public schema;
            # attempt to grant it for the current user first.
            try:
                db.execute_sql("GRANT ALL ON SCHEMA public TO CURRENT_USER")
            except Exception:
                pass
            db.create_tables([User, ShortURL, Event], safe=True)
    except Exception as e:
        log.warning("create_tables failed (tables may already exist): %s", e)
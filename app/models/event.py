import datetime
import json
from app.database import BaseModel
from peewee import CharField, DateTimeField, ForeignKeyField, TextField, IntegerField
from app.models.user import User
from app.models.url import ShortURL

class Event(BaseModel):
    url = ForeignKeyField(ShortURL, backref="events", null=True, on_delete="SET NULL")
    user = ForeignKeyField(User, backref="events", null=True, on_delete="SET NULL")
    event_type = CharField(max_length=50)  # "created", "visited", "updated", "deactivated"
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    details = TextField(default="{}")  # JSON string

    class Meta:
        table_name = "events"
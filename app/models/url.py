import datetime

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.user import User


class ShortURL(BaseModel):
    user = ForeignKeyField(User, backref="urls", null=True, on_delete="SET NULL")
    short_code = CharField(unique=True, max_length=10)
    original_url = TextField()
    title = CharField(max_length=500, null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "short_urls"

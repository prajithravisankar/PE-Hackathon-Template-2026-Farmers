import datetime

from peewee import CharField, DateTimeField

from app.database import BaseModel


class User(BaseModel):
    username = CharField(unique=True, max_length=150)
    email = CharField(unique=True, max_length=254)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "users"

import csv
import json
import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from peewee import chunked
from app import create_app
from app.database import db
from app.models import User, ShortURL, Event

def parse_datetime(s):
    if not s:
        return None
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def parse_bool(s):
    return s.strip().lower() in ("true", "1", "yes")

def load_users(filepath="users.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))
    with db.atomic():
        for batch in chunked(rows, 100):
            data = [
                {
                    "id": int(r["id"]),
                    "username": r["username"],
                    "email": r["email"],
                    "created_at": parse_datetime(r["created_at"]),
                }
                for r in batch
            ]
            User.insert_many(data).on_conflict_ignore().execute()
    print(f"Loaded {len(rows)} users")

def load_urls(filepath="urls.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))
    with db.atomic():
        for batch in chunked(rows, 100):
            data = [
                {
                    "id": int(r["id"]),
                    "user_id": int(r["user_id"]),
                    "short_code": r["short_code"],
                    "original_url": r["original_url"],
                    "title": r["title"],
                    "is_active": parse_bool(r["is_active"]),
                    "created_at": parse_datetime(r["created_at"]),
                    "updated_at": parse_datetime(r["updated_at"]),
                }
                for r in batch
            ]
            ShortURL.insert_many(data).on_conflict_ignore().execute()
    print(f"Loaded {len(rows)} urls")

def load_events(filepath="events.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))
    with db.atomic():
        for batch in chunked(rows, 100):
            data = [
                {
                    "id": int(r["id"]),
                    "url_id": int(r["url_id"]),
                    "user_id": int(r["user_id"]),
                    "event_type": r["event_type"],
                    "timestamp": parse_datetime(r["timestamp"]),
                    "details": r["details"],  # already a JSON string
                }
                for r in batch
            ]
            Event.insert_many(data).on_conflict_ignore().execute()
    print(f"Loaded {len(rows)} events")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Clear existing data (child tables first to respect FKs)
        Event.delete().execute()
        ShortURL.delete().execute()
        User.delete().execute()
        print("Cleared existing data.")

        # Disable FK checks so rows referencing skipped duplicates still load
        db.execute_sql("SET session_replication_role = replica;")

        load_users()
        load_urls()
        load_events()

        # Re-enable FK checks
        db.execute_sql("SET session_replication_role = DEFAULT;")

        # Advance sequences past max IDs so future INSERTs don't collide
        db.execute_sql("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));")
        db.execute_sql("SELECT setval('short_urls_id_seq', (SELECT MAX(id) FROM short_urls));")
        db.execute_sql("SELECT setval('events_id_seq', (SELECT MAX(id) FROM events));")

    print("All CSV data loaded.")
import json

from flask import Blueprint, request

from app.models import Event
from app.utils.response import success

events_bp = Blueprint("events", __name__)


def serialize_event(event):
    details = event.details
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except (json.JSONDecodeError, TypeError):
            details = {}
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "details": details if details else {},
    }


@events_bp.route("/events", methods=["GET"])
def list_events():
    query = Event.select().order_by(Event.id)

    url_id = request.args.get("url_id", type=int)
    user_id = request.args.get("user_id", type=int)
    event_type = request.args.get("event_type")

    if url_id is not None:
        query = query.where(Event.url == url_id)
    if user_id is not None:
        query = query.where(Event.user == user_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    events = [serialize_event(e) for e in query]
    return success(events)

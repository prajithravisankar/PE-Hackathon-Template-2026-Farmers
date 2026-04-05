import datetime
import json

from flask import Blueprint, request

from app.models import Event, ShortURL, User
from app.utils.response import created, error, not_found, success

events_bp = Blueprint("events", __name__)


def serialize_event(event):
    details = event.details
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except (json.JSONDecodeError, TypeError):
            details = {}

    url_obj = None
    if event.url_id is not None:
        try:
            url = ShortURL.get_by_id(event.url_id)
            url_obj = {
                "id": url.id,
                "short_code": url.short_code,
                "original_url": url.original_url,
                "title": url.title,
            }
        except ShortURL.DoesNotExist:
            url_obj = None

    user_obj = None
    if event.user_id is not None:
        try:
            user = User.get_by_id(event.user_id)
            user_obj = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        except User.DoesNotExist:
            user_obj = None

    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "details": details if details is not None else {},
        "url": url_obj,
        "user": user_obj,
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

    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    if page is not None and per_page is not None:
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        query = query.paginate(page, per_page)

    events = [serialize_event(e) for e in query]
    return success(events)


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    event_type = data.get("event_type")
    if not isinstance(event_type, str) or not event_type.strip():
        return error("event_type must be a non-empty string", 422)

    url_id = data.get("url_id")
    user_id = data.get("user_id")

    if url_id is not None:
        if not isinstance(url_id, int) or isinstance(url_id, bool):
            return error("url_id must be an integer", 422)
        try:
            ShortURL.get_by_id(url_id)
        except ShortURL.DoesNotExist:
            return not_found("URL")

    if user_id is not None:
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            return error("user_id must be an integer", 422)
        try:
            User.get_by_id(user_id)
        except User.DoesNotExist:
            return not_found("User")

    details = data.get("details")
    if details is not None and not isinstance(details, dict):
        return error("Details must be a JSON object", 422)
    if details is None:
        details = {}

    event = Event.create(
        url=url_id,
        user=user_id,
        event_type=event_type,
        timestamp=datetime.datetime.utcnow(),
        details=json.dumps(details),
    )

    return created(serialize_event(event))


@events_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        return not_found("Event")
    return success(serialize_event(event))


@events_bp.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        return not_found("Event")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    if "event_type" in data:
        if not isinstance(data["event_type"], str) or not data["event_type"].strip():
            return error("event_type must be a non-empty string", 422)
        event.event_type = data["event_type"]

    if "url_id" in data:
        url_id = data["url_id"]
        if url_id is not None:
            if not isinstance(url_id, int) or isinstance(url_id, bool):
                return error("url_id must be an integer", 422)
            try:
                ShortURL.get_by_id(url_id)
            except ShortURL.DoesNotExist:
                return not_found("URL")
        event.url = url_id

    if "user_id" in data:
        user_id = data["user_id"]
        if user_id is not None:
            if not isinstance(user_id, int) or isinstance(user_id, bool):
                return error("user_id must be an integer", 422)
            try:
                User.get_by_id(user_id)
            except User.DoesNotExist:
                return not_found("User")
        event.user = user_id

    if "details" in data:
        details = data["details"]
        if details is not None and not isinstance(details, dict):
            return error("Details must be a JSON object", 422)
        event.details = json.dumps(details if details is not None else {})

    event.save()
    return success(serialize_event(event))


@events_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        return not_found("Event")
    event.delete_instance()
    return "", 204

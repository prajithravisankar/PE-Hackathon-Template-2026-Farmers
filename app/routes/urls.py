import datetime
import json

from flask import Blueprint, redirect, request
from peewee import fn
from peewee import IntegrityError

from app.models import Event, ShortURL, User
from app.utils.cache import cache_response, invalidate_cache
from app.utils.response import created, error, not_found, success
from app.utils.short_code import generate_short_code
from app.utils.validators import is_valid_url

urls_bp = Blueprint("urls", __name__)


def serialize_url(url):
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }


def _log_event(url, user_id, event_type, details_dict):
    Event.create(
        url=url,
        user=user_id,
        event_type=event_type,
        timestamp=datetime.datetime.utcnow(),
        details=json.dumps(details_dict),
    )


@urls_bp.route("/urls", methods=["POST"])
def create_url():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 422)

    original_url = data.get("original_url")
    if not original_url or not is_valid_url(original_url):
        return error("Invalid URL format", 422, {"original_url": "Must be a valid URL (e.g. https://example.com)"})

    user_id = data.get("user_id")
    if user_id is not None:
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            return error("user_id must be an integer", 422)
        try:
            User.get_by_id(user_id)
        except User.DoesNotExist:
            return not_found("User")

    short_code = generate_short_code()
    now = datetime.datetime.utcnow()

    url = ShortURL.create(
        user=user_id,
        short_code=short_code,
        original_url=original_url,
        title=data.get("title"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    _log_event(url, user_id, "created", {
        "short_code": short_code,
        "original_url": original_url,
    })

    invalidate_cache("urls")
    return created(serialize_url(url))


@urls_bp.route("/urls", methods=["GET"])
@cache_response("urls", ttl=15)
def list_urls():
    user_id = request.args.get("user_id", type=int)
    query = ShortURL.select().order_by(ShortURL.id)

    if user_id is not None:
        try:
            User.get_by_id(user_id)
        except User.DoesNotExist:
            return not_found("User")
        query = query.where(ShortURL.user == user_id)

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.where(ShortURL.is_active == (is_active.lower() == "true"))

    short_code = request.args.get("short_code")
    if short_code is not None:
        query = query.where(ShortURL.short_code == short_code)

    title = request.args.get("title")
    if title is not None:
        query = query.where(ShortURL.title == title)

    short_code = request.args.get("short_code")
    if short_code is not None:
        query = query.where(ShortURL.short_code == short_code)

    title = request.args.get("title")
    if title is not None:
        query = query.where(ShortURL.title == title)

    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    if page is not None and per_page is not None:
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        query = query.paginate(page, per_page)

    urls = [serialize_url(u) for u in query]
    return success(urls)


@urls_bp.route("/urls/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = ShortURL.get_by_id(url_id)
    except ShortURL.DoesNotExist:
        return not_found("URL")
    return success(serialize_url(url))


@urls_bp.route("/urls/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        url = ShortURL.get_by_id(url_id)
    except ShortURL.DoesNotExist:
        return not_found("URL")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 422)

    if "original_url" in data:
        if not is_valid_url(data["original_url"]):
            return error("Invalid URL format", 422)
        url.original_url = data["original_url"]

    if "title" in data:
        url.title = data["title"]

    deactivated = False
    if "is_active" in data:
        new_val = data["is_active"]
        if url.is_active and not new_val:
            deactivated = True
        url.is_active = new_val

    url.updated_at = datetime.datetime.utcnow()
    url.save()

    if deactivated:
        _log_event(url, url.user_id, "deactivated", {"short_code": url.short_code})
    else:
        _log_event(url, url.user_id, "updated", {"short_code": url.short_code})

    invalidate_cache("urls")
    return success(serialize_url(url))


@urls_bp.route("/urls/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    try:
        url = ShortURL.get_by_id(url_id)
    except ShortURL.DoesNotExist:
        return not_found("URL")

    _log_event(url, url.user_id, "deleted", {"short_code": url.short_code})
    url.delete_instance()
    invalidate_cache("urls")
    return "", 204


@urls_bp.route("/urls/<int:url_id>/stats", methods=["GET"])
def get_url_stats(url_id):
    try:
        url = ShortURL.get_by_id(url_id)
    except ShortURL.DoesNotExist:
        return not_found("URL")

    total_events = Event.select().where(Event.url == url_id).count()
    total_clicks = Event.select().where(
        (Event.url == url_id) & (Event.event_type == "visited")
    ).count()

    last_visited = (
        Event.select(Event.timestamp)
        .where((Event.url == url_id) & (Event.event_type == "visited"))
        .order_by(Event.timestamp.desc())
        .first()
    )

    return success({
        "id": url.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "total_events": total_events,
        "total_clicks": total_clicks,
        "last_visited": last_visited.timestamp.isoformat() if last_visited else None,
    })


@urls_bp.route("/<short_code>", methods=["GET"])
def redirect_short_url(short_code):
    try:
        url = ShortURL.get(ShortURL.short_code == short_code)
    except ShortURL.DoesNotExist:
        return not_found("URL")

    if not url.is_active:
        return not_found("URL")

    _log_event(url, url.user_id, "visited", {"short_code": url.short_code, "original_url": url.original_url})
    return redirect(url.original_url, 302)

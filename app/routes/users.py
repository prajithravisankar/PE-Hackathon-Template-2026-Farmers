import csv
import datetime
import io

from flask import Blueprint, request
from peewee import IntegrityError

from app.models import User
from app.utils.response import created, error, not_found, success
from app.utils.validators import is_valid_email, is_valid_username

users_bp = Blueprint("users", __name__)


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@users_bp.route("/users", methods=["GET"])
def list_users():
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    query = User.select().order_by(User.id)

    username = request.args.get("username")
    if username is not None:
        query = query.where(User.username == username)

    email = request.args.get("email")
    if email is not None:
        query = query.where(User.email == email)

    if page is not None and per_page is not None:
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        query = query.paginate(page, per_page)
    users = [serialize_user(u) for u in query]
    return success(users)


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return not_found("User")
    return success(serialize_user(user))


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    username = data.get("username")
    email = data.get("email")

    errors = {}
    if not is_valid_username(username):
        errors["username"] = "Invalid username. Must be a non-empty alphanumeric string (max 150 chars)."
    if not is_valid_email(email):
        errors["email"] = "Invalid email format."

    if errors:
        return error("Validation failed", 422, errors)

    try:
        user = User.create(
            username=username,
            email=email,
            created_at=datetime.datetime.utcnow(),
        )
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return error("Username already exists", 409)
        if "email" in err_msg:
            return error("Email already exists", 409)
        return error("Duplicate entry", 409)

    return created(serialize_user(user))


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return not_found("User")
    user.delete_instance()
    return "", 204


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return not_found("User")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)

    errors = {}
    if "username" in data:
        if not is_valid_username(data["username"]):
            errors["username"] = "Invalid username."
    if "email" in data:
        if not is_valid_email(data["email"]):
            errors["email"] = "Invalid email format."

    if errors:
        return error("Validation failed", 422, errors)

    try:
        if "username" in data:
            user.username = data["username"]
        if "email" in data:
            user.email = data["email"]
        user.save()
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return error("Username already exists", 409)
        if "email" in err_msg:
            return error("Email already exists", 409)
        return error("Duplicate entry", 409)

    return success(serialize_user(user))


@users_bp.route("/users/bulk", methods=["POST"])
def bulk_import_users():
    if "file" not in request.files:
        return error("No file provided. Send a CSV as multipart form field named 'file'.", 400)

    file = request.files["file"]
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    imported = 0
    for row in reader:
        username = row.get("username", "").strip()
        email = row.get("email", "").strip()

        if not username or not email:
            continue

        try:
            User.create(
                username=username,
                email=email,
                created_at=datetime.datetime.utcnow(),
            )
            imported += 1
        except IntegrityError:
            continue
        except Exception:
            continue

    return success({"imported": imported})

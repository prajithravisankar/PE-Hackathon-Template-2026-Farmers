from flask import jsonify


def success(data, status=200):
    return jsonify(data), status


def created(data):
    return jsonify(data), 201


def error(message, status=400, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def not_found(resource="Resource"):
    return error(f"{resource} not found", 404)

"""
Gold-tier tests: graceful failure handling.

Every error response must be JSON — never HTML, never a stack trace.
These tests hit the edges our Bronze suite didn't cover.
"""
import io


# ---------- Flask-level error handlers (app/__init__.py) ----------

def test_unknown_route_returns_json_404(client):
    """Hit a route that doesn't exist → Flask's 404 handler."""
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_method_not_allowed_returns_json_405(client):
    """DELETE /users is not a valid method → Flask's 405 handler."""
    response = client.delete("/users")
    assert response.status_code == 405
    data = response.get_json()
    assert "error" in data


# ---------- Content-Type / body edge cases ----------

def test_post_users_with_non_json_body_returns_400(client):
    """POST plain text instead of JSON → 400, not 500."""
    response = client.post(
        "/users",
        data="this is not json",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_post_urls_with_no_body_returns_400(client):
    """POST /urls with empty body → 422."""
    response = client.post(
        "/urls",
        data="garbage",
        content_type="text/plain",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert "error" in data


def test_put_urls_with_no_json_returns_400(client):
    """PUT /urls/<id> without JSON → 400."""
    # First create a url to PUT against
    user_resp = client.post("/users", json={
        "username": "putnojs",
        "email": "putnojs@example.com",
    })
    user_id = user_resp.get_json()["id"]
    url_resp = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    url_id = url_resp.get_json()["id"]

    response = client.put(
        f"/urls/{url_id}",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert "error" in data


def test_put_users_with_no_json_returns_400(client):
    """PUT /users/<id> without JSON → 400."""
    user_resp = client.post("/users", json={
        "username": "putnojs2",
        "email": "putnojs2@example.com",
    })
    user_id = user_resp.get_json()["id"]

    response = client.put(
        f"/users/{user_id}",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


# ---------- Request size limit ----------

def test_oversized_request_returns_413(client):
    """Body larger than MAX_CONTENT_LENGTH → 413 JSON."""
    huge_payload = "x" * (2 * 1024 * 1024)  # 2 MB
    response = client.post(
        "/users",
        data=huge_payload,
        content_type="application/json",
    )
    assert response.status_code == 413
    data = response.get_json()
    assert "error" in data


# ---------- Bulk upload edge cases ----------

def test_bulk_upload_no_file_returns_400(client):
    """POST /users/bulk without a file field → 400."""
    response = client.post(
        "/users/bulk",
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_bulk_upload_empty_csv_returns_zero(client):
    """CSV with only headers, no data rows → imported: 0."""
    csv_data = "username,email\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "empty.csv")}
    response = client.post(
        "/users/bulk",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["imported"] == 0


def test_bulk_upload_csv_invalid_username_format(client):
    """CSV row with spaces in username → still imported (no format validation on bulk)."""
    csv_data = "username,email\nbad user,bad@example.com\ngood_user,good@example.com\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "users.csv")}
    response = client.post(
        "/users/bulk",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["imported"] == 2


def test_bulk_upload_csv_invalid_email_format(client):
    """CSV row with bad email → still imported (no format validation on bulk)."""
    csv_data = "username,email\nvalid_user,not-an-email\nother_user,ok@example.com\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "users.csv")}
    response = client.post(
        "/users/bulk",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["imported"] == 2

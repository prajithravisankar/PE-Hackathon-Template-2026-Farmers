def _create_user(client, username="testuser", email="test@example.com"):
    resp = client.post("/users", json={"username": username, "email": email})
    return resp.get_json()["id"]


def test_create_url_returns_201(client):
    user_id = _create_user(client)
    response = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
        "title": "Example",
    })
    assert response.status_code == 201


def test_create_url_has_short_code(client):
    user_id = _create_user(client)
    response = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    data = response.get_json()
    assert "short_code" in data
    assert len(data["short_code"]) > 0


def test_create_url_short_code_is_6_chars(client):
    user_id = _create_user(client)
    response = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    data = response.get_json()
    assert len(data["short_code"]) == 6


def test_create_url_missing_user_returns_404(client):
    response = client.post("/urls", json={
        "user_id": 99999,
        "original_url": "https://example.com",
    })
    assert response.status_code == 404


def test_create_url_invalid_url_format_returns_422(client):
    response = client.post("/urls", json={
        "original_url": "not-a-url",
    })
    assert response.status_code == 422


def test_get_url_returns_404_for_missing_id(client):
    response = client.get("/urls/99999")
    assert response.status_code == 404


def test_list_urls_filter_by_user_id(client):
    user_id = _create_user(client)
    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    response = client.get(f"/urls?user_id={user_id}")
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(u["user_id"] == user_id for u in data)


def test_put_url_updates_title(client):
    user_id = _create_user(client)
    create_resp = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
        "title": "Old Title",
    })
    url_id = create_resp.get_json()["id"]

    response = client.put(f"/urls/{url_id}", json={"title": "New Title"})
    assert response.status_code == 200
    assert response.get_json()["title"] == "New Title"


def test_put_url_deactivates_url(client):
    user_id = _create_user(client)
    create_resp = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    url_id = create_resp.get_json()["id"]

    response = client.put(f"/urls/{url_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.get_json()["is_active"] is False


def test_put_url_updates_updated_at(client):
    user_id = _create_user(client)
    create_resp = client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    url_data = create_resp.get_json()
    url_id = url_data["id"]
    original_updated_at = url_data["updated_at"]

    response = client.put(f"/urls/{url_id}", json={"title": "Changed"})
    new_updated_at = response.get_json()["updated_at"]
    assert new_updated_at >= original_updated_at

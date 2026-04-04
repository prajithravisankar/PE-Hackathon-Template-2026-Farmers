def _create_user(client, username="evtuser", email="evt@example.com"):
    resp = client.post("/users", json={"username": username, "email": email})
    return resp.get_json()["id"]


def test_get_events_returns_array(client):
    response = client.get("/events")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_create_url_creates_event(client):
    user_id = _create_user(client)
    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    response = client.get("/events")
    events = response.get_json()
    assert len(events) >= 1
    assert events[-1]["event_type"] == "created"


def test_event_has_required_fields(client):
    user_id = _create_user(client)
    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    response = client.get("/events")
    event = response.get_json()[-1]
    for field in ("id", "url_id", "user_id", "event_type", "timestamp", "details"):
        assert field in event, f"Missing field: {field}"


def test_event_details_is_dict_not_string(client):
    user_id = _create_user(client)
    client.post("/urls", json={
        "user_id": user_id,
        "original_url": "https://example.com",
    })
    response = client.get("/events")
    event = response.get_json()[-1]
    assert isinstance(event["details"], dict)

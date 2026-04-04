def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok(client):
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "ok"

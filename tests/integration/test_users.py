import io


# ---------- GET /users/<id> success ----------

def test_get_user_returns_user_object(client):
    create_resp = client.post("/users", json={
        "username": "fetchme",
        "email": "fetchme@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "fetchme"
    assert data["email"] == "fetchme@example.com"


# ---------- PUT /users validation edge cases ----------

def test_put_user_rejects_invalid_username(client):
    create_resp = client.post("/users", json={
        "username": "orig",
        "email": "orig@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={"username": "has spaces"})
    assert response.status_code == 422


def test_put_user_rejects_invalid_email(client):
    create_resp = client.post("/users", json={
        "username": "orig2",
        "email": "orig2@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_put_user_updates_email(client):
    create_resp = client.post("/users", json={
        "username": "emailup",
        "email": "old@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={"email": "new@example.com"})
    assert response.status_code == 200
    assert response.get_json()["email"] == "new@example.com"


def test_put_user_duplicate_username_returns_409(client):
    client.post("/users", json={"username": "taken", "email": "taken@example.com"})
    create_resp = client.post("/users", json={
        "username": "mover",
        "email": "mover@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={"username": "taken"})
    assert response.status_code == 409


# ---------- Original tests ----------

def test_create_user_returns_201(client):
    response = client.post("/users", json={
        "username": "newuser",
        "email": "new@example.com",
    })
    assert response.status_code == 201


def test_create_user_returns_user_object(client):
    response = client.post("/users", json={
        "username": "newuser",
        "email": "new@example.com",
    })
    data = response.get_json()
    assert "id" in data
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "created_at" in data


def test_create_user_rejects_integer_username(client):
    response = client.post("/users", json={
        "username": 12345,
        "email": "int@example.com",
    })
    assert response.status_code == 422


def test_create_user_rejects_invalid_email(client):
    response = client.post("/users", json={
        "username": "validuser",
        "email": "not-an-email",
    })
    assert response.status_code == 422


def test_create_duplicate_username_returns_409(client):
    client.post("/users", json={
        "username": "dupeuser",
        "email": "first@example.com",
    })
    response = client.post("/users", json={
        "username": "dupeuser",
        "email": "second@example.com",
    })
    assert response.status_code == 409


def test_create_duplicate_email_returns_409(client):
    client.post("/users", json={
        "username": "user_one",
        "email": "same@example.com",
    })
    response = client.post("/users", json={
        "username": "user_two",
        "email": "same@example.com",
    })
    assert response.status_code == 409


def test_get_user_returns_404_for_missing_id(client):
    response = client.get("/users/99999")
    assert response.status_code == 404


def test_list_users_returns_array(client):
    client.post("/users", json={"username": "a", "email": "a@example.com"})
    response = client.get("/users")
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_users_with_pagination(client):
    for i in range(5):
        client.post("/users", json={
            "username": f"page_user_{i}",
            "email": f"page{i}@example.com",
        })
    response = client.get("/users?page=1&per_page=2")
    data = response.get_json()
    assert len(data) == 2


def test_list_users_pagination_page_zero_clamped(client):
    client.post("/users", json={"username": "z", "email": "z@example.com"})
    response = client.get("/users?page=0&per_page=10")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_put_user_updates_username(client):
    create_resp = client.post("/users", json={
        "username": "original",
        "email": "orig@example.com",
    })
    user_id = create_resp.get_json()["id"]

    response = client.put(f"/users/{user_id}", json={"username": "updated"})
    assert response.status_code == 200
    assert response.get_json()["username"] == "updated"


def test_put_user_returns_404_for_missing_id(client):
    response = client.put("/users/99999", json={"username": "nope"})
    assert response.status_code == 404


def test_bulk_import_csv_valid(client):
    csv_data = "username,email\nbulk1,bulk1@example.com\nbulk2,bulk2@example.com\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "users.csv")}
    response = client.post("/users/bulk", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.get_json()["imported"] == 2


def test_bulk_import_csv_with_malformed_rows(client):
    csv_data = "username,email\ngood,good@example.com\nbad-row-no-email,\n,missing-username@x.com\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "users.csv")}
    response = client.post("/users/bulk", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.get_json()["imported"] == 1


def test_bulk_import_csv_with_duplicate_rows(client):
    client.post("/users", json={"username": "existing", "email": "existing@example.com"})
    csv_data = "username,email\nexisting,existing@example.com\nfresh,fresh@example.com\n"
    data = {"file": (io.BytesIO(csv_data.encode()), "users.csv")}
    response = client.post("/users/bulk", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.get_json()["imported"] == 2

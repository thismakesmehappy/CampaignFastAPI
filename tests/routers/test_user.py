from app.constants import PAGE_LIMIT_DEFAULT
from tests.conftest import VALID_USERNAME, VALID_PASSWORD, USER_LIST_USERNAMES


class TestCreateUser:
    async def test_create_user(self, client, existing_client):
        response = await client.post("/users", json={
            "username": VALID_USERNAME, "password": VALID_PASSWORD, "client_ids": [existing_client.id],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == VALID_USERNAME
        assert data["client_ids"] == [existing_client.id]
        assert "password" not in data
        assert "password_hash" not in data
        assert "is_admin" not in data

    async def test_create_user_password_too_short(self, client, existing_client):
        response = await client.post("/users", json={
            "username": VALID_USERNAME, "password": "short", "client_ids": [existing_client.id],
        })
        assert response.status_code == 422

    async def test_create_user_client_not_found(self, client):
        response = await client.post("/users", json={
            "username": VALID_USERNAME, "password": VALID_PASSWORD, "client_ids": [999999999999],
        })
        assert response.status_code == 404

    async def test_create_user_multiple_clients_rejected(self, client, existing_client):
        """client_ids is array-shaped for a future many-to-many move, but only one client is supported today."""
        response = await client.post("/users", json={
            "username": VALID_USERNAME, "password": VALID_PASSWORD, "client_ids": [existing_client.id, existing_client.id + 1],
        })
        assert response.status_code == 422


class TestGetUser:
    async def test_get_user(self, client, existing_user):
        response = await client.get(f"/users/{existing_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == existing_user.username
        assert "password_hash" not in data

    async def test_get_user_not_found(self, client, existing_user):
        response = await client.get(f"/users/{existing_user.id + 1}")
        assert response.status_code == 404


class TestListUsers:
    async def test_list_users(self, client, existing_user_list):
        response = await client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(USER_LIST_USERNAMES)
        assert len(data["items"]) == PAGE_LIMIT_DEFAULT

    async def test_list_users_filter_by_username(self, client, existing_user_list):
        response = await client.get("/users", params={"username_filter": USER_LIST_USERNAMES[0]})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_list_users_empty(self, client):
        response = await client.get("/users")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestUpdateUser:
    async def test_update_username(self, client, existing_user):
        response = await client.patch(f"/users/{existing_user.id}", json={"username": "updated_username"})
        assert response.status_code == 200
        assert response.json()["username"] == "updated_username"

    async def test_update_not_found(self, client, existing_user):
        response = await client.patch(f"/users/{existing_user.id + 1}", json={"username": "x"})
        assert response.status_code == 404


class TestDeleteUser:
    async def test_delete_user(self, client, existing_user):
        response = await client.delete(f"/users/{existing_user.id}")
        assert response.status_code == 204

    async def test_delete_user_not_found(self, client, existing_user):
        response = await client.delete(f"/users/{existing_user.id + 1}")
        assert response.status_code == 404


class TestLogin:
    async def test_login_success(self, client, existing_client, make_user):
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)
        response = await client.post("/auth/login", json={"username": VALID_USERNAME, "password": VALID_PASSWORD})
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 1
        assert data["clients"][0]["client_id"] == existing_client.id
        assert data["clients"][0]["client_name"] == existing_client.name
        assert "token" not in data
        assert "password" not in data

    async def test_login_wrong_password(self, client, existing_client, make_user):
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)
        response = await client.post("/auth/login", json={"username": VALID_USERNAME, "password": "wrong-password"})
        assert response.status_code == 422

    async def test_login_unknown_username(self, client):
        response = await client.post("/auth/login", json={"username": "no_such_user", "password": "whatever"})
        assert response.status_code == 422

    async def test_login_requires_valid_api_key(self, client, existing_client, make_user):
        """/auth/login is behind require_api_key like every other route — the app-wide key gets you in the door, login itself scopes to a client."""
        await make_user(username=VALID_USERNAME, password=VALID_PASSWORD, client_id=existing_client.id)
        client.headers["X-Api-Key"] = "not-a-valid-key"
        response = await client.post("/auth/login", json={"username": VALID_USERNAME, "password": VALID_PASSWORD})
        assert response.status_code == 401

from app.constants import PAGE_LIMIT_DEFAULT
from tests.conftest import VALID_CLIENT_NAME, VALID_CLIENT_API_KEY, CLIENT_LIST_NAMES, LONG_STRING


class TestCreateClient:
    async def test_create_client(self, client):
        response = await client.post("/clients/", json={"name": VALID_CLIENT_NAME, "api_key": VALID_CLIENT_API_KEY})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == VALID_CLIENT_NAME
        assert "api_key" not in data

    async def test_create_client_name_too_long(self, client):
        response = await client.post("/clients/", json={"name": LONG_STRING, "api_key": VALID_CLIENT_API_KEY})
        assert response.status_code == 422

    async def test_create_client_name_missing(self, client):
        response = await client.post("/clients/", json={"api_key": VALID_CLIENT_API_KEY})
        assert response.status_code == 422

    async def test_create_client_api_key_missing(self, client):
        response = await client.post("/clients/", json={"name": VALID_CLIENT_NAME})
        assert response.status_code == 422


class TestGetClient:
    async def test_get_client(self, client, existing_client):
        response = await client.get(f"/clients/{existing_client.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == existing_client.name
        assert "api_key" not in data

    async def test_get_client_not_found(self, client, existing_client):
        response = await client.get(f"/clients/{existing_client.id + 1}")
        assert response.status_code == 404


class TestListClients:
    async def test_list_clients(self, client, existing_client_list):
        response = await client.get("/clients/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(CLIENT_LIST_NAMES)
        assert len(data["items"]) == PAGE_LIMIT_DEFAULT

    async def test_list_clients_filter_by_name(self, client, existing_client_list):
        response = await client.get("/clients/", params={"name_filter": "Acme"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Acme Corp"

    async def test_list_clients_filter_no_match(self, client, existing_client_list):
        response = await client.get("/clients/", params={"name_filter": "zzznomatch"})
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_list_clients_empty(self, client):
        response = await client.get("/clients/")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestUpdateClient:
    async def test_update_name(self, client, existing_client):
        response = await client.patch(f"/clients/{existing_client.id}", json={"name": "Updated"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    async def test_update_not_found(self, client, existing_client):
        response = await client.patch(f"/clients/{existing_client.id + 1}", json={"name": "x"})
        assert response.status_code == 404

    async def test_update_name_too_long(self, client, existing_client):
        response = await client.patch(f"/clients/{existing_client.id}", json={"name": LONG_STRING})
        assert response.status_code == 422


class TestDeleteClient:
    async def test_delete_client(self, client, existing_client):
        response = await client.delete(f"/clients/{existing_client.id}")
        assert response.status_code == 204

    async def test_delete_client_not_found(self, client, existing_client):
        response = await client.delete(f"/clients/{existing_client.id + 1}")
        assert response.status_code == 404
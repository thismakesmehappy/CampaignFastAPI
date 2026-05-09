import pytest

from app.services import client as client_service
from app.schema.client import ClientCreate, ClientUpdate, ClientFilter
from app.schema import PaginatedFilter
from app.exceptions import NotFoundError
from tests.conftest import VALID_CLIENT_NAME, CLIENT_LIST_NAMES


class TestCreateClient:
    async def test_create_client(self, db_session):
        data = ClientCreate(name=VALID_CLIENT_NAME)
        client = await client_service.create(db_session, data)
        assert client.id is not None
        assert client.name == VALID_CLIENT_NAME
        assert client.api_key is not None
        assert len(client.api_key) > 0

    async def test_create_client_generates_unique_api_keys(self, db_session):
        c1 = await client_service.create(db_session, ClientCreate(name="Client One"))
        c2 = await client_service.create(db_session, ClientCreate(name="Client Two"))
        assert c1.api_key != c2.api_key

    async def test_create_client_with_email(self, db_session):
        data = ClientCreate(name=VALID_CLIENT_NAME, email="test@example.com")
        client = await client_service.create(db_session, data)
        assert client.email == "test@example.com"


class TestGetClient:
    async def test_get_client(self, db_session, existing_client):
        client = await client_service.get(db_session, existing_client.id)
        assert client.id == existing_client.id

    async def test_get_client_not_found(self, db_session, existing_client):
        with pytest.raises(NotFoundError):
            await client_service.get(db_session, existing_client.id + 1)


class TestListClients:
    async def test_list_clients(self, db_session, existing_client_list):
        result = await client_service.list_clients(db_session)
        assert result.total == len(CLIENT_LIST_NAMES)

    async def test_list_clients_pagination(self, db_session, existing_client_list):
        result = await client_service.list_clients(db_session, PaginatedFilter(limit=3))
        assert len(result.items) == 3

    async def test_list_clients_filter_by_name(self, db_session, existing_client_list):
        result = await client_service.list_clients(db_session, options=ClientFilter(name_filter="Acme"))
        assert result.total == 1
        assert result.items[0].name == "Acme Corp"

    async def test_list_clients_filter_no_match(self, db_session, existing_client_list):
        result = await client_service.list_clients(db_session, options=ClientFilter(name_filter="zzznomatch"))
        assert result.total == 0

    async def test_list_clients_has_more(self, db_session, existing_client_list):
        result = await client_service.list_clients(db_session, PaginatedFilter(limit=3))
        assert result.has_more is True

    async def test_list_clients_empty(self, db_session):
        result = await client_service.list_clients(db_session)
        assert result.total == 0
        assert result.items == []


class TestUpdateClient:
    async def test_update_name(self, db_session, existing_client):
        result = await client_service.update(db_session, existing_client.id, ClientUpdate(name="New Name"))
        assert result.name == "New Name"

    async def test_update_is_active(self, db_session, existing_client):
        result = await client_service.update(db_session, existing_client.id, ClientUpdate(is_active=False))
        assert result.is_active is False

    async def test_update_not_found(self, db_session, existing_client):
        with pytest.raises(NotFoundError):
            await client_service.update(db_session, existing_client.id + 1, ClientUpdate(name="x"))


class TestDeleteClient:
    async def test_delete_client(self, db_session, existing_client):
        await client_service.delete(db_session, existing_client.id)
        with pytest.raises(NotFoundError):
            await client_service.get(db_session, existing_client.id)

    async def test_delete_client_not_found(self, db_session, existing_client):
        with pytest.raises(NotFoundError):
            await client_service.delete(db_session, existing_client.id + 1)
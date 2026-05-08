from app.repositories import client as client_repo
from app.schema import PaginatedFilter
from app.schema.client import ClientFilter
from tests.conftest import (
    VALID_CLIENT_NAME,
    VALID_CLIENT_API_KEY,
    CLIENT_LIST_NAMES,
    LENGTH_OF_CLIENT_RESULTS_DEFAULT,
)


class TestSaveClient:
    async def test_save_client(self, db_session, client_factory):
        client = await client_repo.save(db_session, client_factory())
        assert client.name == VALID_CLIENT_NAME
        assert client.api_key == VALID_CLIENT_API_KEY
        assert client.id is not None
        assert client.id > 0

    async def test_save_client_update_existing(self, db_session, existing_client):
        existing_client.name = "Updated Name"
        client = await client_repo.save(db_session, existing_client)
        assert client.name == "Updated Name"
        assert client.id == existing_client.id


class TestGetClient:
    async def test_get_client(self, db_session, existing_client):
        client = await client_repo.get(db_session, existing_client.id)
        assert client is not None
        assert client.id == existing_client.id
        assert client.name == existing_client.name

    async def test_get_client_not_found(self, db_session, existing_client):
        client = await client_repo.get(db_session, existing_client.id + 1)
        assert client is None


class TestFindAllClients:
    async def test_find_all_no_filters(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session)
        assert len(result) == LENGTH_OF_CLIENT_RESULTS_DEFAULT

    async def test_find_all_limit(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session, PaginatedFilter(limit=3))
        assert len(result) == 3

    async def test_find_all_offset_past_end(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session, PaginatedFilter(offset=len(CLIENT_LIST_NAMES)))
        assert result == []

    async def test_find_all_empty(self, db_session):
        result = await client_repo.find_all(db_session)
        assert result == []

    async def test_filter_by_name_partial_matches_all(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session, None, ClientFilter(name_filter="a"))
        assert len(result) > 0
        for client in result:
            assert "a" in client.name.lower()

    async def test_filter_by_name_full_match_returns_one(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session, None, ClientFilter(name_filter=CLIENT_LIST_NAMES[0][0]))
        assert len(result) == 1
        assert result[0].name == CLIENT_LIST_NAMES[0][0]

    async def test_filter_by_name_no_match(self, db_session, existing_client_list):
        result = await client_repo.find_all(db_session, None, ClientFilter(name_filter="zzznomatch"))
        assert result == []


class TestCountClients:
    async def test_count_with_entries(self, db_session, existing_client_list):
        total = await client_repo.count(db_session)
        assert total == len(CLIENT_LIST_NAMES)

    async def test_count_empty(self, db_session):
        total = await client_repo.count(db_session)
        assert total == 0

    async def test_count_filter_matches_all(self, db_session, existing_client_list):
        total = await client_repo.count(db_session, ClientFilter(name_filter="a"))
        assert total > 0

    async def test_count_filter_no_match(self, db_session, existing_client_list):
        total = await client_repo.count(db_session, ClientFilter(name_filter="zzznomatch"))
        assert total == 0


class TestDeleteClient:
    async def test_delete_client(self, db_session, existing_client):
        await client_repo.delete(db_session, existing_client)
        result = await client_repo.get(db_session, existing_client.id)
        assert result is None
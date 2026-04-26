from app.constants import PAGE_LIMIT_DEFAULT
from tests.conftest import (
    TEST_CAMPAIGN_CRUD,
    LONG_STRING,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
    TEST_CAMPAIGN_LIST_CRUD,
    UPDATE_CAMPAIGN_NAME,
    UPDATE_CAMPAIGN_CLIENT,
    VALID_CAMPAIGN_NAME,
)
from tests.helpers.campaign import compare_campaign_list_equality


class TestCreateCampaign:
    async def test_create_campaign(self, client):
        response = await client.post("/campaigns/", json={"name": VALID_CAMPAIGN_NAME, "client": VALID_CAMPAIGN_NAME})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == VALID_CAMPAIGN_NAME
        assert data["client"] == VALID_CAMPAIGN_NAME

    async def test_create_campaign_name_too_long(self, client):
        response = await client.post("/campaigns/", json={"name": LONG_STRING, "client": "Client"})
        assert response.status_code == 422
        
    async def test_create_campaign_client_too_long(self, client):
        response = await client.post("/campaigns/", json={"name": "Campaign", "client": LONG_STRING})
        assert response.status_code == 422

    async def test_create_campaign_name_missing(self, client):
        response = await client.post(
            "/campaigns/", json={"client": "Client"}
        )
        assert response.status_code == 422

    async def test_create_campaign_client_missing(self, client):
        response = await client.post(
            "/campaigns/", json={"name": "Campaign"}
        )
        assert response.status_code == 422

class TestGetCampaign:
    async def test_get_campaign(self, client, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        response = await client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_CAMPAIGN_CRUD.name
        assert data["client"] == TEST_CAMPAIGN_CRUD.client

    async def test_get_campaign_not_found(self, client, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        response = await client.get(f"/campaigns/{fake_id}")
        assert response.status_code == 404

class TestListCampaign:
    async def test_list_campaign(self, client, existing_campaign_list_crud):
        response = await client.get("/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == PAGE_LIMIT_DEFAULT
        items = data['items']
        assert len(items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD)

    async def test_list_campaigns_filter_limit_is_less_than_total_items(self, client, existing_campaign_list_crud):
        limit = 4
        response = await client.get(f"/campaigns/?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == limit
        items = data['items']
        assert len(items) == limit
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD)

    async def test_list_campaigns_filter_limit_is_greater_than_total_items(self, client, existing_campaign_list_crud):
        limit = len(TEST_CAMPAIGN_LIST_CRUD) * 2
        response = await client.get(f"/campaigns/?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == limit
        items = data['items']
        assert len(items) == len(TEST_CAMPAIGN_LIST_CRUD)
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD)

    async def test_list_campaigns_filter_offset_result_contains_default_number_of_items(self, client, existing_campaign_list_crud):
        offset = 1
        response = await client.get(f"/campaigns/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 1
        assert data['limit'] == PAGE_LIMIT_DEFAULT
        items = data['items']
        assert len(items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD, offset)
    
    async def test_list_campaigns_filter_offset_result_contains_fewer_items(self, client, existing_campaign_list_crud):
        expected_results_size = 2
        offset = len(TEST_CAMPAIGN_LIST_CRUD) - expected_results_size
        response = await client.get(f"/campaigns/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == expected_results_size
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD, offset)

    async def test_list_campaigns_filter_offset_past_number_of_entries(self, client, existing_campaign_list_crud):
        offset = len(TEST_CAMPAIGN_LIST_CRUD)
        response = await client.get(f"/campaigns/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == 0
        
    async def test_list_campaigns_filter_offset_and_limit(self, client, existing_campaign_list_crud):
        offset = 1
        limit = 2
        response = await client.get(f"/campaigns/?offset={offset}&limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == limit
        items = data["items"]
        assert len(items) == limit
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST_CRUD, offset)

    async def test_list_campaigns_filter_no_entries(self, client):
        response = await client.get("/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == 0


class TestUpdateCampaign:
    async def test_update_campaign(self, client, existing_campaign_crud):
        response = await client.patch(
            f"/campaigns/{existing_campaign_crud.id}",
            json={"name": UPDATE_CAMPAIGN_NAME, "client": UPDATE_CAMPAIGN_CLIENT},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == UPDATE_CAMPAIGN_NAME
        assert data["client"] == UPDATE_CAMPAIGN_CLIENT
    
    async def test_update_campaign_name(self, client, existing_campaign_crud):
        response = await client.patch(
            f"/campaigns/{existing_campaign_crud.id}",
            json={"name": UPDATE_CAMPAIGN_NAME},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == UPDATE_CAMPAIGN_NAME
        assert data["client"] == existing_campaign_crud.client

    async def test_update_campaign_client(self, client, existing_campaign_crud):
        response = await client.patch(
            f"/campaigns/{existing_campaign_crud.id}",
            json={"client": UPDATE_CAMPAIGN_CLIENT},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == existing_campaign_crud.name
        assert data["client"] == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_not_found(self, client, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        response = await client.patch(f"/campaigns/{fake_id}", json={"name": UPDATE_CAMPAIGN_NAME})
        assert response.status_code == 404

    async def test_update_campaign_name_too_long(self, client, existing_campaign_crud):
        response = await client.patch(
            f"/campaigns/{existing_campaign_crud.id}",
            json={"name": LONG_STRING},
        )
        assert response.status_code == 422

    async def test_update_campaign_client_too_long(self, client, existing_campaign_crud):
        response = await client.patch(
            f"/campaigns/{existing_campaign_crud.id}",
            json={"client": LONG_STRING},
        )
        assert response.status_code == 422

class TestDeleteCampaign:
    async def test_delete_campaign(self, client, existing_campaign_crud):
        response = await client.delete(f"/campaigns/{existing_campaign_crud.id}")
        assert response.status_code == 204

    async def test_delete_campaign_not_found(self, client, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        response = await client.delete(f"/campaigns/{fake_id}")
        assert response.status_code == 404

    async def test_delete_campaign_removes_it(self, client, existing_campaign_crud):
        await client.delete(f"/campaigns/{existing_campaign_crud.id}")
        response = await client.get(f"/campaigns/{existing_campaign_crud.id}")
        assert response.status_code == 404
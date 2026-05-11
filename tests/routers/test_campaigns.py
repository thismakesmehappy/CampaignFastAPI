from app.constants import PAGE_LIMIT_DEFAULT
from tests.conftest import (
    LONG_STRING,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
    TEST_CAMPAIGN_LIST,
    UPDATE_CAMPAIGN_NAME,
    VALID_CAMPAIGN_NAME,
)
from tests.helpers.campaign import compare_campaign_list_equality


class TestCreateCampaign:
    async def test_create_campaign(self, client, existing_client):
        response = await client.post(f"/clients/{existing_client.id}/campaigns", json={"name": VALID_CAMPAIGN_NAME})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == VALID_CAMPAIGN_NAME
        assert data["client_id"] == existing_client.id

    async def test_create_campaign_name_too_long(self, client, existing_client):
        response = await client.post(f"/clients/{existing_client.id}/campaigns", json={"name": LONG_STRING})
        assert response.status_code == 422

    async def test_create_campaign_name_missing(self, client, existing_client):
        response = await client.post(f"/clients/{existing_client.id}/campaigns", json={})
        assert response.status_code == 422

    async def test_create_campaign_client_not_found(self, client, existing_client):
        fake_id = existing_client.id + 1
        response = await client.post(f"/clients/{fake_id}/campaigns", json={"name": VALID_CAMPAIGN_NAME})
        assert response.status_code == 404


class TestGetCampaign:
    async def test_get_campaign(self, client, existing_campaign):
        campaign_id = existing_campaign.id
        response = await client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == existing_campaign.name
        assert data["client_id"] == existing_campaign.client_id

    async def test_get_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.get(f"/campaigns/{fake_id}")
        assert response.status_code == 404


class TestListCampaign:
    async def test_list_campaign(self, client, existing_campaign_list):
        response = await client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == PAGE_LIMIT_DEFAULT
        items = data['items']
        assert len(items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST)

    async def test_list_campaigns_filter_limit_is_less_than_total_items(self, client, existing_campaign_list):
        limit = 4
        response = await client.get(f"/campaigns?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == limit
        items = data['items']
        assert len(items) == limit
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST)

    async def test_list_campaigns_filter_limit_is_greater_than_total_items(self, client, existing_campaign_list):
        limit = len(TEST_CAMPAIGN_LIST) * 2
        response = await client.get(f"/campaigns?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 0
        assert data['limit'] == limit
        items = data['items']
        assert len(items) == len(TEST_CAMPAIGN_LIST)
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST)

    async def test_list_campaigns_filter_offset_result_contains_default_number_of_items(self, client, existing_campaign_list):
        offset = 1
        response = await client.get(f"/campaigns?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data['offset'] == 1
        assert data['limit'] == PAGE_LIMIT_DEFAULT
        items = data['items']
        assert len(items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST, offset)

    async def test_list_campaigns_filter_offset_result_contains_fewer_items(self, client, existing_campaign_list):
        expected_results_size = 2
        offset = len(TEST_CAMPAIGN_LIST) - expected_results_size
        response = await client.get(f"/campaigns?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == expected_results_size
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST, offset)

    async def test_list_campaigns_filter_offset_past_number_of_entries(self, client, existing_campaign_list):
        offset = len(TEST_CAMPAIGN_LIST)
        response = await client.get(f"/campaigns?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == 0

    async def test_list_campaigns_filter_offset_and_limit(self, client, existing_campaign_list):
        offset = 1
        limit = 2
        response = await client.get(f"/campaigns?offset={offset}&limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == limit
        items = data["items"]
        assert len(items) == limit
        compare_campaign_list_equality(items, TEST_CAMPAIGN_LIST, offset)

    async def test_list_campaigns_filter_no_entries(self, client):
        response = await client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == 0

    async def test_list_campaigns_filter_by_name_matches_all(self, client, existing_campaign_list):
        response = await client.get("/campaigns?name_filter=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(TEST_CAMPAIGN_LIST)
        assert len(data["items"]) == LENGTH_OF_RESULTS_DEFAULT_FILTERS

    async def test_list_campaigns_filter_by_name_matches_some(self, client, existing_campaign_list):
        # "ve" appears in Five, Seven, Eleven, Twelve — 4 entries
        response = await client.get("/campaigns?name_filter=ve")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4
        assert data["has_more"] is False

    async def test_list_campaigns_filter_by_name_matches_none(self, client, existing_campaign_list):
        response = await client.get("/campaigns?name_filter=Invalid")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
        assert data["has_more"] is False

    async def test_list_campaigns_filter_by_client_name_matches_some(self, client, existing_campaign_list):
        # "ve" in client name: Five, Seven, Eleven, Twelve — 4 entries
        response = await client.get("/campaigns?client_name_filter=ve")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    async def test_list_campaigns_filter_by_name_and_client_name(self, client, existing_campaign_list):
        # name contains "ev" and client name contains "ve": Seven, Eleven — 2 entries
        response = await client.get("/campaigns?name_filter=ev&client_name_filter=ve")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["has_more"] is False

    async def test_list_campaigns_filter_by_ids(self, client, existing_campaign_list):
        ids = f"{existing_campaign_list[0].id},{existing_campaign_list[1].id}"
        response = await client.get("/campaigns", params={"ids": ids})
        assert response.status_code == 200
        assert response.json()["total"] == 2

    async def test_list_campaigns_filter_by_ids_not_found(self, client, existing_campaign_list):
        response = await client.get("/campaigns", params={"ids": "999999999999"})
        assert response.status_code == 404


class TestListCampaignForClient:
    async def test_list_campaigns_for_client(self, client, existing_campaign_list):
        target = existing_campaign_list[0]
        response = await client.get(f"/clients/{target.client_id}/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        compare_campaign_list_equality(data["items"], [target], client_id=target.client_id)

    async def test_list_campaigns_for_client_not_found(self, client, existing_campaign_list):
        max_id = max(c.client_id for c in existing_campaign_list)
        response = await client.get(f"/clients/{max_id + 1}/campaigns")
        assert response.status_code == 404

    async def test_list_campaigns_for_client_no_entries(self, client, existing_client):
        response = await client.get(f"/clients/{existing_client.id}/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestUpdateCampaign:
    async def test_update_campaign_name(self, client, existing_campaign):
        response = await client.patch(
            f"/campaigns/{existing_campaign.id}",
            json={"name": UPDATE_CAMPAIGN_NAME},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == UPDATE_CAMPAIGN_NAME
        assert data["client_id"] == existing_campaign.client_id

    async def test_update_campaign_client_id(self, client, existing_campaign, existing_client):
        response = await client.patch(
            f"/campaigns/{existing_campaign.id}",
            json={"client_id": existing_client.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == existing_campaign.name
        assert data["client_id"] == existing_client.id

    async def test_update_campaign_name_and_client_id(self, client, existing_campaign, existing_client):
        response = await client.patch(
            f"/campaigns/{existing_campaign.id}",
            json={"name": UPDATE_CAMPAIGN_NAME, "client_id": existing_client.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == UPDATE_CAMPAIGN_NAME
        assert data["client_id"] == existing_client.id

    async def test_update_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.patch(f"/campaigns/{fake_id}", json={"name": UPDATE_CAMPAIGN_NAME})
        assert response.status_code == 404

    async def test_update_campaign_name_too_long(self, client, existing_campaign):
        response = await client.patch(
            f"/campaigns/{existing_campaign.id}",
            json={"name": LONG_STRING},
        )
        assert response.status_code == 422

    async def test_update_campaign_client_id_not_found(self, client, existing_campaign, existing_client):
        response = await client.patch(
            f"/campaigns/{existing_campaign.id}",
            json={"client_id": existing_client.id + 999},
        )
        assert response.status_code == 404


class TestDeleteCampaign:
    async def test_delete_campaign(self, client, existing_campaign):
        response = await client.delete(f"/campaigns/{existing_campaign.id}")
        assert response.status_code == 204

    async def test_delete_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.delete(f"/campaigns/{fake_id}")
        assert response.status_code == 404

    async def test_delete_campaign_removes_it(self, client, existing_campaign):
        await client.delete(f"/campaigns/{existing_campaign.id}")
        response = await client.get(f"/campaigns/{existing_campaign.id}")
        assert response.status_code == 404
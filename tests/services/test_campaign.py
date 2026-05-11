import pytest
from app.services import campaign as campaign_service
from app.repositories import campaign as campaign_repo
from app.exceptions import NotFoundError
from app.schema import CampaignCreate, CampaignUpdate, PaginatedFilter
from app.schema.campaign import CampaignFilter
from tests.conftest import (
    VALID_CAMPAIGN_NAME,
    UPDATE_CAMPAIGN_NAME,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
    TEST_CAMPAIGN_LIST,
)
from tests.helpers.campaign import compare_campaign_list_equality


class TestCreateCampaign:
    async def test_create_campaign(self, db_session, existing_client):
        data = CampaignCreate(name=VALID_CAMPAIGN_NAME)
        campaign = await campaign_service.create(db_session, data, existing_client.id)
        assert campaign.id is not None
        assert campaign.id > 0
        assert campaign.name == VALID_CAMPAIGN_NAME
        assert campaign.client_id == existing_client.id

    async def test_create_campaign_client_not_found(self, db_session, existing_client):
        data = CampaignCreate(name=VALID_CAMPAIGN_NAME)
        with pytest.raises(NotFoundError):
            await campaign_service.create(db_session, data, existing_client.id + 1)


class TestGetCampaign:
    async def test_get_campaign(self, db_session, existing_campaign):
        campaign = await campaign_service.get(db_session, existing_campaign.id)
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client_id == existing_campaign.client_id

    async def test_get_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        with pytest.raises(NotFoundError) as exc_info:
            await campaign_service.get(db_session, fake_id)
        assert "Campaign not found" in exc_info.value.messages


class TestListCampaigns:
    async def test_list_campaigns_no_filters(self, db_session, existing_campaign_list):
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination)
        assert response.total == len(TEST_CAMPAIGN_LIST)
        assert len(response.items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        assert response.offset == 0
        assert response.limit == pagination.limit
        compare_campaign_list_equality(response.items, TEST_CAMPAIGN_LIST)

    async def test_list_campaigns_has_more(self, db_session, existing_campaign_list):
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination)
        assert response.has_more == (len(TEST_CAMPAIGN_LIST) > pagination.limit)

    async def test_list_campaigns_with_limit(self, db_session, existing_campaign_list):
        limit = 3
        pagination = PaginatedFilter(limit=limit)
        response = await campaign_service.list_campaigns(db_session, pagination)
        assert len(response.items) == limit
        assert response.has_more is True
        compare_campaign_list_equality(response.items, TEST_CAMPAIGN_LIST)

    async def test_list_campaigns_with_offset(self, db_session, existing_campaign_list):
        offset = len(TEST_CAMPAIGN_LIST) - 2
        pagination = PaginatedFilter(offset=offset)
        response = await campaign_service.list_campaigns(db_session, pagination)
        assert len(response.items) == 2
        assert response.has_more is False
        compare_campaign_list_equality(response.items, TEST_CAMPAIGN_LIST, offset)

    async def test_list_campaigns_no_entries(self, db_session):
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination)
        assert response.total == 0
        assert len(response.items) == 0
        assert response.has_more is False

    async def test_list_campaigns_filter_by_name_matches_all(self, db_session, existing_campaign_list):
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, CampaignFilter(name_filter="Test"))
        assert response.total == len(TEST_CAMPAIGN_LIST)
        assert len(response.items) == LENGTH_OF_RESULTS_DEFAULT_FILTERS

    async def test_list_campaigns_filter_by_name_matches_some(self, db_session, existing_campaign_list):
        # "ve" appears in Five, Seven, Eleven, Twelve — 4 entries
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, CampaignFilter(name_filter="ve"))
        assert response.total == 4
        assert len(response.items) == 4
        assert response.has_more is False

    async def test_list_campaigns_filter_by_name_matches_none(self, db_session, existing_campaign_list):
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, CampaignFilter(name_filter="Invalid"))
        assert response.total == 0
        assert len(response.items) == 0
        assert response.has_more is False

    async def test_list_campaigns_filter_by_client_matches_some(self, db_session, existing_campaign_list):
        # "ve" in client name: Five, Seven, Eleven, Twelve — 4 entries
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, CampaignFilter(client_name_filter="ve"))
        assert response.total == 4
        assert len(response.items) == 4

    async def test_list_campaigns_filter_by_name_and_client(self, db_session, existing_campaign_list):
        # name contains "ev" and client name contains "ve": Seven, Eleven — 2 entries
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, CampaignFilter(name_filter="ev", client_name_filter="ve"))
        assert response.total == 2
        assert len(response.items) == 2
        assert response.has_more is False

    async def test_list_campaigns_for_client(self, db_session, existing_campaign_list):
        target = existing_campaign_list[0]
        pagination = PaginatedFilter()
        response = await campaign_service.list_campaigns(db_session, pagination, client_id=target.client_id)
        assert response.total == 1
        assert response.items[0].client_id == target.client_id

    async def test_list_campaigns_for_client_not_found(self, db_session, existing_campaign_list):
        max_id = max(c.client_id for c in existing_campaign_list)
        with pytest.raises(NotFoundError):
            await campaign_service.list_campaigns(db_session, client_id=max_id + 1)

    async def test_list_campaigns_filter_by_ids(self, db_session, existing_campaign_list):
        ids = [existing_campaign_list[0].id, existing_campaign_list[1].id]
        result = await campaign_service.list_campaigns(db_session, options=CampaignFilter(ids=f"{ids[0]},{ids[1]}"))
        assert result.total == 2
        assert {c.id for c in result.items} == set(ids)

    async def test_list_campaigns_filter_by_ids_not_found(self, db_session, existing_campaign_list):
        with pytest.raises(NotFoundError):
            await campaign_service.list_campaigns(db_session, options=CampaignFilter(ids="999999999999"))


class TestUpdateCampaign:
    async def test_update_campaign_name(self, db_session, existing_campaign):
        data = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client_id == existing_campaign.client_id

    async def test_update_campaign_client_id(self, db_session, existing_campaign, existing_client):
        # existing_client is a different client than the one the campaign was created with
        data = CampaignUpdate(client_id=existing_client.id)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client_id == existing_client.id

    async def test_update_campaign_name_and_client_id(self, db_session, existing_campaign, existing_client):
        data = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client_id=existing_client.id)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client_id == existing_client.id

    async def test_update_campaign_client_id_not_found(self, db_session, existing_campaign, existing_client):
        data = CampaignUpdate(client_id=existing_client.id + 999)
        with pytest.raises(NotFoundError):
            await campaign_service.update(db_session, existing_campaign.id, data)

    async def test_update_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        data = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME)
        with pytest.raises(NotFoundError) as exc_info:
            await campaign_service.update(db_session, fake_id, data)
        assert "Campaign not found" in exc_info.value.messages


class TestDeleteCampaign:
    async def test_delete_campaign(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        await campaign_service.delete(db_session, campaign_id)
        with pytest.raises(NotFoundError):
            await campaign_service.get(db_session, campaign_id)

    async def test_delete_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        with pytest.raises(NotFoundError):
            await campaign_service.delete(db_session, fake_id)

    async def test_delete_campaign_cascades_metrics(self, db_session, existing_campaign, make_metric):
        await make_metric(existing_campaign.id)
        await campaign_service.delete(db_session, existing_campaign.id)
        result = await campaign_repo.get(db_session, existing_campaign.id)
        assert result is None

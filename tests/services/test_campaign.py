import pytest
from app.services import campaign as campaign_service
from app.repositories import campaign as campaign_repo
from app.exceptions import NotFoundError
from app.schema import CampaignCreate, CampaignUpdate, PaginatedFilter
from tests.conftest import (
    VALID_CAMPAIGN_NAME,
    VALID_CAMPAIGN_CLIENT,
    UPDATE_CAMPAIGN_NAME,
    UPDATE_CAMPAIGN_CLIENT,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
    TEST_CAMPAIGN_LIST,
)
from tests.helpers.campaign import compare_campaign_list_equality


class TestCreateCampaign:
    async def test_create_campaign(self, db_session):
        data = CampaignCreate(name=VALID_CAMPAIGN_NAME, client=VALID_CAMPAIGN_CLIENT)
        campaign = await campaign_service.create(db_session, data)
        assert campaign.id is not None
        assert campaign.id > 0
        assert campaign.name == VALID_CAMPAIGN_NAME
        assert campaign.client == VALID_CAMPAIGN_CLIENT


class TestGetCampaign:
    async def test_get_campaign(self, db_session, existing_campaign):
        campaign = await campaign_service.get(db_session, existing_campaign.id)
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client == existing_campaign.client

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


class TestUpdateCampaign:
    async def test_update_campaign_name(self, db_session, existing_campaign):
        data = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == existing_campaign.client

    async def test_update_campaign_client(self, db_session, existing_campaign):
        data = CampaignUpdate(client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_name_and_client(self, db_session, existing_campaign):
        data = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await campaign_service.update(db_session, existing_campaign.id, data)
        assert campaign.id == existing_campaign.id
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

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

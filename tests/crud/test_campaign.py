import pytest
from pydantic import ValidationError

from app.crud import (
    create_campaign,
    get_campaign,
    get_total_number_of_campaigns,
    update_campaign,
    delete_campaign,
)
from app.crud.campaign import list_campaigns
from app.schema import CampaignCreate, PaginatedFilter, CampaignUpdate
from tests.conftest import (
    TEST_CAMPAIGN_CRUD,
    TEST_CAMPAIGN_LIST_CRUD,
    LONG_STRING,
    VALID_CAMPAIGN_CLIENT,
    VALID_CAMPAIGN_NAME,
    UPDATE_CAMPAIGN_CLIENT,
    UPDATE_CAMPAIGN_NAME,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
)
from tests.helpers.campaign import compare_campaign_list_equality

class TestCreateCampaign:
    async def test_create_campaign(self, db_session):
        campaign = await create_campaign(db_session, TEST_CAMPAIGN_CRUD)
        assert campaign.name == TEST_CAMPAIGN_CRUD.name
        assert campaign.client == TEST_CAMPAIGN_CRUD.client
        assert campaign.id is not None
        assert campaign.id > 0

    async def test_create_campaign_name_too_long(self, db_session):
        with pytest.raises(ValidationError):
            await create_campaign(db_session, CampaignCreate(name=LONG_STRING, client=VALID_CAMPAIGN_CLIENT))

    async def test_create_campaign_client_too_long(self, db_session):
        with pytest.raises(ValidationError):
            await create_campaign(db_session, CampaignCreate(name=VALID_CAMPAIGN_NAME, client=LONG_STRING))

    async def test_create_campaign_name_missing(self, db_session):
        with pytest.raises(ValidationError):
            await create_campaign(db_session, CampaignCreate(name=VALID_CAMPAIGN_NAME))

    async def test_create_campaign_client_missing(self, db_session):
        with pytest.raises(ValidationError):
            await create_campaign(db_session, CampaignCreate(client=VALID_CAMPAIGN_CLIENT))

class TestGetCampaign:
    async def test_get_campaign(self, db_session, existing_campaign_crud):
        campaign = await get_campaign(db_session, existing_campaign_crud.id)
        assert campaign is not None
        assert campaign.id == existing_campaign_crud.id
        assert campaign.name == existing_campaign_crud.name
        assert campaign.client == existing_campaign_crud.client

    async def test_get_campaign_not_found(self, db_session, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        campaign = await get_campaign(db_session, fake_id)
        assert campaign is None
        
class TestListCampaigns:
    async def test_list_campaigns_no_filters(self, db_session, existing_campaign_list_crud):
        campaign_list = await list_campaigns(db_session)
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST_CRUD)
    
    async def test_list_campaigns_filter_limit_is_less_than_total_items(self, db_session, existing_campaign_list_crud):
        limit = 4
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == limit
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST_CRUD)

    async def test_list_campaigns_filter_limit_is_greater_than_total_items(self, db_session, existing_campaign_list_crud):
        limit = len(TEST_CAMPAIGN_LIST_CRUD) * 2
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == len(TEST_CAMPAIGN_LIST_CRUD)
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST_CRUD)

    async def test_list_campaigns_filter_offset_result_contains_default_number_of_items(self, db_session, existing_campaign_list_crud):
        offset = 1
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST_CRUD, offset)

    async def test_list_campaigns_filter_offset_result_contains_fewer_items(self, db_session, existing_campaign_list_crud):
        expected_results_size = 2
        offset = len(TEST_CAMPAIGN_LIST_CRUD) - expected_results_size
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == expected_results_size
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST_CRUD, offset)

    async def test_list_campaigns_filter_offset_past_number_of_entries(self, db_session, existing_campaign_list_crud):
        offset = len(TEST_CAMPAIGN_LIST_CRUD)
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0

    async def test_list_campaigns_filter_no_entries(self, db_session):
        campaign_list = await list_campaigns(db_session)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0
        
class TestGetTotalNumberOfCampaigns:
    async def test_get_total_number_of_campaigns_with_entries(self, db_session, existing_campaign_list_crud):
        number_of_campaigns = await get_total_number_of_campaigns(db_session)
        assert number_of_campaigns == len(existing_campaign_list_crud)

    async def test_get_total_number_of_campaigns_no_entries(self, db_session):
        number_of_campaigns = await get_total_number_of_campaigns(db_session)
        assert number_of_campaigns == 0
        
class TestUpdateCampaign:
    async def test_update_campaign_with_name_and_client(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_with_name(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=None)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == existing_campaign_crud.client

    async def test_update_campaign_with_client(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        updated_campaign = CampaignUpdate(name=None, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == existing_campaign_crud.name
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_no_op(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        updated_campaign = CampaignUpdate(name=None, client=None)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == existing_campaign_crud.name
        assert campaign.client == existing_campaign_crud.client

    async def test_update_campaign_not_found(self, db_session, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, fake_id, updated_campaign)
        assert not campaign

class TestDeleteCampaign:
    async def test_delete_campaign(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        deleted = await delete_campaign(db_session, campaign_id)
        assert deleted

    async def test_delete_campaign_doesnt_exist(self, db_session, existing_campaign_crud):
        fake_id = existing_campaign_crud.id + 1
        deleted = await delete_campaign(db_session, fake_id)
        assert not deleted
import pytest
import pytest_asyncio
from pydantic import ValidationError

from app.constants import PAGE_LIMIT_DEFAULT
from app.crud import (
    get_campaign,
    get_total_number_of_campaigns,
    update_campaign,
    delete_campaign,
)
from app.crud.campaign import create_campaign, list_campaigns
from app.schema import CampaignCreate, PaginatedFilter, CampaignUpdate

TEST_CAMPAIGNS = [
    CampaignCreate(name="Test Campaign Name 1", client="Test Campaign Client 1"),
    CampaignCreate(name="Test Campaign Name 2", client="Test Campaign Client 2"),
    CampaignCreate(name="Test Campaign Name 3", client="Test Campaign Client 3"),
    CampaignCreate(name="Test Campaign Name 4", client="Test Campaign Client 4"),
    CampaignCreate(name="Test Campaign Name 5", client="Test Campaign Client 5"),
    CampaignCreate(name="Test Campaign Name 6", client="Test Campaign Client 6"),
    CampaignCreate(name="Test Campaign Name 7", client="Test Campaign Client 7"),
    CampaignCreate(name="Test Campaign Name 8", client="Test Campaign Client 8"),
    CampaignCreate(name="Test Campaign Name 9", client="Test Campaign Client 9"),
    CampaignCreate(name="Test Campaign Name 10", client="Test Campaign Client 10"),
    CampaignCreate(name="Test Campaign Name 11", client="Test Campaign Client 11"),
    CampaignCreate(name="Test Campaign Name 12", client="Test Campaign Client 12")
]

TEST_CAMPAIGN = CampaignCreate(name="Test Campaign Name", client="Test Campaign Client")

UPDATE_CAMPAIGN_NAME = "Update Campaign Name"
UPDATE_CAMPAIGN_CLIENT = "Update Campaign Client"
LONG_STRING = "A" * 201
VALID_CAMPAIGN_NAME = "Test Campaign Name"
VALID_CAMPAIGN_CLIENT = "Test Campaign Client"

LENGTH_OF_RESULTS_DEFAULT_FILTERS = min(len(TEST_CAMPAIGNS), PAGE_LIMIT_DEFAULT)

@pytest_asyncio.fixture
async def existing_campaign(db_session):
    return await create_campaign(db_session, TEST_CAMPAIGN)

@pytest_asyncio.fixture
async def existing_campaign_list(db_session):
    campaigns = []
    for test_campaign in TEST_CAMPAIGNS:
        campaign = await create_campaign(db_session, test_campaign)
        campaigns.append(campaign)
    return campaigns

class TestCreateCampaign:
    async def test_create_campaign(self, db_session):
        campaign = await create_campaign(db_session, TEST_CAMPAIGN)
        assert campaign.name == TEST_CAMPAIGN.name
        assert campaign.client == TEST_CAMPAIGN.client
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
    async def test_get_campaign(self, db_session, existing_campaign):
        campaign = await get_campaign(db_session, existing_campaign.id)
        assert campaign is not None
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client == existing_campaign.client

    async def test_get_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        campaign = await get_campaign(db_session, fake_id)
        assert campaign is None
        
class TestListCampaigns:
    async def test_list_campaigns_no_filters(self, db_session, existing_campaign_list):
        campaign_list = await list_campaigns(db_session)
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        for index in range(LENGTH_OF_RESULTS_DEFAULT_FILTERS):
            assert campaign_list[index].name == TEST_CAMPAIGNS[index].name
            assert campaign_list[index].client == TEST_CAMPAIGNS[index].client
    
    async def test_list_campaigns_filter_limit_is_less_than_total_items(self, db_session, existing_campaign_list):
        limit = 4
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == limit
        for index in range(limit):
            assert campaign_list[index].name == TEST_CAMPAIGNS[index].name
            assert campaign_list[index].client == TEST_CAMPAIGNS[index].client

    async def test_list_campaigns_filter_limit_is_greater_than_total_items(self, db_session, existing_campaign_list):
        limit = len(TEST_CAMPAIGNS) * 2
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == len(TEST_CAMPAIGNS)
        for index in range(len(TEST_CAMPAIGNS)):
            assert campaign_list[index].name == TEST_CAMPAIGNS[index].name
            assert campaign_list[index].client == TEST_CAMPAIGNS[index].client

    async def test_list_campaigns_filter_offset_result_contains_default_number_of_items(self, db_session, existing_campaign_list):
        offset = 1
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        for index in range(len(campaign_list)):
            assert campaign_list[index].name == TEST_CAMPAIGNS[index + offset].name
            assert campaign_list[index].client == TEST_CAMPAIGNS[index + offset].client

    async def test_list_campaigns_filter_offset_result_contains_fewer_items(self, db_session, existing_campaign_list):
        expected_results_size = 2
        offset = len(TEST_CAMPAIGNS) - expected_results_size
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == expected_results_size
        for index in range(expected_results_size):
            assert campaign_list[index].name == TEST_CAMPAIGNS[index + offset].name
            assert campaign_list[index].client == TEST_CAMPAIGNS[index + offset].client

    async def test_list_campaigns_filter_offset_past_number_of_entries(self, db_session, existing_campaign_list):
        offset = len(TEST_CAMPAIGNS)
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await list_campaigns(db_session, filter_limit)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0

    async def test_list_campaigns_filter_no_entries(self, db_session):
        campaign_list = await list_campaigns(db_session)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0
        
class TestGetTotalNumberOfCampaigns:
    async def test_get_total_number_of_campaigns_with_entries(self, db_session, existing_campaign_list):
        number_of_campaigns = await get_total_number_of_campaigns(db_session)
        assert number_of_campaigns == len(existing_campaign_list)

    async def test_get_total_number_of_campaigns_no_entries(self, db_session):
        number_of_campaigns = await get_total_number_of_campaigns(db_session)
        assert number_of_campaigns == 0
        
class TestUpdateCampaign:
    async def test_update_campaign_with_name_and_client(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_with_name(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=None)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client == existing_campaign.client

    async def test_update_campaign_with_client(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        updated_campaign = CampaignUpdate(name=None, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == existing_campaign.name
        assert campaign.client == UPDATE_CAMPAIGN_CLIENT

    async def test_update_campaign_no_op(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        updated_campaign = CampaignUpdate(name=None, client=None)
        campaign = await update_campaign(db_session, campaign_id, updated_campaign)
        assert campaign
        assert campaign.name == existing_campaign.name
        assert campaign.client == existing_campaign.client

    async def test_update_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        updated_campaign = CampaignUpdate(name=UPDATE_CAMPAIGN_NAME, client=UPDATE_CAMPAIGN_CLIENT)
        campaign = await update_campaign(db_session, fake_id, updated_campaign)
        assert not campaign

class TestDeleteCampaign:
    async def test_delete_campaign(self, db_session, existing_campaign):
        campaign_id = existing_campaign.id
        deleted = await delete_campaign(db_session, campaign_id)
        assert deleted

    async def test_delete_campaign_doesnt_exist(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        deleted = await delete_campaign(db_session, fake_id)
        assert not deleted
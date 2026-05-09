from app.repositories import campaign as campaign_repo
from app.schema import PaginatedFilter
from app.schema.campaign import CampaignFilter
from tests.conftest import (
    UPDATE_CAMPAIGN_NAME,
    VALID_CAMPAIGN_NAME,
    LENGTH_OF_RESULTS_DEFAULT_FILTERS,
    TEST_CAMPAIGN_LIST,
    TEST_CAMPAIGN_CLIENT_NAMES,
)
from tests.helpers.campaign import compare_campaign_list_equality

class TestSaveCampaign:
    async def test_save_campaign(self, db_session, campaign_factory):
        campaign = await campaign_repo.save(db_session, await campaign_factory())
        assert campaign.name == VALID_CAMPAIGN_NAME
        assert campaign.client_id is not None
        assert campaign.id is not None
        assert campaign.id > 0

    async def test_save_campaign_update_existing(self, db_session, existing_campaign_to_update, make_client):
        new_client = await make_client(name="New Client")
        existing_campaign_to_update.name = UPDATE_CAMPAIGN_NAME
        existing_campaign_to_update.client_id = new_client.id
        campaign = await campaign_repo.save(db_session, existing_campaign_to_update)
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client_id == new_client.id
        assert campaign.id == existing_campaign_to_update.id

    async def test_save_campaign_update_existing_name_only(self, db_session, existing_campaign_to_update):
        original_client_id = existing_campaign_to_update.client_id
        existing_campaign_to_update.name = UPDATE_CAMPAIGN_NAME
        campaign = await campaign_repo.save(db_session, existing_campaign_to_update)
        assert campaign.name == UPDATE_CAMPAIGN_NAME
        assert campaign.client_id == original_client_id
        assert campaign.id == existing_campaign_to_update.id

    async def test_save_campaign_update_client_id(self, db_session, existing_campaign_to_update, make_client):
        new_client = await make_client(name="Another Client")
        existing_campaign_to_update.client_id = new_client.id
        campaign = await campaign_repo.save(db_session, existing_campaign_to_update)
        assert campaign.name == existing_campaign_to_update.name
        assert campaign.client_id == new_client.id
        assert campaign.id == existing_campaign_to_update.id

class TestGetCampaign:
    async def test_get_campaign(self, db_session, existing_campaign):
        campaign = await campaign_repo.get(db_session, existing_campaign.id)
        assert campaign is not None
        assert campaign.id == existing_campaign.id
        assert campaign.name == existing_campaign.name
        assert campaign.client_id == existing_campaign.client_id

    async def test_get_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        campaign = await campaign_repo.get(db_session, fake_id)
        assert campaign is None

class TestFindAllCampaigns:
    async def test_find_all_campaigns_no_filters(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session)
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST)

    async def test_find_all_campaigns_filter_limit_is_less_than_total_items(self, db_session, existing_campaign_list):
        limit = 4
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await campaign_repo.find_all(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == limit
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST)

    async def test_find_all_campaigns_filter_limit_is_greater_than_total_items(self, db_session, existing_campaign_list):
        limit = len(TEST_CAMPAIGN_LIST) * 2
        filter_limit = PaginatedFilter(limit=limit)
        campaign_list = await campaign_repo.find_all(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == len(TEST_CAMPAIGN_LIST)
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST)

    async def test_find_all_campaigns_filter_offset_result_contains_default_number_of_items(self, db_session, existing_campaign_list):
        offset = 1
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await campaign_repo.find_all(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST, offset)

    async def test_find_all_campaigns_filter_offset_result_contains_fewer_items(self, db_session, existing_campaign_list):
        expected_results_size = 2
        offset = len(TEST_CAMPAIGN_LIST) - expected_results_size
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await campaign_repo.find_all(db_session, filter_limit)
        assert campaign_list
        assert len(campaign_list) == expected_results_size
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST, offset)

    async def test_find_all_campaigns_filter_offset_past_number_of_entries(self, db_session, existing_campaign_list):
        offset = len(TEST_CAMPAIGN_LIST)
        filter_limit = PaginatedFilter(offset=offset)
        campaign_list = await campaign_repo.find_all(db_session, filter_limit)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0

    async def test_find_all_campaigns_filter_no_entries(self, db_session):
        campaign_list = await campaign_repo.find_all(db_session)
        assert isinstance(campaign_list, list)
        assert len(campaign_list) == 0

    async def test_find_all_campaigns_filter_by_name_partial_filter_return_all_entries(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(name_filter="test"))
        assert campaign_list
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST)

    async def test_find_all_campaigns_filter_by_name_partial_filter_return_some_entries(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(name_filter="ve"))
        assert campaign_list
        assert len(campaign_list) == 4
        for campaign in campaign_list:
            assert "ve" in campaign.name.lower()

    async def test_find_all_campaigns_filter_by_name_full_name_filter_return_one_entry(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(
            name_filter=TEST_CAMPAIGN_LIST[0].name))
        assert campaign_list
        assert len(campaign_list) == 1
        assert campaign_list[0].name == TEST_CAMPAIGN_LIST[0].name

    async def test_find_all_campaigns_filter_by_name_no_entry(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(name_filter="Invalid Filter"))
        assert len(campaign_list) == 0

    async def test_find_all_campaigns_filter_by_client_partial_filter_return_all_entries(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(client_name_filter="test"))
        assert campaign_list
        assert len(campaign_list) == LENGTH_OF_RESULTS_DEFAULT_FILTERS
        compare_campaign_list_equality(campaign_list, TEST_CAMPAIGN_LIST)

    async def test_find_all_campaigns_filter_by_client_partial_filter_return_some_entries(self, db_session, existing_campaign_list):
        # "ve" in client name: Five, Seven, Eleven, Twelve — 4 entries
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(client_name_filter="ve"))
        assert campaign_list
        assert len(campaign_list) == 4
        for campaign in campaign_list:
            assert campaign.client_id is not None

    async def test_find_all_campaigns_filter_by_client_full_client_filter_return_one_entry(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None,
                                                     CampaignFilter(client_name_filter=TEST_CAMPAIGN_CLIENT_NAMES[0]))
        assert campaign_list
        assert len(campaign_list) == 1
        assert campaign_list[0].client_id == existing_campaign_list[0].client_id

    async def test_find_all_campaigns_filter_by_client_no_entry(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None, CampaignFilter(client_name_filter="Invalid Filter"))
        assert len(campaign_list) == 0

    async def test_find_all_campaigns_filter_by_name_and_client_full_client_filter_return_one_entry(self, db_session, existing_campaign_list):
        campaign_list = await campaign_repo.find_all(db_session, None,
                                                     CampaignFilter(name_filter="ev", client_name_filter="ve"))
        assert campaign_list
        assert len(campaign_list) == 2
        for campaign in campaign_list:
            assert "ev" in campaign.name.lower()
            assert campaign.client_id is not None

class TestGetTotalNumberOfCampaigns:
    async def test_count_campaign_with_entries(self, db_session, existing_campaign_list):
        number_of_campaigns = await campaign_repo.count(db_session)
        assert number_of_campaigns == len(existing_campaign_list)

    async def test_count_campaign_no_entries(self, db_session):
        number_of_campaigns = await campaign_repo.count(db_session)
        assert number_of_campaigns == 0

    async def test_count_campaign_filter_by_name_matches_all(self, db_session, existing_campaign_list):
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(name_filter="test"))
        assert number_of_campaigns == len(existing_campaign_list)

    async def test_count_campaign_filter_by_name_matches_some(self, db_session, existing_campaign_list):
        # "ve" appears in Five, Seven, Eleven, Twelve — 4 entries
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(name_filter="ve"))
        assert number_of_campaigns == 4

    async def test_count_campaign_filter_by_name_matches_none(self, db_session, existing_campaign_list):
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(name_filter="Invalid"))
        assert number_of_campaigns == 0

    async def test_count_campaign_filter_by_client_matches_all(self, db_session, existing_campaign_list):
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(client_name_filter="test"))
        assert number_of_campaigns == len(existing_campaign_list)

    async def test_count_campaign_filter_by_client_matches_some(self, db_session, existing_campaign_list):
        # "ve" in client name: Five, Seven, Eleven, Twelve — 4 entries
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(client_name_filter="ve"))
        assert number_of_campaigns == 4

    async def test_count_campaign_filter_by_name_and_client(self, db_session, existing_campaign_list):
        # name contains "ev" and client name contains "ve": Seven, Eleven — 2 entries
        number_of_campaigns = await campaign_repo.count(db_session, CampaignFilter(name_filter="ev", client_name_filter="ve"))
        assert number_of_campaigns == 2

class TestDeleteCampaign:
    async def test_delete_campaign(self, db_session, existing_campaign):
        await campaign_repo.delete(db_session, existing_campaign)
        result = await campaign_repo.get(db_session, existing_campaign.id)
        assert result is None
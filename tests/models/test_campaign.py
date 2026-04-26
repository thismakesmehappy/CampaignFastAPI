import pytest

from app.models.campaign import Campaign
from app.constants import CAMPAIGN_NAME_MAX_LENGTH, CAMPAIGN_CLIENT_MAX_LENGTH

VALID_NAME = "Test Campaign"
VALID_CLIENT = "Test Client"
LONG_NAME = "A" * (CAMPAIGN_NAME_MAX_LENGTH + 1)
LONG_CLIENT = "A" * (CAMPAIGN_CLIENT_MAX_LENGTH + 1)
MAX_NAME = "A" * CAMPAIGN_NAME_MAX_LENGTH
MAX_CLIENT = "A" * CAMPAIGN_CLIENT_MAX_LENGTH


class TestCampaignModel:
    def test_valid_campaign(self):
        campaign = Campaign(name=VALID_NAME, client=VALID_CLIENT)
        assert campaign.name == VALID_NAME
        assert campaign.client == VALID_CLIENT

    def test_name_at_max_length(self):
        campaign = Campaign(name=MAX_NAME, client=VALID_CLIENT)
        assert campaign.name == MAX_NAME

    def test_client_at_max_length(self):
        campaign = Campaign(name=VALID_NAME, client=MAX_CLIENT)
        assert campaign.client == MAX_CLIENT

    def test_name_too_long(self):
        with pytest.raises(ValueError):
            Campaign(name=LONG_NAME, client=VALID_CLIENT)

    def test_client_too_long(self):
        with pytest.raises(ValueError):
            Campaign(name=VALID_NAME, client=LONG_CLIENT)

    def test_name_none(self):
        with pytest.raises(ValueError):
            Campaign(name=None, client=VALID_CLIENT)

    def test_client_none(self):
        with pytest.raises(ValueError):
            Campaign(name=VALID_NAME, client=None)
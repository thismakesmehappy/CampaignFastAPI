import pytest

from app.models.campaign import Campaign
from app.constants import CAMPAIGN_NAME_MAX_LENGTH

VALID_NAME = "Test Campaign"
LONG_NAME = "A" * (CAMPAIGN_NAME_MAX_LENGTH + 1)
MAX_NAME = "A" * CAMPAIGN_NAME_MAX_LENGTH


class TestCampaignModel:
    def test_valid_campaign(self):
        campaign = Campaign(name=VALID_NAME, client_id=1)
        assert campaign.name == VALID_NAME
        assert campaign.client_id == 1

    def test_name_at_max_length(self):
        campaign = Campaign(name=MAX_NAME, client_id=1)
        assert campaign.name == MAX_NAME

    def test_name_too_long(self):
        with pytest.raises(ValueError):
            Campaign(name=LONG_NAME, client_id=1)

    def test_name_none(self):
        with pytest.raises(ValueError):
            Campaign(name=None, client_id=1)
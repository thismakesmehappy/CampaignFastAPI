import pytest

from app.models.metric import Metric
from datetime import datetime, timezone

VALID_CAMPAIGN_ID = 1
VALID_SPEND = 10.0
VALID_CLICKS = 5
VALID_IMPRESSIONS = 100
PERIOD_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 1, 31, tzinfo=timezone.utc)


class TestMetricModel:
    def test_valid_metric(self):
        metric = Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)
        assert metric.campaign_id == VALID_CAMPAIGN_ID
        assert metric.spend == VALID_SPEND
        assert metric.clicks == VALID_CLICKS
        assert metric.impressions == VALID_IMPRESSIONS

    def test_spend_zero(self):
        metric = Metric(campaign_id=VALID_CAMPAIGN_ID, spend=0, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)
        assert metric.spend == 0

    def test_clicks_zero(self):
        metric = Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=0, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)
        assert metric.clicks == 0

    def test_impressions_zero(self):
        metric = Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=0, period_start=PERIOD_START, period_end=PERIOD_END)
        assert metric.impressions == 0

    def test_spend_negative(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=-1, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_clicks_negative(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=-1, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_impressions_negative(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=-1, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_campaign_id_zero(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=0, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_campaign_id_negative(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=-1, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_campaign_id_none(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=None, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_spend_none(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=None, clicks=VALID_CLICKS, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_clicks_none(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=None, impressions=VALID_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)

    def test_impressions_none(self):
        with pytest.raises(ValueError):
            Metric(campaign_id=VALID_CAMPAIGN_ID, spend=VALID_SPEND, clicks=VALID_CLICKS, impressions=None, period_start=PERIOD_START, period_end=PERIOD_END)
import pytest
from datetime import datetime, timezone
from app.services import metric as metric_service
from app.exceptions import NotFoundError, DomainValidationError
from app.schema import MetricCreate, MetricUpdate, PaginatedFilter
from tests.conftest import (
    TEST_METRIC_SPEND,
    TEST_METRIC_CLICKS,
    TEST_METRIC_IMPRESSIONS,
    UPDATE_METRIC_SPEND,
    UPDATE_METRIC_CLICKS,
    UPDATE_METRIC_IMPRESSIONS,
    UPDATE_METRIC_PERIOD_START,
    UPDATE_METRIC_PERIOD_END,
    PERIOD_START,
    PERIOD_END,
    LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS,
    SUMMARY_TOTAL_SPEND,
    SUMMARY_TOTAL_CLICKS,
    SUMMARY_TOTAL_IMPRESSIONS,
)


class TestCreateMetric:
    async def test_create_metric(self, db_session, existing_campaign):
        data = MetricCreate(spend=TEST_METRIC_SPEND, clicks=TEST_METRIC_CLICKS, impressions=TEST_METRIC_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)
        metric = await metric_service.create(db_session, existing_campaign.id, data)
        assert metric.id is not None
        assert metric.id > 0
        assert metric.campaign_id == existing_campaign.id
        assert metric.spend == TEST_METRIC_SPEND
        assert metric.clicks == TEST_METRIC_CLICKS
        assert metric.impressions == TEST_METRIC_IMPRESSIONS
        assert metric.period_start == PERIOD_START
        assert metric.period_end == PERIOD_END

    async def test_create_metric_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        data = MetricCreate(spend=TEST_METRIC_SPEND, clicks=TEST_METRIC_CLICKS, impressions=TEST_METRIC_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.create(db_session, fake_id, data)
        assert "Campaign not found" in exc_info.value.messages

class TestGetMetric:
    async def test_get_metric(self, db_session, existing_metric):
        metric = await metric_service.get(db_session, existing_metric.id)
        assert metric.id == existing_metric.id
        assert metric.campaign_id == existing_metric.campaign_id
        assert metric.spend == existing_metric.spend
        assert metric.clicks == existing_metric.clicks
        assert metric.impressions == existing_metric.impressions

    async def test_get_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.get(db_session, fake_id)
        assert "Metric not found" in exc_info.value.messages


class TestListMetrics:
    async def test_list_metrics_no_filters(self, db_session, existing_metric_list):
        pagination = PaginatedFilter()
        response = await metric_service.list_metrics(db_session, pagination)
        assert response.total == 12
        assert len(response.items) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS
        assert response.offset == 0
        assert response.has_more is True

    async def test_list_metrics_for_campaign(self, db_session, existing_metric_list):
        campaign_id = existing_metric_list.id
        pagination = PaginatedFilter()
        response = await metric_service.list_metrics(db_session, pagination, campaign_id)
        assert response.total == 12
        assert len(response.items) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS

    async def test_list_metrics_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.list_metrics(db_session, PaginatedFilter(), fake_id)
        assert "Campaign not found" in exc_info.value.messages

    async def test_list_metrics_no_entries(self, db_session):
        pagination = PaginatedFilter()
        response = await metric_service.list_metrics(db_session, pagination)
        assert response.total == 0
        assert len(response.items) == 0
        assert response.has_more is False


class TestListMetricsSummary:
    async def test_summary_all(self, db_session, existing_metrics_across_campaigns):
        summary = await metric_service.list_metrics_summary(db_session)
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS

    async def test_summary_for_campaign(self, db_session, existing_metrics_single_campaign):
        campaign_id = existing_metrics_single_campaign.id
        summary = await metric_service.list_metrics_summary(db_session, campaign_id)
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS

    async def test_summary_campaign_not_found(self, db_session, existing_campaign):
        fake_id = existing_campaign.id + 1
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.list_metrics_summary(db_session, fake_id)
        assert "Campaign not found" in exc_info.value.messages

    async def test_summary_no_entries(self, db_session):
        summary = await metric_service.list_metrics_summary(db_session)
        assert summary.spend == 0
        assert summary.clicks == 0
        assert summary.impressions == 0


class TestUpdateMetric:
    async def test_update_metric_spend(self, db_session, existing_metric):
        data = MetricUpdate(spend=UPDATE_METRIC_SPEND)
        metric = await metric_service.update(db_session, existing_metric.id, data)
        assert metric.spend == UPDATE_METRIC_SPEND
        assert metric.clicks == existing_metric.clicks
        assert metric.impressions == existing_metric.impressions

    async def test_update_metric_clicks(self, db_session, existing_metric):
        data = MetricUpdate(clicks=UPDATE_METRIC_CLICKS)
        metric = await metric_service.update(db_session, existing_metric.id, data)
        assert metric.clicks == UPDATE_METRIC_CLICKS
        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions

    async def test_update_metric_impressions(self, db_session, existing_metric):
        data = MetricUpdate(impressions=UPDATE_METRIC_IMPRESSIONS)
        metric = await metric_service.update(db_session, existing_metric.id, data)
        assert metric.impressions == UPDATE_METRIC_IMPRESSIONS
        assert metric.spend == existing_metric.spend
        assert metric.clicks == existing_metric.clicks

    async def test_update_metric_period(self, db_session, existing_metric):
        data = MetricUpdate(period_start=UPDATE_METRIC_PERIOD_START, period_end=UPDATE_METRIC_PERIOD_END)
        metric = await metric_service.update(db_session, existing_metric.id, data)
        assert metric.period_start == UPDATE_METRIC_PERIOD_START
        assert metric.period_end == UPDATE_METRIC_PERIOD_END

    async def test_update_metric_invalid_period(self, db_session, existing_metric):
        data = MetricUpdate(period_start=UPDATE_METRIC_PERIOD_END, period_end=UPDATE_METRIC_PERIOD_START)
        with pytest.raises(DomainValidationError):
            await metric_service.update(db_session, existing_metric.id, data)

    async def test_update_metric_period_start_after_existing_end(self, db_session, existing_metric):
        # existing period_end is PERIOD_END (Jan 31); moving start past it makes start > end
        data = MetricUpdate(period_start=UPDATE_METRIC_PERIOD_END)
        with pytest.raises(DomainValidationError):
            await metric_service.update(db_session, existing_metric.id, data)

    async def test_update_metric_period_end_before_existing_start(self, db_session, existing_metric):
        # existing period_start is PERIOD_START (Jan 1); moving end before it makes end < start
        before_period_start = datetime(2025, 12, 31, tzinfo=timezone.utc)
        data = MetricUpdate(period_end=before_period_start)
        with pytest.raises(DomainValidationError):
            await metric_service.update(db_session, existing_metric.id, data)

    async def test_update_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        data = MetricUpdate(spend=UPDATE_METRIC_SPEND)
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.update(db_session, fake_id, data)
        assert "Metric not found" in exc_info.value.messages


class TestDeleteMetric:
    async def test_delete_metric(self, db_session, existing_metric):
        metric_id = existing_metric.id
        await metric_service.delete(db_session, metric_id)
        with pytest.raises(NotFoundError):
            await metric_service.get(db_session, metric_id)

    async def test_delete_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        with pytest.raises(NotFoundError) as exc_info:
            await metric_service.delete(db_session, fake_id)
        assert "Metric not found" in exc_info.value.messages
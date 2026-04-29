import pytest_asyncio

from app.repositories import metric as metric_repo
from app.schema import PaginatedFilter
from tests.conftest import (
    TEST_METRICS_MULTI as TEST_METRICS,
    SUMMARY_TOTAL_CLICKS,
    SUMMARY_TOTAL_SPEND,
    SUMMARY_TOTAL_IMPRESSIONS,
    PERIOD_START,
    PERIOD_END,
    UPDATE_METRIC_PERIOD_START,
    UPDATE_METRIC_PERIOD_END,
    TEST_METRIC_SPEND,
    TEST_METRIC_CLICKS,
    TEST_METRIC_IMPRESSIONS,
)

UPDATE_METRIC_SPEND = 200
UPDATE_METRIC_CLICKS = 100
UPDATE_METRIC_IMPRESSIONS = 400

@pytest_asyncio.fixture
async def existing_metric(db_session, make_metric, make_campaign):
    campaign = await make_campaign()
    return await make_metric(campaign.id, spend=TEST_METRIC_SPEND, clicks=TEST_METRIC_CLICKS, impressions=TEST_METRIC_IMPRESSIONS, period_start=PERIOD_START, period_end=PERIOD_END)


class TestSaveMetric:
    async def test_save_metric(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == campaign_id
        
        assert metric.spend == TEST_METRIC_SPEND
        assert metric.impressions == TEST_METRIC_IMPRESSIONS
        assert metric.clicks == TEST_METRIC_CLICKS
        assert metric.id is not None
        assert metric.id > 0

    async def test_save_metric_update_existing(self, db_session, existing_metric):
        existing_metric.spend = UPDATE_METRIC_SPEND
        existing_metric.impressions = UPDATE_METRIC_IMPRESSIONS
        existing_metric.clicks = UPDATE_METRIC_CLICKS
        existing_metric.period_start = UPDATE_METRIC_PERIOD_START
        existing_metric.period_end = UPDATE_METRIC_PERIOD_END
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id
        
        assert metric.spend == UPDATE_METRIC_SPEND
        assert metric.impressions == UPDATE_METRIC_IMPRESSIONS
        assert metric.clicks == UPDATE_METRIC_CLICKS
        assert metric.period_start == UPDATE_METRIC_PERIOD_START
        assert metric.period_end == UPDATE_METRIC_PERIOD_END

    async def test_save_metric_update_existing_spend_only(self, db_session, existing_metric):
        existing_metric.spend = UPDATE_METRIC_SPEND
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id

        assert metric.spend == UPDATE_METRIC_SPEND
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == existing_metric.clicks
        assert metric.period_start == existing_metric.period_start
        assert metric.period_end == existing_metric.period_end

    async def test_save_metric_update_existing_impressions_only(self, db_session, existing_metric):
        existing_metric.impressions = UPDATE_METRIC_IMPRESSIONS
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id

        assert metric.spend == existing_metric.spend
        assert metric.impressions == UPDATE_METRIC_IMPRESSIONS
        assert metric.clicks == existing_metric.clicks
        assert metric.period_start == existing_metric.period_start
        assert metric.period_end == existing_metric.period_end

    async def test_save_metric_update_existing_clicks_only(self, db_session, existing_metric):
        existing_metric.clicks = UPDATE_METRIC_CLICKS
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id

        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == UPDATE_METRIC_CLICKS
        assert metric.period_start == existing_metric.period_start
        assert metric.period_end == existing_metric.period_end

    async def test_save_metric_update_existing_period_start_only(self, db_session, existing_metric):
        existing_metric.period_start = UPDATE_METRIC_PERIOD_START
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id

        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == existing_metric.clicks
        assert metric.period_start == UPDATE_METRIC_PERIOD_START
        assert metric.period_end == existing_metric.period_end

    async def test_save_metric_update_existing_period_end_only(self, db_session, existing_metric):
        existing_metric.period_end = UPDATE_METRIC_PERIOD_END
        metric = await metric_repo.save(db_session, existing_metric)
        assert metric is not None
        assert metric.id is not None
        assert metric.campaign_id == existing_metric.campaign_id

        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == existing_metric.clicks
        assert metric.period_start == existing_metric.period_start
        assert metric.period_end == UPDATE_METRIC_PERIOD_END

class TestGetMetric:
    async def test_get_metric(self, db_session, existing_metric):
        metric = await metric_repo.get(db_session, existing_metric.id)
        assert metric is not None
        assert metric.campaign_id == existing_metric.campaign_id
        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == existing_metric.clicks

    async def test_get_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        metric = await metric_repo.get(db_session, fake_id)
        assert metric is None
        
class TestFindAllMetrics:
    async def test_find_all_metrics(self, db_session, existing_metrics_across_campaigns):
        metric_list = await metric_repo.find_all(db_session)
        assert len(metric_list) == len(TEST_METRICS)
        for index in range(len(metric_list)):
            assert metric_list[index].clicks == TEST_METRICS[index].clicks
            assert metric_list[index].spend == TEST_METRICS[index].spend
            assert metric_list[index].impressions == TEST_METRICS[index].impressions
            
    async def test_find_all_metrics_with_offset(self, db_session, existing_metrics_across_campaigns):
        offset = 1
        filter_offset = PaginatedFilter(offset=offset)
        metric_list = await metric_repo.find_all(db_session, filter_offset)
        assert len(metric_list) == len(TEST_METRICS) - offset
        for index in range(len(metric_list)):
            assert metric_list[index].clicks == TEST_METRICS[index + offset].clicks
            assert metric_list[index].spend == TEST_METRICS[index + offset].spend
            assert metric_list[index].impressions == TEST_METRICS[index + offset].impressions

    async def test_find_all_metrics_with_limit(self, db_session, existing_metrics_across_campaigns):
        limit = 2
        filter_offset = PaginatedFilter(limit=limit)
        metric_list = await metric_repo.find_all(db_session, filter_offset)
        assert len(metric_list) == limit
        for index in range(limit):
            assert metric_list[index].clicks == TEST_METRICS[index].clicks
            assert metric_list[index].spend == TEST_METRICS[index].spend
            assert metric_list[index].impressions == TEST_METRICS[index].impressions

    async def test_find_all_metrics_with_campaign_id(self, db_session, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns['campaign_ids']
        position = 1
        campaign_id = campaign_ids[position]

        metric_list = await metric_repo.find_all(db_session, None, campaign_id)
        assert len(metric_list) == 1
        assert metric_list[0].clicks == TEST_METRICS[position].clicks
        assert metric_list[0].spend == TEST_METRICS[position].spend
        assert metric_list[0].impressions == TEST_METRICS[position].impressions

    async def test_find_all_metrics_no_entries(self, db_session):
        metric_list = await metric_repo.find_all(db_session)
        assert len(metric_list) == 0
        
class TestCountMetrics:
    async def test_count_metrics_with_entries(self, db_session, existing_metrics_across_campaigns):
        number_of_metrics = await metric_repo.count(db_session)
        assert number_of_metrics == len(existing_metrics_across_campaigns["metrics"])

    async def test_count_metrics_no_entries(self, db_session):
        number_of_metrics = await metric_repo.count(db_session)
        assert number_of_metrics == 0

    async def test_count_metrics_filtered_by_campaign(self, db_session, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns["campaign_ids"]
        number_of_metrics = await metric_repo.count(db_session, campaign_ids[0])
        assert number_of_metrics == 1

class TestMetricsSummary:
    async def test_summarize(self, db_session, existing_metrics_across_campaigns):
        summary = await metric_repo.summarize(db_session)
        assert summary
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS
        
    async def test_summarize_no_entries(self, db_session):
        summary = await metric_repo.summarize(db_session)
        assert summary
        assert summary.clicks == 0
        assert summary.spend == 0
        assert summary.impressions == 0
        
    async def test_summarize_for_campaign(self, db_session, existing_metrics_single_campaign):
        campaign_id = existing_metrics_single_campaign.id
        summary = await metric_repo.summarize(db_session, campaign_id)
        assert summary
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS

    async def test_summarize_for_campaign_no_entries(self, db_session, make_campaign):
        campaign = await make_campaign()
        campaign_id = campaign.id
        summary = await metric_repo.summarize(db_session, campaign_id)
        assert summary
        assert summary.clicks == 0
        assert summary.spend == 0
        assert summary.impressions == 0

    async def test_summarize_for_campaign_only_shows_campaigns_results(self, db_session, existing_metrics_across_campaigns):
        metric = existing_metrics_across_campaigns['metrics'][0]
        campaign_id = metric.campaign_id
        summary = await metric_repo.summarize(db_session, campaign_id)
        assert summary
        assert summary.clicks == metric.clicks
        assert summary.spend == metric.spend
        assert summary.impressions == metric.impressions

class TestDeleteMetric:
    async def test_delete_metric(self, db_session, existing_metric):
        metric_id = existing_metric.id
        await metric_repo.delete(db_session, existing_metric)
        result = await metric_repo.get(db_session, metric_id)
        assert result is None
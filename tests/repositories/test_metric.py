import pytest_asyncio
from datetime import datetime, timezone

from app.repositories import metric as metric_repo
from app.schema import PaginatedFilter
from app.schema.metric import MetricFilter
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

    async def test_filter_by_campaign_name(self, db_session, existing_metrics_for_campaign_filter):
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(campaign_name_filter="Test"))
        assert len(metric_list) == 4

    async def test_filter_by_campaign_name_no_match(self, db_session, existing_metrics_for_campaign_filter):
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(campaign_name_filter="Invalid"))
        assert len(metric_list) == 0

    async def test_filter_by_campaign_client(self, db_session, existing_metrics_for_campaign_filter):
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(
            client_name_filter="Acme"))
        assert len(metric_list) == 4

    async def test_filter_by_campaign_client_no_match(self, db_session, existing_metrics_for_campaign_filter):
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(
            client_name_filter="Invalid"))
        assert len(metric_list) == 0

    async def test_filter_by_campaign_name_and_client(self, db_session, existing_metrics_for_campaign_filter):
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(campaign_name_filter="Test", client_name_filter="Acme"))
        assert len(metric_list) == 3

    async def test_filter_by_min_spend(self, db_session, existing_metric_list):
        # TEST_METRIC_LIST: spend=i*10 for i in 1..12; spend>=50 means i>=5, so 8 results (capped at default limit 10)
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(min_spend=50.0))
        assert len(metric_list) == 8
        for metric in metric_list:
            assert metric.spend >= 50.0

    async def test_filter_by_max_spend(self, db_session, existing_metric_list):
        # spend<=50 means i<=5, so 5 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(max_spend=50.0))
        assert len(metric_list) == 5
        for metric in metric_list:
            assert metric.spend <= 50.0

    async def test_filter_by_spend_range(self, db_session, existing_metric_list):
        # spend between 20 and 60 means i in 2..6, so 5 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(min_spend=20.0, max_spend=60.0))
        assert len(metric_list) == 5
        for metric in metric_list:
            assert 20.0 <= metric.spend <= 60.0

    async def test_filter_by_min_clicks(self, db_session, existing_metric_list):
        # clicks=i*5 for i in 1..12; clicks>=25 means i>=5, so 8 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(min_clicks=25))
        assert len(metric_list) == 8
        for metric in metric_list:
            assert metric.clicks >= 25

    async def test_filter_by_max_clicks(self, db_session, existing_metric_list):
        # clicks<=25 means i<=5, so 5 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(max_clicks=25))
        assert len(metric_list) == 5
        for metric in metric_list:
            assert metric.clicks <= 25

    async def test_filter_by_min_impressions(self, db_session, existing_metric_list):
        # impressions=i*100 for i in 1..12; impressions>=500 means i>=5, so 8 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(min_impressions=500))
        assert len(metric_list) == 8
        for metric in metric_list:
            assert metric.impressions >= 500

    async def test_filter_by_max_impressions(self, db_session, existing_metric_list):
        # impressions<=500 means i<=5, so 5 results
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(max_impressions=500))
        assert len(metric_list) == 5
        for metric in metric_list:
            assert metric.impressions <= 500

    async def test_filter_by_period_start(self, db_session, existing_metric_list):
        # period_start=datetime(2026, 1, i); i>=6 means 7 results
        after = datetime(2026, 1, 6, tzinfo=timezone.utc)
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(period_start=after))
        assert len(metric_list) == 7
        for metric in metric_list:
            assert metric.period_start >= after

    async def test_filter_by_period_end(self, db_session, existing_metric_list):
        # period_end=datetime(2026, 1, i); i<=6 means 6 results
        before = datetime(2026, 1, 6, tzinfo=timezone.utc)
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(period_end=before))
        assert len(metric_list) == 6
        for metric in metric_list:
            assert metric.period_end <= before

    async def test_filter_by_period_range(self, db_session, existing_metric_list):
        # i>=3 and i<=8 means i in 3..8, so 6 results
        after = datetime(2026, 1, 3, tzinfo=timezone.utc)
        before = datetime(2026, 1, 8, tzinfo=timezone.utc)
        metric_list = await metric_repo.find_all(db_session, options=MetricFilter(period_start=after, period_end=before))
        assert len(metric_list) == 6
        for metric in metric_list:
            assert metric.period_start >= after
            assert metric.period_end <= before


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

    async def test_count_filter_by_campaign_name(self, db_session, existing_metrics_for_campaign_filter):
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(campaign_name_filter="Test"))
        assert number_of_metrics == 4

    async def test_count_filter_by_campaign_name_no_match(self, db_session, existing_metrics_for_campaign_filter):
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(campaign_name_filter="Invalid"))
        assert number_of_metrics == 0

    async def test_count_filter_by_campaign_client(self, db_session, existing_metrics_for_campaign_filter):
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(client_name_filter="Acme"))
        assert number_of_metrics == 4

    async def test_count_filter_by_campaign_name_and_client(self, db_session, existing_metrics_for_campaign_filter):
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(campaign_name_filter="Test", client_name_filter="Acme"))
        assert number_of_metrics == 3

    async def test_count_filter_by_min_spend(self, db_session, existing_metric_list):
        # spend=i*10 for i in 1..12; spend>=50 means i>=5, so 8 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(min_spend=50.0))
        assert number_of_metrics == 8

    async def test_count_filter_by_max_spend(self, db_session, existing_metric_list):
        # spend<=50 means i<=5, so 5 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(max_spend=50.0))
        assert number_of_metrics == 5

    async def test_count_filter_by_spend_range(self, db_session, existing_metric_list):
        # spend between 20 and 60 means i in 2..6, so 5 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(min_spend=20.0, max_spend=60.0))
        assert number_of_metrics == 5

    async def test_count_filter_by_min_clicks(self, db_session, existing_metric_list):
        # clicks=i*5 for i in 1..12; clicks>=25 means i>=5, so 8 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(min_clicks=25))
        assert number_of_metrics == 8

    async def test_count_filter_by_max_clicks(self, db_session, existing_metric_list):
        # clicks<=25 means i<=5, so 5 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(max_clicks=25))
        assert number_of_metrics == 5

    async def test_count_filter_by_min_impressions(self, db_session, existing_metric_list):
        # impressions=i*100 for i in 1..12; impressions>=500 means i>=5, so 8 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(min_impressions=500))
        assert number_of_metrics == 8

    async def test_count_filter_by_max_impressions(self, db_session, existing_metric_list):
        # impressions<=500 means i<=5, so 5 results
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(max_impressions=500))
        assert number_of_metrics == 5

    async def test_count_filter_by_period_start(self, db_session, existing_metric_list):
        # period_start=datetime(2026, 1, i); i>=6 means 7 results
        after = datetime(2026, 1, 6, tzinfo=timezone.utc)
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(period_start=after))
        assert number_of_metrics == 7

    async def test_count_filter_by_period_end(self, db_session, existing_metric_list):
        # period_end=datetime(2026, 1, i); i<=6 means 6 results
        before = datetime(2026, 1, 6, tzinfo=timezone.utc)
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(period_end=before))
        assert number_of_metrics == 6

    async def test_count_filter_by_period_range(self, db_session, existing_metric_list):
        # i>=3 and i<=8 means i in 3..8, so 6 results
        after = datetime(2026, 1, 3, tzinfo=timezone.utc)
        before = datetime(2026, 1, 8, tzinfo=timezone.utc)
        number_of_metrics = await metric_repo.count(db_session, options=MetricFilter(period_start=after, period_end=before))
        assert number_of_metrics == 6

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

    async def test_summarize_filter_by_min_spend(self, db_session, existing_metric_list):
        # spend=i*10 for i in 1..12; spend>=50 means i>=5: spend sum=50+60+...+120=780, clicks=25+30+...+60=340, impressions=500+...+1200=7800 (but default limit 10 doesn't apply to summarize)
        summary = await metric_repo.summarize(db_session, options=MetricFilter(min_spend=50.0))
        assert summary.spend == sum(i * 10 for i in range(5, 13))
        assert summary.clicks == sum(i * 5 for i in range(5, 13))
        assert summary.impressions == sum(i * 100 for i in range(5, 13))

    async def test_summarize_filter_by_max_spend(self, db_session, existing_metric_list):
        # spend<=50 means i<=5
        summary = await metric_repo.summarize(db_session, options=MetricFilter(max_spend=50.0))
        assert summary.spend == sum(i * 10 for i in range(1, 6))
        assert summary.clicks == sum(i * 5 for i in range(1, 6))
        assert summary.impressions == sum(i * 100 for i in range(1, 6))

    async def test_summarize_filter_by_spend_range(self, db_session, existing_metric_list):
        # spend between 20 and 60 means i in 2..6
        summary = await metric_repo.summarize(db_session, options=MetricFilter(min_spend=20.0, max_spend=60.0))
        assert summary.spend == sum(i * 10 for i in range(2, 7))

    async def test_summarize_filter_by_period_range(self, db_session, existing_metric_list):
        # i>=3 and i<=8 means i in 3..8
        after = datetime(2026, 1, 3, tzinfo=timezone.utc)
        before = datetime(2026, 1, 8, tzinfo=timezone.utc)
        summary = await metric_repo.summarize(db_session, options=MetricFilter(period_start=after, period_end=before))
        assert summary.spend == sum(i * 10 for i in range(3, 9))
        assert summary.clicks == sum(i * 5 for i in range(3, 9))
        assert summary.impressions == sum(i * 100 for i in range(3, 9))

    async def test_summarize_filter_by_campaign_name(self, db_session, existing_metrics_for_campaign_filter):
        # "Test" matches 4 campaigns: spend=1.1+2.2+3.3+5.5=12.1
        summary = await metric_repo.summarize(db_session, options=MetricFilter(campaign_name_filter="Test"))
        assert round(summary.spend, 2) == round(1.1 + 2.2 + 3.3 + 5.5, 2)

    async def test_summarize_filter_by_campaign_name_and_client(self, db_session, existing_metrics_for_campaign_filter):
        # name="Test" AND client="Acme" matches 3 campaigns: spend=1.1+2.2+3.3=6.6
        summary = await metric_repo.summarize(db_session, options=MetricFilter(campaign_name_filter="Test", client_name_filter="Acme"))
        assert round(summary.spend, 2) == round(1.1 + 2.2 + 3.3, 2)

    async def test_summarize_filter_no_match(self, db_session, existing_metric_list):
        summary = await metric_repo.summarize(db_session, options=MetricFilter(min_spend=9999.0))
        assert summary.spend == 0
        assert summary.clicks == 0
        assert summary.impressions == 0

class TestDeleteMetric:
    async def test_delete_metric(self, db_session, existing_metric):
        metric_id = existing_metric.id
        await metric_repo.delete(db_session, existing_metric)
        result = await metric_repo.get(db_session, metric_id)
        assert result is None
import pytest
import pytest_asyncio

from app.crud.metric import (
    create_metric,
    get_metric,
    list_metrics,
    get_total_number_of_metrics,
    update_metric,
    delete_metric,
    get_metrics_summary,
)
from app.schema import MetricBase, MetricCreate, MetricUpdate, PaginatedFilter
from tests.conftest import (
    TEST_CAMPAIGN_CRUD,
    TEST_METRICS_MULTI as TEST_METRICS,
    SUMMARY_TOTAL_CLICKS,
    SUMMARY_TOTAL_SPEND,
    SUMMARY_TOTAL_IMPRESSIONS,
    PERIOD_START,
    PERIOD_END,
)

TEST_METRIC = MetricCreate(spend=1, clicks=2, impressions=3, period_start=PERIOD_START, period_end=PERIOD_END)

UPDATE_METRIC_SPEND = 200
UPDATE_METRIC_CLICKS = 100
UPDATE_METRIC_IMPRESSIONS = 400

@pytest_asyncio.fixture
async def existing_metric(db_session, make_metric, make_campaign):
    campaign = await make_campaign(name=TEST_CAMPAIGN_CRUD.name, client=TEST_CAMPAIGN_CRUD.client)
    return await make_metric(campaign.id, spend=TEST_METRIC.spend, clicks=TEST_METRIC.clicks, impressions=TEST_METRIC.impressions)


class TestCreateMetric:
    async def test_create_metric(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        metric = await create_metric(db_session, campaign_id, TEST_METRIC)
        assert metric is not None
        assert metric.campaign_id == campaign_id
        assert metric.spend == TEST_METRIC.spend
        assert metric.impressions == TEST_METRIC.impressions
        assert metric.clicks == TEST_METRIC.clicks
        assert metric.id is not None
        assert metric.id > 0

    async def test_create_metric_no_spend(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(clicks=0, impressions=0))

    async def test_create_metric_no_clicks(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(spend=0, impressions=0))

    async def test_create_metric_no_impressions(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(clicks=0, spend=0))

    async def test_create_metric_negative_spend(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(spend=-1, clicks=0, impressions=0))

    async def test_create_metric_negative_clicks(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(spend=0, clicks=-1, impressions=0))

    async def test_create_metric_negative_impressions(self, db_session, existing_metric):
        campaign_id = existing_metric.campaign_id
        with pytest.raises(ValueError):
            await create_metric(db_session, campaign_id, MetricBase(spend=0, clicks=0, impressions=-1))

class TestGetMetric:
    async def test_get_metric(self, db_session, existing_metric):
        metric = await get_metric(db_session, existing_metric.id)
        assert metric is not None
        assert metric.campaign_id == existing_metric.campaign_id
        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions
        assert metric.clicks == existing_metric.clicks

    async def test_get_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        metric = await get_metric(db_session, fake_id)
        assert metric is None
        
class TestListMetrics:
    async def test_list_metrics(self, db_session, existing_metrics_across_campaigns):
        metric_list = await list_metrics(db_session)
        assert len(metric_list) == len(TEST_METRICS)
        for index in range(len(metric_list)):
            assert metric_list[index].clicks == TEST_METRICS[index].clicks
            assert metric_list[index].spend == TEST_METRICS[index].spend
            assert metric_list[index].impressions == TEST_METRICS[index].impressions
            
    async def test_list_metrics_with_offset(self, db_session, existing_metrics_across_campaigns):
        offset = 1
        filter_offset = PaginatedFilter(offset=offset)
        metric_list = await list_metrics(db_session, filter_offset)
        assert len(metric_list) == len(TEST_METRICS) - offset
        for index in range(len(metric_list)):
            assert metric_list[index].clicks == TEST_METRICS[index + offset].clicks
            assert metric_list[index].spend == TEST_METRICS[index + offset].spend
            assert metric_list[index].impressions == TEST_METRICS[index + offset].impressions

    async def test_list_metrics_with_limit(self, db_session, existing_metrics_across_campaigns):
        limit = 2
        filter_offset = PaginatedFilter(limit=limit)
        metric_list = await list_metrics(db_session, filter_offset)
        assert len(metric_list) == limit
        for index in range(limit):
            assert metric_list[index].clicks == TEST_METRICS[index].clicks
            assert metric_list[index].spend == TEST_METRICS[index].spend
            assert metric_list[index].impressions == TEST_METRICS[index].impressions

    async def test_list_metrics_with_campaign_id(self, db_session, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns['campaign_ids']
        position = 1
        campaign_id = campaign_ids[position]

        metric_list = await list_metrics(db_session, None, campaign_id)
        assert len(metric_list) == 1
        assert metric_list[0].clicks == TEST_METRICS[position].clicks
        assert metric_list[0].spend == TEST_METRICS[position].spend
        assert metric_list[0].impressions == TEST_METRICS[position].impressions

    async def test_list_metrics_no_entries(self, db_session):
        metric_list = await list_metrics(db_session)
        assert len(metric_list) == 0
        
class TestGetTotalNumberOfMetrics:
    async def test_get_total_number_of_metrics_with_entries(self, db_session, existing_metrics_across_campaigns):
        number_of_metrics = await get_total_number_of_metrics(db_session)
        assert number_of_metrics == len(existing_metrics_across_campaigns["metrics"])

    async def test_get_total_number_of_metrics_no_entries(self, db_session):
        number_of_metrics = await get_total_number_of_metrics(db_session)
        assert number_of_metrics == 0

    async def test_get_total_number_of_metrics_filtered_by_campaign(self, db_session, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns["campaign_ids"]
        number_of_metrics = await get_total_number_of_metrics(db_session, campaign_ids[0])
        assert number_of_metrics == 1

class TestMetricsSummary:
    async def test_summary(self, db_session, existing_metrics_across_campaigns):
        summary = await get_metrics_summary(db_session)
        assert summary
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS
        
    async def test_summary_no_entries(self, db_session):
        summary = await get_metrics_summary(db_session)
        assert summary
        assert summary.clicks == 0
        assert summary.spend == 0
        assert summary.impressions == 0
        
    async def test_summary_for_campaign(self, db_session, existing_metrics_single_campaign_crud, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        summary = await get_metrics_summary(db_session, campaign_id)
        assert summary
        assert summary.clicks == SUMMARY_TOTAL_CLICKS
        assert summary.spend == SUMMARY_TOTAL_SPEND
        assert summary.impressions == SUMMARY_TOTAL_IMPRESSIONS
    
    async def test_summary_for_campaign_no_entries(self, db_session, existing_campaign_crud):
        campaign_id = existing_campaign_crud.id
        summary = await get_metrics_summary(db_session, campaign_id)
        assert summary
        assert summary.clicks == 0
        assert summary.spend == 0
        assert summary.impressions == 0

    async def test_summary_for_campaign_only_shows_campaigns_results(self, db_session, existing_metrics_across_campaigns):
        metric = existing_metrics_across_campaigns['metrics'][0]
        campaign_id = metric.campaign_id
        summary = await get_metrics_summary(db_session, campaign_id)
        assert summary
        assert summary.clicks == metric.clicks
        assert summary.spend == metric.spend
        assert summary.impressions == metric.impressions

class TestUpdateCampaign:
    async def test_update_metric_with_all_fields(self, db_session, existing_metric):
        metric_id = existing_metric.id
        updated_metric = MetricUpdate(spend=UPDATE_METRIC_SPEND, clicks=UPDATE_METRIC_CLICKS, impressions=UPDATE_METRIC_IMPRESSIONS)
        metric = await update_metric(db_session, metric_id, updated_metric)
        assert metric
        assert metric.spend == UPDATE_METRIC_SPEND
        assert metric.clicks == UPDATE_METRIC_CLICKS
        assert metric.impressions == UPDATE_METRIC_IMPRESSIONS


    async def test_update_metric_with_spend(self, db_session, existing_metric):
        metric_id = existing_metric.id
        updated_metric = MetricUpdate(spend=UPDATE_METRIC_SPEND)
        metric = await update_metric(db_session, metric_id, updated_metric)
        assert metric
        assert metric.spend == UPDATE_METRIC_SPEND
        assert metric.clicks == existing_metric.clicks
        assert metric.impressions == existing_metric.impressions

    async def test_update_metric_with_clicks(self, db_session, existing_metric):
        metric_id = existing_metric.id
        updated_metric = MetricUpdate(clicks=UPDATE_METRIC_CLICKS)
        metric = await update_metric(db_session, metric_id, updated_metric)
        assert metric
        assert metric.clicks == UPDATE_METRIC_CLICKS
        assert metric.spend == existing_metric.spend
        assert metric.impressions == existing_metric.impressions

    async def test_update_metric_with_impressions(self, db_session, existing_metric):
        metric_id = existing_metric.id
        updated_metric = MetricUpdate(impressions=UPDATE_METRIC_IMPRESSIONS)
        metric = await update_metric(db_session, metric_id, updated_metric)
        assert metric
        assert metric.impressions == UPDATE_METRIC_IMPRESSIONS
        assert metric.spend == existing_metric.spend
        assert metric.clicks == existing_metric.clicks

    async def test_update_metric_no_op(self, db_session, existing_metric):
        metric_id = existing_metric.id
        updated_metric = MetricUpdate()
        metric = await update_metric(db_session, metric_id, updated_metric)
        assert metric
        assert metric.spend == existing_metric.spend
        assert metric.clicks == existing_metric.clicks
        assert metric.impressions == existing_metric.impressions

    async def test_update_metric_not_found(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        updated_metric = MetricUpdate(spend=UPDATE_METRIC_SPEND, clicks=UPDATE_METRIC_CLICKS, impressions=UPDATE_METRIC_IMPRESSIONS)
        metric = await update_metric(db_session, fake_id, updated_metric)
        assert not metric

class TestDeleteMetric:
    async def test_delete_metric(self, db_session, existing_metric):
        metric_id = existing_metric.id
        deleted = await delete_metric(db_session, metric_id)
        assert deleted

    async def test_delete_metric_doesnt_exist(self, db_session, existing_metric):
        fake_id = existing_metric.id + 1
        deleted = await delete_metric(db_session, fake_id)
        assert not deleted
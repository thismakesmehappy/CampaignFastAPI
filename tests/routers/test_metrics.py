from app.constants import PAGE_LIMIT_DEFAULT
from tests.conftest import (
    TEST_METRIC,
    TEST_METRIC_LIST,
    TEST_METRICS_MULTI,
    UPDATE_METRIC_SPEND,
    UPDATE_METRIC_CLICKS,
    UPDATE_METRIC_IMPRESSIONS,
    LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS,
    SUMMARY_TOTAL_CLICKS,
    SUMMARY_TOTAL_SPEND,
    SUMMARY_TOTAL_IMPRESSIONS,
)


class TestCreateMetric:
    async def test_create_metric(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": TEST_METRIC.spend, "clicks": TEST_METRIC.clicks, "impressions": TEST_METRIC.impressions},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["spend"] == TEST_METRIC.spend
        assert data["clicks"] == TEST_METRIC.clicks
        assert data["impressions"] == TEST_METRIC.impressions
        assert data["campaign_id"] == existing_campaign.id
        assert "id" in data

    async def test_create_metric_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.post(
            f"/campaigns/{fake_id}/metrics/",
            json={"spend": 100.0, "clicks": 50, "impressions": 1000},
        )
        assert response.status_code == 404

    async def test_create_metric_negative_spend(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": -1.0, "clicks": 50, "impressions": 1000},
        )
        assert response.status_code == 422

    async def test_create_metric_negative_clicks(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": 100.0, "clicks": -1, "impressions": 1000},
        )
        assert response.status_code == 422

    async def test_create_metric_negative_impressions(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": 100.0, "clicks": 50, "impressions": -1},
        )
        assert response.status_code == 422

    async def test_create_metric_spend_missing(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"clicks": 50, "impressions": 1000},
        )
        assert response.status_code == 422

    async def test_create_metric_clicks_missing(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": 100.0, "impressions": 1000},
        )
        assert response.status_code == 422

    async def test_create_metric_impressions_missing(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": 100.0, "clicks": 50},
        )
        assert response.status_code == 422

    async def test_create_metric_zero_values_allowed(self, client, existing_campaign):
        response = await client.post(
            f"/campaigns/{existing_campaign.id}/metrics/",
            json={"spend": 0.0, "clicks": 0, "impressions": 0},
        )
        assert response.status_code == 201


class TestListMetricsForCampaign:
    async def test_list_metrics_for_campaign(self, client, existing_metric_list, existing_campaign):
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS
        assert all(item["campaign_id"] == existing_campaign.id for item in items)

    async def test_list_metrics_for_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.get(f"/campaigns/{fake_id}/metrics/")
        assert response.status_code == 404

    async def test_list_metrics_for_campaign_no_entries(self, client, existing_campaign):
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    async def test_list_metrics_for_campaign_limit(self, client, existing_metric_list, existing_campaign):
        limit = 4
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == limit
        assert len(data["items"]) == limit

    async def test_list_metrics_for_campaign_offset(self, client, existing_metric_list, existing_campaign):
        offset = 1
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert len(data["items"]) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS

    async def test_list_metrics_for_campaign_only_returns_own_metrics(self, client, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns["campaign_ids"]
        target_id = campaign_ids[0]
        response = await client.get(f"/campaigns/{target_id}/metrics/")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert all(item["campaign_id"] == target_id for item in items)


class TestGetMetric:
    async def test_get_metric(self, client, existing_metric):
        response = await client.get(f"/metrics/{existing_metric.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["spend"] == TEST_METRIC.spend
        assert data["clicks"] == TEST_METRIC.clicks
        assert data["impressions"] == TEST_METRIC.impressions
        assert data["campaign_id"] == existing_metric.campaign_id

    async def test_get_metric_not_found(self, client, existing_metric):
        fake_id = existing_metric.id + 1
        response = await client.get(f"/metrics/{fake_id}/")
        assert response.status_code == 404


class TestListMetrics:
    async def test_list_metrics(self, client, existing_metric_list):
        response = await client.get("/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        items = data["items"]
        assert len(items) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS

    async def test_list_metrics_limit_less_than_total(self, client, existing_metric_list):
        limit = 4
        response = await client.get(f"/metrics/?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == limit
        assert len(data["items"]) == limit

    async def test_list_metrics_limit_greater_than_total(self, client, existing_metric_list):
        limit = len(TEST_METRIC_LIST) * 2
        response = await client.get(f"/metrics/?limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0
        assert data["limit"] == limit
        assert len(data["items"]) == len(TEST_METRIC_LIST)

    async def test_list_metrics_offset(self, client, existing_metric_list):
        offset = 1
        response = await client.get(f"/metrics/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        assert len(data["items"]) == LENGTH_OF_METRIC_RESULTS_DEFAULT_FILTERS

    async def test_list_metrics_offset_fewer_results(self, client, existing_metric_list):
        expected_results_size = 2
        offset = len(TEST_METRIC_LIST) - expected_results_size
        response = await client.get(f"/metrics/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        assert len(data["items"]) == expected_results_size

    async def test_list_metrics_offset_past_total(self, client, existing_metric_list):
        offset = len(TEST_METRIC_LIST)
        response = await client.get(f"/metrics/?offset={offset}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == PAGE_LIMIT_DEFAULT
        assert len(data["items"]) == 0

    async def test_list_metrics_offset_and_limit(self, client, existing_metric_list):
        offset = 1
        limit = 2
        response = await client.get(f"/metrics/?offset={offset}&limit={limit}")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == offset
        assert data["limit"] == limit
        assert len(data["items"]) == limit

    async def test_list_metrics_no_entries(self, client):
        response = await client.get("/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0


class TestUpdateMetric:
    async def test_update_metric_all_fields(self, client, existing_metric):
        response = await client.patch(
            f"/metrics/{existing_metric.id}/",
            json={"spend": UPDATE_METRIC_SPEND, "clicks": UPDATE_METRIC_CLICKS, "impressions": UPDATE_METRIC_IMPRESSIONS},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend"] == UPDATE_METRIC_SPEND
        assert data["clicks"] == UPDATE_METRIC_CLICKS
        assert data["impressions"] == UPDATE_METRIC_IMPRESSIONS

    async def test_update_metric_spend(self, client, existing_metric):
        response = await client.patch(
            f"/metrics/{existing_metric.id}/",
            json={"spend": UPDATE_METRIC_SPEND},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend"] == UPDATE_METRIC_SPEND
        assert data["clicks"] == existing_metric.clicks
        assert data["impressions"] == existing_metric.impressions

    async def test_update_metric_clicks(self, client, existing_metric):
        response = await client.patch(
            f"/metrics/{existing_metric.id}/",
            json={"clicks": UPDATE_METRIC_CLICKS},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend"] == existing_metric.spend
        assert data["clicks"] == UPDATE_METRIC_CLICKS
        assert data["impressions"] == existing_metric.impressions

    async def test_update_metric_impressions(self, client, existing_metric):
        response = await client.patch(
            f"/metrics/{existing_metric.id}/",
            json={"impressions": UPDATE_METRIC_IMPRESSIONS},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend"] == existing_metric.spend
        assert data["clicks"] == existing_metric.clicks
        assert data["impressions"] == UPDATE_METRIC_IMPRESSIONS

    async def test_update_metric_not_found(self, client, existing_metric):
        fake_id = existing_metric.id + 1
        response = await client.patch(f"/metrics/{fake_id}/", json={"spend": UPDATE_METRIC_SPEND})
        assert response.status_code == 404

    async def test_update_metric_negative_spend(self, client, existing_metric):
        response = await client.patch(f"/metrics/{existing_metric.id}/", json={"spend": -1.0})
        assert response.status_code == 422

    async def test_update_metric_negative_clicks(self, client, existing_metric):
        response = await client.patch(f"/metrics/{existing_metric.id}/", json={"clicks": -1})
        assert response.status_code == 422

    async def test_update_metric_negative_impressions(self, client, existing_metric):
        response = await client.patch(f"/metrics/{existing_metric.id}/", json={"impressions": -1})
        assert response.status_code == 422


class TestDeleteMetric:
    async def test_delete_metric(self, client, existing_metric):
        response = await client.delete(f"/metrics/{existing_metric.id}/")
        assert response.status_code == 204

    async def test_delete_metric_not_found(self, client, existing_metric):
        fake_id = existing_metric.id + 1
        response = await client.delete(f"/metrics/{fake_id}/")
        assert response.status_code == 404

    async def test_delete_metric_removes_it(self, client, existing_metric):
        await client.delete(f"/metrics/{existing_metric.id}/")
        response = await client.get(f"/metrics/{existing_metric.id}/")
        assert response.status_code == 404


class TestGetMetricsSummaryForCampaign:
    async def test_summary_for_campaign(self, client, existing_metrics_single_campaign, existing_campaign):
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] == SUMMARY_TOTAL_CLICKS
        assert data["spend"] == SUMMARY_TOTAL_SPEND
        assert data["impressions"] == SUMMARY_TOTAL_IMPRESSIONS
        assert data["total_metrics"] == len(TEST_METRICS_MULTI)
        assert data["campaign_id"] == existing_campaign.id

    async def test_summary_for_campaign_no_entries(self, client, existing_campaign):
        response = await client.get(f"/campaigns/{existing_campaign.id}/metrics/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] == 0
        assert data["spend"] == 0
        assert data["impressions"] == 0
        assert data["total_metrics"] == 0
        assert data["campaign_id"] == existing_campaign.id

    async def test_summary_for_campaign_not_found(self, client, existing_campaign):
        fake_id = existing_campaign.id + 1
        response = await client.get(f"/campaigns/{fake_id}/metrics/summary/")
        assert response.status_code == 404

    async def test_summary_for_campaign_only_shows_own_metrics(self, client, existing_metrics_across_campaigns):
        campaign_ids = existing_metrics_across_campaigns["campaign_ids"]
        metrics = existing_metrics_across_campaigns["metrics"]
        target_id = campaign_ids[0]
        response = await client.get(f"/campaigns/{target_id}/metrics/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] == metrics[0].clicks
        assert data["spend"] == metrics[0].spend
        assert data["impressions"] == metrics[0].impressions
        assert data["total_metrics"] == 1
        assert data["campaign_id"] == target_id


class TestGetMetricsSummary:
    async def test_summary(self, client, existing_metrics_across_campaigns):
        response = await client.get("/metrics/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] == SUMMARY_TOTAL_CLICKS
        assert data["spend"] == SUMMARY_TOTAL_SPEND
        assert data["impressions"] == SUMMARY_TOTAL_IMPRESSIONS
        assert data["total_metrics"] == len(TEST_METRICS_MULTI)
        assert data["campaign_id"] is None

    async def test_summary_no_entries(self, client):
        response = await client.get("/metrics/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["clicks"] == 0
        assert data["spend"] == 0
        assert data["impressions"] == 0
        assert data["total_metrics"] == 0
        assert data["campaign_id"] is None

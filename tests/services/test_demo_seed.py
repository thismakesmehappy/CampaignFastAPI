from datetime import datetime, timedelta, timezone

import pytest

from app.exceptions import NotFoundError
from app.models.metric import MetricSource
from app.repositories import metric as metric_repo
from app.schema import PaginatedFilter
from app.schema.demo_seed import SeedDemoDataRequest
from app.services import demo_seed as demo_seed_service

_ALL_ROWS = PaginatedFilter(limit=500)


class TestSeedDemoData:
    async def test_seeds_campaigns_and_metrics_for_empty_client(self, db_session, existing_client):
        result = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        assert result.seeded is True
        assert result.campaigns_created == 3
        assert result.metrics_created > 0
        assert result.ranges_filled == [7, 30, 60, 90, 180]

    async def test_seeded_metrics_are_system_sourced(self, db_session, existing_client):
        await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        metrics = await metric_repo.find_all(db_session, data=_ALL_ROWS, client_id=existing_client.id)
        assert len(metrics) > 0
        assert all(m.source == MetricSource.system for m in metrics)

    async def test_every_range_gets_at_least_one_datapoint(self, db_session, existing_client):
        """Each of the 5 UI filter ranges (7/30/60/90/180) should have real data after seeding an empty client."""
        now = datetime.now(timezone.utc)
        await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        metrics = await metric_repo.find_all(db_session, data=_ALL_ROWS, client_id=existing_client.id)

        bands = [(0, 7), (7, 30), (30, 60), (60, 90), (90, 180)]
        for band_start, band_end in bands:
            floor = now - timedelta(days=band_end)
            ceiling = now - timedelta(days=band_start)
            in_band = [m for m in metrics if floor <= m.period_start <= ceiling]
            assert len(in_band) > 0, f"band ({band_start}, {band_end}] has no datapoints"

    async def test_seeded_metrics_within_lookback_window(self, db_session, existing_client):
        lookback_days = 90
        await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest(lookback_days=lookback_days))
        metrics = await metric_repo.find_all(db_session, data=_ALL_ROWS, client_id=existing_client.id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days + 1)
        assert all(m.period_start >= cutoff for m in metrics)

    async def test_seeded_metrics_respect_value_ranges(self, db_session, existing_client):
        data = SeedDemoDataRequest(min_spend=20.0, max_spend=100.0, min_impressions=1000, max_impressions=2000, max_ctr=0.1)
        await demo_seed_service.seed_demo_data(db_session, existing_client.id, data)
        metrics = await metric_repo.find_all(db_session, data=_ALL_ROWS, client_id=existing_client.id)
        assert len(metrics) > 0
        for m in metrics:
            assert 20.0 <= m.spend <= 100.0
            assert 1000 <= m.impressions <= 2000
            assert m.clicks <= m.impressions * 0.1

    async def test_second_call_is_noop_when_all_ranges_covered(self, db_session, existing_client):
        first = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        assert first.seeded is True

        second = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        assert second.seeded is False
        assert second.campaigns_created == 0
        assert second.metrics_created == 0
        assert second.ranges_filled == []

    async def test_seeds_when_only_stale_data_exists(self, db_session, existing_client, make_campaign, make_metric):
        """A client with only old (>7 day) metrics should still get the sparse 7-day range filled."""
        campaign = await make_campaign(client_id=existing_client.id)
        old_period = datetime.now(timezone.utc) - timedelta(days=30)
        await make_metric(campaign.id, spend=10.0, clicks=1, impressions=100, period_start=old_period, period_end=old_period)

        result = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        assert result.seeded is True
        assert 7 in result.ranges_filled

    async def test_only_fills_sparse_ranges_not_covered_ones(self, db_session, existing_client, make_campaign, make_metric):
        """A client with only recent (last-week) data should have the 7-day range skipped but older ranges filled."""
        campaign = await make_campaign(client_id=existing_client.id)
        recent_period = datetime.now(timezone.utc) - timedelta(days=2)
        await make_metric(campaign.id, spend=10.0, clicks=1, impressions=100, period_start=recent_period, period_end=recent_period)

        result = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest())
        assert result.seeded is True
        assert 7 not in result.ranges_filled
        assert set(result.ranges_filled) == {30, 60, 90, 180}

    async def test_client_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            await demo_seed_service.seed_demo_data(db_session, 999999999999, SeedDemoDataRequest())

    async def test_custom_campaign_count(self, db_session, existing_client):
        data = SeedDemoDataRequest(campaign_count=1)
        result = await demo_seed_service.seed_demo_data(db_session, existing_client.id, data)
        assert result.campaigns_created == 1

    async def test_lookback_days_shorter_than_180_drops_outer_bands(self, db_session, existing_client):
        result = await demo_seed_service.seed_demo_data(db_session, existing_client.id, SeedDemoDataRequest(lookback_days=45))
        assert result.ranges_filled == [7, 30, 45]
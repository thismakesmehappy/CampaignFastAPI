import pytest
from pydantic import ValidationError

from app.models.metric import MetricSource
from app.schema.metric import MetricSummaryFilter


class TestSourceList:
    def test_unset_returns_all_sources(self):
        assert MetricSummaryFilter().source_list == list(MetricSource)

    def test_single_source(self):
        assert MetricSummaryFilter(source="user").source_list == [MetricSource.user]

    def test_comma_separated_sources(self):
        result = MetricSummaryFilter(source="user,system").source_list
        assert result == [MetricSource.user, MetricSource.system]

    def test_comma_separated_sources_with_spaces(self):
        result = MetricSummaryFilter(source=" user , system ").source_list
        assert result == [MetricSource.user, MetricSource.system]

    def test_all_keyword_expands_to_every_source(self):
        assert MetricSummaryFilter(source="all").source_list == list(MetricSource)

    def test_all_keyword_mixed_with_other_values_still_expands(self):
        assert MetricSummaryFilter(source="all,system").source_list == list(MetricSource)

    def test_invalid_source_raises_at_construction(self):
        with pytest.raises(ValidationError):
            MetricSummaryFilter(source="bogus")

    def test_partially_invalid_source_raises_at_construction(self):
        with pytest.raises(ValidationError):
            MetricSummaryFilter(source="user,bogus")

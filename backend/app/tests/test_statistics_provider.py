from app.modules.statistics.enums import StatisticScope
from app.modules.statistics.providers.statistics_feed_v1 import StatisticsFeedV1Adapter

def test_statistics_adapter_normalizes_extensible_values() -> None:
    result = StatisticsFeedV1Adapter().normalize({"fixture":{"provider":"fixture_feed_v1","id":"fixture-1"},"observed_at":"2026-08-01T12:00:00+00:00","statistics":[{"scope":"team","category":{"code":"possession","name":"Possession"},"team":{"id":"team-1","name":"Home FC"},"values":{"percentage":61.2,"provider_only_metric":"accepted"}}]})
    assert result.statistics[0].scope is StatisticScope.TEAM
    assert result.statistics[0].values["provider_only_metric"] == "accepted"

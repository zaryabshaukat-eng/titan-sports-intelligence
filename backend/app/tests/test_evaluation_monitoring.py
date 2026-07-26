from app.modules.evaluation_monitoring.analyzers.distribution import js, kl, normalize, psi, wasserstein
from app.modules.evaluation_monitoring.registry import MonitoringAnalyzerRegistry


def test_drift_analyzers_are_deterministic_and_registered() -> None:
    baseline, current = normalize([3, 1]), normalize([1, 3])
    assert psi(baseline, current) > 0
    assert kl(baseline, current) > 0
    assert js(baseline, current) > 0
    assert wasserstein(baseline, current) > 0
    assert len(MonitoringAnalyzerRegistry().analyzers()) == 4

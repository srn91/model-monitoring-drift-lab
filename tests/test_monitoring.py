from app.monitoring import build_monitoring_summary, compute_feature_drift
from app.simulation import simulate_datasets


def test_simulation_creates_shifted_current_window() -> None:
    reference_rows, current_rows = simulate_datasets()

    assert len(reference_rows) == 2000
    assert len(current_rows) == 2000

    reference_utilization = sum(float(row["credit_utilization"]) for row in reference_rows) / len(reference_rows)
    current_utilization = sum(float(row["credit_utilization"]) for row in current_rows) / len(current_rows)
    reference_defaults = sum(int(row["actual_default"]) for row in reference_rows) / len(reference_rows)
    current_defaults = sum(int(row["actual_default"]) for row in current_rows) / len(current_rows)

    assert current_utilization > reference_utilization
    assert current_defaults > reference_defaults


def test_feature_drift_flags_shifted_features() -> None:
    reference_rows, current_rows = simulate_datasets()
    metrics = compute_feature_drift(reference_rows, current_rows)
    metric_by_name = {metric.name: metric for metric in metrics}

    assert metric_by_name["credit_utilization"].status == "critical"
    assert metric_by_name["payment_ratio"].status in {"warning", "critical"}


def test_monitoring_summary_emits_incident_alerts() -> None:
    reference_rows, current_rows = simulate_datasets()
    summary = build_monitoring_summary(reference_rows, current_rows)

    assert summary.overall_status == "critical"
    assert summary.prediction_drift.status in {"warning", "critical"}
    assert summary.performance.status in {"warning", "critical"}
    assert summary.alerts
    assert "log loss changed" in summary.summary

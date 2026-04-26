from fastapi.testclient import TestClient

from app.monitoring import build_monitoring_summary, compute_feature_drift
from app.reporting import write_outputs
from app.web import app
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


def test_report_outputs_html_dashboard(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.reporting.SUMMARY_PATH", tmp_path / "monitoring_summary.json")
    monkeypatch.setattr("app.reporting.REPORT_PATH", tmp_path / "incident_report.md")
    monkeypatch.setattr("app.reporting.DASHBOARD_PATH", tmp_path / "monitoring_dashboard.html")

    reference_rows, current_rows = simulate_datasets()
    summary = build_monitoring_summary(reference_rows, current_rows)
    summary_path, report_path, dashboard_path = write_outputs(summary)

    dashboard_html = (tmp_path / "monitoring_dashboard.html").read_text(encoding="utf-8")
    assert summary_path.endswith("monitoring_summary.json")
    assert report_path.endswith("incident_report.md")
    assert dashboard_path.endswith("monitoring_dashboard.html")
    assert "<title>Monitoring Dashboard" in dashboard_html
    assert "prediction_latency_ms" in dashboard_html
    assert "Recommended Actions" in dashboard_html


def test_read_only_api_exposes_summary_and_report() -> None:
    client = TestClient(app)

    health_response = client.get("/health")
    summary_response = client.get("/summary")
    report_response = client.get("/report")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}

    assert summary_response.status_code == 200
    payload = summary_response.json()
    assert payload["overall_status"] == "critical"
    assert payload["prediction_drift"]["status"] in {"warning", "critical"}
    assert payload["alerts"]

    assert report_response.status_code == 200
    assert "Monitoring Incident Report" in report_response.text
    assert "Overall status" in report_response.text

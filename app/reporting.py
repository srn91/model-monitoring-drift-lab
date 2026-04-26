import json
from pathlib import Path

from app.config import REPORT_PATH, SUMMARY_PATH
from app.models import MonitoringSummary


def _status_badge(status: str) -> str:
    return status.upper()


def render_markdown(summary: MonitoringSummary) -> str:
    feature_lines = [
        "| Feature | Reference Mean | Current Mean | Delta | PSI | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for metric in summary.feature_drift:
        feature_lines.append(
            f"| {metric.name} | {metric.reference_mean:.4f} | {metric.current_mean:.4f} | "
            f"{metric.mean_delta:.4f} | {metric.population_stability_index:.4f} | {metric.status} |"
        )

    prediction = summary.prediction_drift
    performance = summary.performance
    alert_lines = ["None"] if not summary.alerts else [f"- `{alert.status}` {alert.area}: {alert.message}" for alert in summary.alerts]
    action_lines = [f"{index}. {action}" for index, action in enumerate(summary.recommended_actions, start=1)]

    return "\n".join(
        [
            f"# Monitoring Incident Report: {summary.incident_id}",
            "",
            f"Overall status: `{_status_badge(summary.overall_status)}`",
            "",
            "## Executive Summary",
            "",
            summary.summary,
            "",
            "## Feature Drift",
            "",
            *feature_lines,
            "",
            "## Prediction Shift",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| reference mean score | {prediction.reference_mean_score:.4f} |",
            f"| current mean score | {prediction.current_mean_score:.4f} |",
            f"| mean score delta | {prediction.mean_score_delta:.4f} |",
            f"| KS statistic | {prediction.ks_statistic:.4f} |",
            f"| reference high-risk rate | {prediction.reference_high_risk_rate:.4f} |",
            f"| current high-risk rate | {prediction.current_high_risk_rate:.4f} |",
            f"| status | {prediction.status} |",
            "",
            "## Delayed Outcome Quality",
            "",
            "| Metric | Reference | Current | Delta |",
            "| --- | ---: | ---: | ---: |",
            f"| accuracy | {performance.reference.accuracy:.4f} | {performance.current.accuracy:.4f} | {performance.accuracy_delta:.4f} |",
            f"| positive rate | {performance.reference.positive_rate:.4f} | {performance.current.positive_rate:.4f} | {performance.positive_rate_delta:.4f} |",
            f"| brier score | {performance.reference.brier_score:.4f} | {performance.current.brier_score:.4f} | {performance.brier_score_delta:.4f} |",
            f"| log loss | {performance.reference.log_loss:.4f} | {performance.current.log_loss:.4f} | {performance.log_loss_delta:.4f} |",
            "",
            "## Alerts",
            "",
            *alert_lines,
            "",
            "## Recommended Actions",
            "",
            *action_lines,
            "",
        ]
    )


def write_outputs(summary: MonitoringSummary) -> tuple[str, str]:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    cwd = Path.cwd()

    def _portable(path: Path) -> str:
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            return str(path)

    return _portable(SUMMARY_PATH), _portable(REPORT_PATH)

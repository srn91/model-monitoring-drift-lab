import html
import json
from pathlib import Path

from app.config import DASHBOARD_PATH, REPORT_PATH, SUMMARY_PATH
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


def render_dashboard_html(summary: MonitoringSummary) -> str:
    feature_rows = "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(metric.name)}</td>"
            f"<td>{metric.reference_mean:.4f}</td>"
            f"<td>{metric.current_mean:.4f}</td>"
            f"<td>{metric.mean_delta:.4f}</td>"
            f"<td>{metric.population_stability_index:.4f}</td>"
            f"<td><span class='pill pill-{html.escape(metric.status)}'>{html.escape(metric.status)}</span></td>"
            "</tr>"
        )
        for metric in summary.feature_drift
    )
    alert_rows = (
        "<li>No alerts</li>"
        if not summary.alerts
        else "\n".join(
            f"<li><span class='pill pill-{html.escape(alert.status)}'>{html.escape(alert.status)}</span> "
            f"{html.escape(alert.area)}: {html.escape(alert.message)}</li>"
            for alert in summary.alerts
        )
    )
    action_rows = "".join(f"<li>{html.escape(action)}</li>" for action in summary.recommended_actions)
    prediction = summary.prediction_drift
    performance = summary.performance
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Monitoring Dashboard - {html.escape(summary.incident_id)}</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #0f172a;
        --panel: #111827;
        --panel-2: #1f2937;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --border: #374151;
        --critical: #ef4444;
        --warning: #f59e0b;
        --healthy: #22c55e;
      }}
      body {{
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #0b1120, var(--bg));
        color: var(--text);
      }}
      .wrap {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 48px; }}
      header {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 24px; }}
      h1, h2 {{ margin: 0; }}
      h1 {{ font-size: 2rem; }}
      .muted {{ color: var(--muted); }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin: 20px 0 24px; }}
      .card {{ background: rgba(17, 24, 39, 0.9); border: 1px solid var(--border); border-radius: 16px; padding: 18px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--border); text-align: left; }}
      th {{ color: var(--muted); font-weight: 600; }}
      .pill {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }}
      .pill-critical {{ background: rgba(239, 68, 68, 0.16); color: #fecaca; }}
      .pill-warning {{ background: rgba(245, 158, 11, 0.16); color: #fde68a; }}
      .pill-healthy {{ background: rgba(34, 197, 94, 0.16); color: #bbf7d0; }}
      ul {{ margin: 0; padding-left: 20px; }}
      code {{ background: rgba(31, 41, 55, 0.85); padding: 2px 6px; border-radius: 6px; }}
      .summary {{ font-size: 1.05rem; line-height: 1.6; }}
    </style>
  </head>
  <body>
    <main class="wrap">
      <header>
        <div>
          <h1>Monitoring Dashboard</h1>
          <p class="muted">{html.escape(summary.incident_id)}</p>
        </div>
        <div class="pill pill-{html.escape(summary.overall_status)}">{html.escape(summary.overall_status)}</div>
      </header>

      <section class="card summary">
        <p>{html.escape(summary.summary)}</p>
      </section>

      <section class="grid">
        <div class="card"><h2>Window Size</h2><p>{summary.reference_rows:,} reference rows / {summary.current_rows:,} current rows</p></div>
        <div class="card"><h2>Prediction Shift</h2><p>KS {prediction.ks_statistic:.4f} with mean delta {prediction.mean_score_delta:.4f}</p></div>
        <div class="card"><h2>Performance</h2><p>Log loss delta {performance.log_loss_delta:.4f} and accuracy delta {performance.accuracy_delta:.4f}</p></div>
      </section>

      <section class="card">
        <h2>Feature Drift</h2>
        <table>
          <thead>
            <tr><th>Feature</th><th>Reference</th><th>Current</th><th>Delta</th><th>PSI</th><th>Status</th></tr>
          </thead>
          <tbody>
            {feature_rows}
          </tbody>
        </table>
      </section>

      <section class="grid">
        <div class="card">
          <h2>Alerts</h2>
          <ul>{alert_rows}</ul>
        </div>
        <div class="card">
          <h2>Recommended Actions</h2>
          <ul>{action_rows}</ul>
        </div>
      </section>
    </main>
  </body>
</html>
"""


def write_outputs(summary: MonitoringSummary) -> tuple[str, str, str]:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_markdown(summary), encoding="utf-8")
    DASHBOARD_PATH.write_text(render_dashboard_html(summary), encoding="utf-8")
    cwd = Path.cwd()

    def _portable(path: Path) -> str:
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            return str(path)

    return _portable(SUMMARY_PATH), _portable(REPORT_PATH), _portable(DASHBOARD_PATH)

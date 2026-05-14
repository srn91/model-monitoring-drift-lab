from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.config import REFERENCE_PATH, ROLLING_PATH
from app.monitoring import build_monitoring_summary
from app.reporting import render_markdown
from app.simulation import read_rows, simulate_datasets

app = FastAPI(
    title="model-monitoring-drift-lab",
    version="1.0.0",
    description="Read-only monitoring surface for the drift lab summary and incident report.",
)


def _load_current_rows() -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]]]:
    if REFERENCE_PATH.exists() and ROLLING_PATH.exists():
        return read_rows(REFERENCE_PATH), read_rows(ROLLING_PATH)
    return simulate_datasets()


def build_current_summary():
    reference_rows, current_rows = _load_current_rows()
    return build_monitoring_summary(reference_rows, current_rows)


def build_current_report() -> str:
    return render_markdown(build_current_summary())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    summary = build_current_summary()
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Model Monitoring Drift Lab</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:860px;margin:48px auto;padding:0 24px;line-height:1.5;color:#111}}a{{color:#0645ad}}</style></head>
<body>
<h1>Model Monitoring Drift Lab</h1>
<p>Monitoring service for feature drift, prediction shift, delayed-outcome quality, and incident-style reporting.</p>
<ul><li>Current status: {summary.overall_status}</li><li>Reference rows: {summary.reference_rows}</li><li>Current rows: {summary.current_rows}</li></ul>
<h2>Open endpoints</h2>
<ul>
<li><a href="/summary">Monitoring summary</a></li>
<li><a href="/report">Incident report</a></li>
<li><a href="/health">Health check</a></li>
<li><a href="/docs">API docs</a></li>
</ul>
</body></html>"""


@app.get("/summary")
def summary() -> dict:
    return build_current_summary().to_dict()


@app.get("/report", response_class=PlainTextResponse)
def report() -> str:
    return build_current_report()

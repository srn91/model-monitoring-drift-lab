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
<style>
body{{margin:0;background:#f8fafc;color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;line-height:1.5}}
main{{max-width:1080px;margin:0 auto;padding:56px 24px}}.hero{{background:linear-gradient(135deg,#111827,#b91c1c);color:white;border-radius:22px;padding:38px;box-shadow:0 24px 60px rgba(15,23,42,.18)}}
.eyebrow{{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#fecaca;font-weight:700}}h1{{font-size:42px;line-height:1.05;margin:10px 0 14px}}.hero p{{font-size:17px;color:#fee2e2;max-width:780px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.card{{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:18px;box-shadow:0 10px 30px rgba(15,23,42,.06)}}
.metric{{font-size:25px;font-weight:800;color:#0f172a}}.label{{font-size:13px;color:#64748b;margin-top:3px}}.links{{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}}
a.button{{background:#0f172a;color:white;text-decoration:none;padding:11px 14px;border-radius:10px;font-weight:700}}a.secondary{{background:white;color:#0f172a;border:1px solid #cbd5e1}}
@media(max-width:800px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}h1{{font-size:34px}}}}
</style></head>
<body><main>
<section class="hero"><div class="eyebrow">Model reliability</div><h1>Model Monitoring Drift Lab</h1>
<p>Monitoring surface for feature drift, prediction shift, delayed-outcome quality, and operational reporting.</p>
<div class="links"><a class="button" href="/summary">Monitoring summary</a><a class="button secondary" href="/report">Incident report</a><a class="button secondary" href="/docs">API docs</a></div></section>
<section class="grid">
<div class="card"><div class="metric">{summary.overall_status}</div><div class="label">current status</div></div>
<div class="card"><div class="metric">{summary.reference_rows}</div><div class="label">reference rows</div></div>
<div class="card"><div class="metric">{summary.current_rows}</div><div class="label">current rows</div></div>
<div class="card"><div class="metric">5</div><div class="label">rolling windows</div></div>
</section>
<section class="card"><p>Open the summary for drift metrics, then read the incident report to see how model quality changes are translated into action.</p></section>
</main></body></html>"""


@app.get("/summary")
def summary() -> dict:
    return build_current_summary().to_dict()


@app.get("/report", response_class=PlainTextResponse)
def report() -> str:
    return build_current_report()

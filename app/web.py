from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

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


@app.get("/summary")
def summary() -> dict:
    return build_current_summary().to_dict()


@app.get("/report", response_class=PlainTextResponse)
def report() -> str:
    return build_current_report()

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

from app.config import (
    GENERATED_DIR,
    REFERENCE_PATH,
    REFERENCE_ROWS,
    ROLLING_DAYS,
    ROLLING_PATH,
    ROLLING_ROWS_PER_DAY,
    SIMULATION_SEED,
)

FIELDNAMES = [
    "row_id",
    "window",
    "monitoring_date",
    "credit_utilization",
    "payment_ratio",
    "support_tickets_30d",
    "prediction_latency_ms",
    "predicted_default_risk",
    "actual_default",
]
REFERENCE_DATE = date(2026, 4, 20)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def logistic(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _simulate_reference_window(
    size: int, rng: random.Random
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for index in range(size):
        credit_utilization = clamp(rng.gauss(0.47, 0.12), 0.03, 0.99)
        payment_ratio = clamp(rng.gauss(0.92, 0.08), 0.35, 1.20)
        support_tickets = max(0, int(round(rng.gauss(1.8, 1.05))))
        prediction_latency = max(40.0, rng.gauss(115.0, 16.0))
        raw_risk = (
            -2.55
            + 3.4 * credit_utilization
            - 2.6 * payment_ratio
            + 0.17 * support_tickets
            + 0.0042 * prediction_latency
            + rng.gauss(0.0, 0.28)
        )
        predicted_default_risk = logistic(raw_risk)
        actual_default_risk = logistic(raw_risk + rng.gauss(0.0, 0.18))
        actual_default = int(rng.random() < actual_default_risk)
        rows.append(
            {
                "row_id": f"reference-{index + 1}",
                "window": "reference",
                "monitoring_date": REFERENCE_DATE.isoformat(),
                "credit_utilization": round(credit_utilization, 6),
                "payment_ratio": round(payment_ratio, 6),
                "support_tickets_30d": support_tickets,
                "prediction_latency_ms": round(prediction_latency, 6),
                "predicted_default_risk": round(predicted_default_risk, 6),
                "actual_default": actual_default,
            }
        )
    return rows


def _simulate_current_day(
    day_index: int, size: int, rng: random.Random
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    monitoring_date = REFERENCE_DATE + timedelta(days=day_index + 1)
    intensity = (day_index + 1) / ROLLING_DAYS

    utilization_mean = 0.47 + 0.15 * intensity
    payment_mean = 0.92 - 0.11 * intensity
    ticket_mean = 1.8 + 1.4 * intensity
    latency_mean = 115.0 + 24.0 * intensity
    prediction_offset = -0.18 * intensity
    outcome_offset = 0.34 * intensity

    for index in range(size):
        credit_utilization = clamp(rng.gauss(utilization_mean, 0.12), 0.03, 0.99)
        payment_ratio = clamp(rng.gauss(payment_mean, 0.08), 0.35, 1.20)
        support_tickets = max(0, int(round(rng.gauss(ticket_mean, 1.05))))
        prediction_latency = max(40.0, rng.gauss(latency_mean, 16.0))

        raw_risk = (
            -2.55
            + 3.4 * credit_utilization
            - 2.6 * payment_ratio
            + 0.17 * support_tickets
            + 0.0042 * prediction_latency
            + rng.gauss(0.0, 0.28)
        )
        predicted_default_risk = logistic(raw_risk + prediction_offset)
        actual_default_risk = logistic(raw_risk + outcome_offset + rng.gauss(0.0, 0.18))
        actual_default = int(rng.random() < actual_default_risk)

        rows.append(
            {
                "row_id": f"{monitoring_date.isoformat()}-{index + 1}",
                "window": "current",
                "monitoring_date": monitoring_date.isoformat(),
                "credit_utilization": round(credit_utilization, 6),
                "payment_ratio": round(payment_ratio, 6),
                "support_tickets_30d": support_tickets,
                "prediction_latency_ms": round(prediction_latency, 6),
                "predicted_default_risk": round(predicted_default_risk, 6),
                "actual_default": actual_default,
            }
        )
    return rows


def simulate_datasets(
    seed: int = SIMULATION_SEED,
) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]]]:
    rng = random.Random(seed)
    reference_rows = _simulate_reference_window(REFERENCE_ROWS, rng)
    rolling_rows: list[dict[str, float | int | str]] = []
    for day_index in range(ROLLING_DAYS):
        rolling_rows.extend(_simulate_current_day(day_index, ROLLING_ROWS_PER_DAY, rng))
    return reference_rows, rolling_rows


def split_rolling_windows(
    rows: list[dict[str, float | int | str]],
) -> list[tuple[str, list[dict[str, float | int | str]]]]:
    buckets: dict[str, list[dict[str, float | int | str]]] = {}
    for row in rows:
        monitoring_date = str(row["monitoring_date"])
        buckets.setdefault(monitoring_date, []).append(row)
    return sorted(buckets.items(), key=lambda item: item[0])


def _write_rows(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def persist_simulation(seed: int = SIMULATION_SEED) -> tuple[Path, Path]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    reference_rows, rolling_rows = simulate_datasets(seed=seed)
    _write_rows(REFERENCE_PATH, reference_rows)
    _write_rows(ROLLING_PATH, rolling_rows)
    return REFERENCE_PATH, ROLLING_PATH


def read_rows(path: Path) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "row_id": row["row_id"],
                    "window": row["window"],
                    "monitoring_date": row["monitoring_date"],
                    "credit_utilization": float(row["credit_utilization"]),
                    "payment_ratio": float(row["payment_ratio"]),
                    "support_tickets_30d": int(row["support_tickets_30d"]),
                    "prediction_latency_ms": float(row["prediction_latency_ms"]),
                    "predicted_default_risk": float(row["predicted_default_risk"]),
                    "actual_default": int(row["actual_default"]),
                }
            )
    return rows

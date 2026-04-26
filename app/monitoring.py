import math
from statistics import mean

from app.models import Alert, FeatureDriftMetric, MonitoringSummary, PerformanceComparison, PerformanceWindowMetric, PredictionDriftMetric

FEATURES = [
    "credit_utilization",
    "payment_ratio",
    "support_tickets_30d",
    "prediction_latency_ms",
]


def _extract(rows: list[dict[str, float | int | str]], key: str) -> list[float]:
    return [float(row[key]) for row in rows]


def _quantile_edges(values: list[float], buckets: int = 10) -> list[float]:
    ordered = sorted(values)
    edges: list[float] = []
    for bucket in range(1, buckets):
        index = min(len(ordered) - 1, int(len(ordered) * bucket / buckets))
        edges.append(ordered[index])
    return edges


def _bin_counts(values: list[float], edges: list[float]) -> list[int]:
    counts = [0] * (len(edges) + 1)
    for value in values:
        bucket = 0
        while bucket < len(edges) and value > edges[bucket]:
            bucket += 1
        counts[bucket] += 1
    return counts


def population_stability_index(reference_values: list[float], current_values: list[float], buckets: int = 10) -> float:
    edges = _quantile_edges(reference_values, buckets=buckets)
    reference_counts = _bin_counts(reference_values, edges)
    current_counts = _bin_counts(current_values, edges)
    epsilon = 1e-6
    psi = 0.0
    total_reference = len(reference_counts) and len(reference_values)
    total_current = len(current_counts) and len(current_values)
    for reference_count, current_count in zip(reference_counts, current_counts):
        reference_ratio = max(reference_count / total_reference, epsilon)
        current_ratio = max(current_count / total_current, epsilon)
        psi += (current_ratio - reference_ratio) * math.log(current_ratio / reference_ratio)
    return psi


def ks_statistic(reference_values: list[float], current_values: list[float]) -> float:
    ordered_reference = sorted(reference_values)
    ordered_current = sorted(current_values)
    points = sorted(set(ordered_reference + ordered_current))
    ref_index = 0
    cur_index = 0
    max_distance = 0.0

    for point in points:
        while ref_index < len(ordered_reference) and ordered_reference[ref_index] <= point:
            ref_index += 1
        while cur_index < len(ordered_current) and ordered_current[cur_index] <= point:
            cur_index += 1
        reference_cdf = ref_index / len(ordered_reference)
        current_cdf = cur_index / len(ordered_current)
        max_distance = max(max_distance, abs(reference_cdf - current_cdf))

    return max_distance


def _status_from_psi(psi: float) -> str:
    if psi >= 0.25:
        return "critical"
    if psi >= 0.12:
        return "warning"
    return "healthy"


def _status_from_prediction_shift(ks_value: float, mean_delta: float, high_risk_delta: float) -> str:
    if ks_value >= 0.18 or abs(mean_delta) >= 0.08 or abs(high_risk_delta) >= 0.10:
        return "critical"
    if ks_value >= 0.10 or abs(mean_delta) >= 0.04 or abs(high_risk_delta) >= 0.05:
        return "warning"
    return "healthy"


def _status_from_performance(log_loss_delta: float, accuracy_delta: float, positive_rate_delta: float) -> str:
    if log_loss_delta >= 0.10 or accuracy_delta <= -0.06 or positive_rate_delta >= 0.08:
        return "critical"
    if log_loss_delta >= 0.05 or accuracy_delta <= -0.03 or positive_rate_delta >= 0.04:
        return "warning"
    return "healthy"


def compute_feature_drift(reference_rows: list[dict[str, float | int | str]], current_rows: list[dict[str, float | int | str]]) -> list[FeatureDriftMetric]:
    metrics: list[FeatureDriftMetric] = []
    for feature in FEATURES:
        reference_values = _extract(reference_rows, feature)
        current_values = _extract(current_rows, feature)
        psi = population_stability_index(reference_values, current_values)
        reference_mean = mean(reference_values)
        current_mean = mean(current_values)
        metrics.append(
            FeatureDriftMetric(
                name=feature,
                reference_mean=round(reference_mean, 4),
                current_mean=round(current_mean, 4),
                mean_delta=round(current_mean - reference_mean, 4),
                population_stability_index=round(psi, 4),
                status=_status_from_psi(psi),
            )
        )
    return metrics


def compute_prediction_drift(reference_rows: list[dict[str, float | int | str]], current_rows: list[dict[str, float | int | str]]) -> PredictionDriftMetric:
    reference_scores = _extract(reference_rows, "predicted_default_risk")
    current_scores = _extract(current_rows, "predicted_default_risk")
    reference_mean_score = mean(reference_scores)
    current_mean_score = mean(current_scores)
    reference_high_risk_rate = sum(score >= 0.5 for score in reference_scores) / len(reference_scores)
    current_high_risk_rate = sum(score >= 0.5 for score in current_scores) / len(current_scores)
    mean_score_delta = current_mean_score - reference_mean_score
    high_risk_delta = current_high_risk_rate - reference_high_risk_rate
    ks_value = ks_statistic(reference_scores, current_scores)
    return PredictionDriftMetric(
        reference_mean_score=round(reference_mean_score, 4),
        current_mean_score=round(current_mean_score, 4),
        mean_score_delta=round(mean_score_delta, 4),
        ks_statistic=round(ks_value, 4),
        reference_high_risk_rate=round(reference_high_risk_rate, 4),
        current_high_risk_rate=round(current_high_risk_rate, 4),
        status=_status_from_prediction_shift(ks_value, mean_score_delta, high_risk_delta),
    )


def _safe_probability(value: float) -> float:
    return min(max(value, 1e-6), 1.0 - 1e-6)


def _performance_window(rows: list[dict[str, float | int | str]]) -> PerformanceWindowMetric:
    probabilities = _extract(rows, "predicted_default_risk")
    labels = [int(row["actual_default"]) for row in rows]
    predictions = [int(probability >= 0.5) for probability in probabilities]
    accuracy = sum(int(prediction == label) for prediction, label in zip(predictions, labels)) / len(labels)
    positive_rate = sum(labels) / len(labels)
    brier_score = sum((probability - label) ** 2 for probability, label in zip(probabilities, labels)) / len(labels)
    log_loss = -sum(
        label * math.log(_safe_probability(probability))
        + (1 - label) * math.log(_safe_probability(1 - probability))
        for probability, label in zip(probabilities, labels)
    ) / len(labels)
    return PerformanceWindowMetric(
        accuracy=round(accuracy, 4),
        positive_rate=round(positive_rate, 4),
        brier_score=round(brier_score, 4),
        log_loss=round(log_loss, 4),
    )


def compute_performance(reference_rows: list[dict[str, float | int | str]], current_rows: list[dict[str, float | int | str]]) -> PerformanceComparison:
    reference = _performance_window(reference_rows)
    current = _performance_window(current_rows)
    accuracy_delta = round(current.accuracy - reference.accuracy, 4)
    positive_rate_delta = round(current.positive_rate - reference.positive_rate, 4)
    brier_delta = round(current.brier_score - reference.brier_score, 4)
    log_loss_delta = round(current.log_loss - reference.log_loss, 4)
    status = _status_from_performance(log_loss_delta, accuracy_delta, positive_rate_delta)
    return PerformanceComparison(
        reference=reference,
        current=current,
        accuracy_delta=accuracy_delta,
        positive_rate_delta=positive_rate_delta,
        brier_score_delta=brier_delta,
        log_loss_delta=log_loss_delta,
        status=status,
    )


def build_alerts(feature_metrics: list[FeatureDriftMetric], prediction_metric: PredictionDriftMetric, performance: PerformanceComparison) -> list[Alert]:
    alerts: list[Alert] = []
    for feature_metric in feature_metrics:
        if feature_metric.status == "healthy":
            continue
        alerts.append(
            Alert(
                area="feature_drift",
                metric=feature_metric.name,
                status=feature_metric.status,
                message=(
                    f"{feature_metric.name} moved from {feature_metric.reference_mean:.4f} "
                    f"to {feature_metric.current_mean:.4f} with PSI {feature_metric.population_stability_index:.4f}."
                ),
            )
        )

    if prediction_metric.status != "healthy":
        alerts.append(
            Alert(
                area="prediction_drift",
                metric="predicted_default_risk",
                status=prediction_metric.status,
                message=(
                    f"Prediction score mean moved by {prediction_metric.mean_score_delta:.4f} "
                    f"and KS reached {prediction_metric.ks_statistic:.4f}."
                ),
            )
        )

    if performance.status != "healthy":
        alerts.append(
            Alert(
                area="performance",
                metric="delayed_outcomes",
                status=performance.status,
                message=(
                    f"Accuracy delta is {performance.accuracy_delta:.4f}, "
                    f"log-loss delta is {performance.log_loss_delta:.4f}, "
                    f"and positive-rate delta is {performance.positive_rate_delta:.4f}."
                ),
            )
        )

    return alerts


def _overall_status(alerts: list[Alert]) -> str:
    if any(alert.status == "critical" for alert in alerts):
        return "critical"
    if any(alert.status == "warning" for alert in alerts):
        return "warning"
    return "healthy"


def _summary_text(feature_metrics: list[FeatureDriftMetric], prediction_metric: PredictionDriftMetric, performance: PerformanceComparison, overall_status: str) -> str:
    worst_feature = max(feature_metrics, key=lambda metric: metric.population_stability_index)
    return (
        f"Overall status is {overall_status}. The strongest feature drift is on {worst_feature.name} "
        f"(PSI {worst_feature.population_stability_index:.4f}), prediction KS is "
        f"{prediction_metric.ks_statistic:.4f}, and current-window log loss changed by "
        f"{performance.log_loss_delta:.4f}."
    )


def build_monitoring_summary(reference_rows: list[dict[str, float | int | str]], current_rows: list[dict[str, float | int | str]]) -> MonitoringSummary:
    feature_metrics = compute_feature_drift(reference_rows, current_rows)
    prediction_metric = compute_prediction_drift(reference_rows, current_rows)
    performance = compute_performance(reference_rows, current_rows)
    alerts = build_alerts(feature_metrics, prediction_metric, performance)
    overall_status = _overall_status(alerts)

    recommended_actions = [
        "Inspect the upstream feature generation path for distribution changes in the flagged features.",
        "Review score calibration and threshold policy before retraining or rollback decisions.",
        "Compare the current window against the latest labeled slice to confirm whether degradation is persistent.",
    ]

    return MonitoringSummary(
        incident_id="mdl-monitoring-2026-04-26",
        overall_status=overall_status,
        reference_rows=len(reference_rows),
        current_rows=len(current_rows),
        feature_drift=feature_metrics,
        prediction_drift=prediction_metric,
        performance=performance,
        alerts=alerts,
        summary=_summary_text(feature_metrics, prediction_metric, performance, overall_status),
        recommended_actions=recommended_actions,
    )

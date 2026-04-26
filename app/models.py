from dataclasses import asdict, dataclass


@dataclass
class FeatureDriftMetric:
    name: str
    reference_mean: float
    current_mean: float
    mean_delta: float
    population_stability_index: float
    status: str


@dataclass
class PredictionDriftMetric:
    reference_mean_score: float
    current_mean_score: float
    mean_score_delta: float
    ks_statistic: float
    reference_high_risk_rate: float
    current_high_risk_rate: float
    status: str


@dataclass
class PerformanceWindowMetric:
    accuracy: float
    positive_rate: float
    brier_score: float
    log_loss: float


@dataclass
class PerformanceComparison:
    reference: PerformanceWindowMetric
    current: PerformanceWindowMetric
    accuracy_delta: float
    positive_rate_delta: float
    brier_score_delta: float
    log_loss_delta: float
    status: str


@dataclass
class Alert:
    area: str
    metric: str
    status: str
    message: str


@dataclass
class MonitoringSummary:
    incident_id: str
    overall_status: str
    reference_rows: int
    current_rows: int
    feature_drift: list[FeatureDriftMetric]
    prediction_drift: PredictionDriftMetric
    performance: PerformanceComparison
    alerts: list[Alert]
    summary: str
    recommended_actions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

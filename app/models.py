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
class DailyWindowSummary:
    monitoring_date: str
    rows: int
    overall_status: str
    strongest_feature: str
    strongest_feature_psi: float
    prediction_ks_statistic: float
    current_default_rate: float
    log_loss: float
    log_loss_delta: float


@dataclass
class MonitoringSummary:
    incident_id: str
    overall_status: str
    reference_rows: int
    current_rows: int
    latest_window_date: str
    rolling_window_days: int
    rolling_daily_windows: list[DailyWindowSummary]
    feature_drift: list[FeatureDriftMetric]
    prediction_drift: PredictionDriftMetric
    performance: PerformanceComparison
    alerts: list[Alert]
    summary: str
    recommended_actions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

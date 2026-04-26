from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT_DIR / "generated"

REFERENCE_PATH = GENERATED_DIR / "reference_window.csv"
ROLLING_PATH = GENERATED_DIR / "rolling_daily_windows.csv"
SUMMARY_PATH = GENERATED_DIR / "monitoring_summary.json"
REPORT_PATH = GENERATED_DIR / "incident_report.md"
DASHBOARD_PATH = GENERATED_DIR / "monitoring_dashboard.html"

REFERENCE_ROWS = 2_000
ROLLING_DAYS = 5
ROLLING_ROWS_PER_DAY = 400
SIMULATION_SEED = 20260426

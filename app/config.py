from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT_DIR / "generated"

REFERENCE_PATH = GENERATED_DIR / "reference_window.csv"
CURRENT_PATH = GENERATED_DIR / "current_window.csv"
SUMMARY_PATH = GENERATED_DIR / "monitoring_summary.json"
REPORT_PATH = GENERATED_DIR / "incident_report.md"
DASHBOARD_PATH = GENERATED_DIR / "monitoring_dashboard.html"

REFERENCE_ROWS = 2_000
CURRENT_ROWS = 2_000
SIMULATION_SEED = 20260426

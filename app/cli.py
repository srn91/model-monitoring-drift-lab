from app.monitoring import build_monitoring_summary
from app.reporting import write_outputs
from app.simulation import persist_simulation, read_rows


def simulate() -> None:
    reference_path, rolling_path = persist_simulation()
    print(f"wrote {reference_path}")
    print(f"wrote {rolling_path}")


def report() -> None:
    reference_path, rolling_path = persist_simulation()
    reference_rows = read_rows(reference_path)
    rolling_rows = read_rows(rolling_path)
    summary = build_monitoring_summary(reference_rows, rolling_rows)
    summary_path, report_path, dashboard_path = write_outputs(summary)
    print(f"overall_status={summary.overall_status}")
    print(f"summary_path={summary_path}")
    print(f"report_path={report_path}")
    print(f"dashboard_path={dashboard_path}")


def main() -> None:
    import sys

    if len(sys.argv) != 2 or sys.argv[1] not in {"simulate", "report"}:
        raise SystemExit("usage: python3 -m app.cli [simulate|report]")

    command = sys.argv[1]
    if command == "simulate":
        simulate()
        return

    report()


if __name__ == "__main__":
    main()

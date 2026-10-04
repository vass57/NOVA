"""Command-line runner for reproducible, non-interactive reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from corroboria.export import audit_to_json, cases_to_csv, run_to_excel
from corroboria.pipeline import InputPaths, InputValidationError, run_reconciliation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CorroborIA deterministic reconciliation.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    arguments = parser.parse_args()
    try:
        run = run_reconciliation(InputPaths.from_data_directory(arguments.data_dir))
    except InputValidationError as error:
        parser.error("\n".join(error.issues))
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    (arguments.output_dir / "corroboria_cases.csv").write_bytes(cases_to_csv(run.cases))
    (arguments.output_dir / "corroboria_report.xlsx").write_bytes(run_to_excel(run))
    (arguments.output_dir / "corroboria_run_audit.json").write_bytes(audit_to_json(run))
    print(run.summary.to_string(index=False))
    print(f"Reports written to {arguments.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

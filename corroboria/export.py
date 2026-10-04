"""Report exporters that never modify the source datasets."""

from __future__ import annotations

from io import BytesIO
import json

import pandas as pd

from corroboria.pipeline import ReconciliationRun


def cases_to_csv(cases: pd.DataFrame) -> bytes:
    """Build a UTF-8 CSV with a BOM for Excel-compatible downloads."""

    return cases.to_csv(index=False).encode("utf-8-sig")


def run_to_excel(run: ReconciliationRun) -> bytes:
    """Build an audit-friendly Excel report in memory."""

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        run.cases.to_excel(writer, sheet_name="Cases", index=False)
        run.summary.to_excel(writer, sheet_name="Summary", index=False)
        run.mapping.to_excel(writer, sheet_name="Mapping", index=False)
        pd.DataFrame([run.audit]).to_excel(writer, sheet_name="Run audit", index=False)
    return output.getvalue()


def audit_to_json(run: ReconciliationRun) -> bytes:
    """Export the reproducibility record independently from case data."""

    return json.dumps(run.audit, indent=2, ensure_ascii=False).encode("utf-8")

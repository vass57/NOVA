"""Report exporters that never modify source datasets."""

from __future__ import annotations

from io import BytesIO
import json

import pandas as pd

from corroboria.pipeline import ReconciliationRun


# ============================================================
# CSV
# ============================================================

def cases_to_csv(
    cases: pd.DataFrame,
) -> bytes:
    """Build a UTF-8 CSV with BOM for Excel compatibility."""

    return (
        cases
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


# ============================================================
# EXCEL FORMATTING
# ============================================================

def _format_workbook(
    writer: pd.ExcelWriter,
) -> None:
    """Apply lightweight usability formatting."""

    workbook = writer.book

    for worksheet in workbook.worksheets:

        worksheet.freeze_panes = "A2"

        if (
            worksheet.max_row
            >=
            1
            and
            worksheet.max_column
            >=
            1
        ):

            worksheet.auto_filter.ref = (
                worksheet.dimensions
            )

        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = (
                column_cells[
                    0
                ].column_letter
            )

            for cell in column_cells:

                value = cell.value

                if value is None:
                    continue

                length = len(
                    str(
                        value
                    )
                )

                max_length = max(
                    max_length,
                    length,
                )

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max(
                    max_length
                    +
                    2,
                    10,
                ),
                50,
            )


# ============================================================
# EXCEL REPORT
# ============================================================

def run_to_excel(
    run: ReconciliationRun,
) -> bytes:
    """Build the complete CorroborIA workbook in memory."""

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        # ----------------------------------------------------
        # Reviewer-facing sheets
        # ----------------------------------------------------

        run.summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        run.cases.to_excel(
            writer,
            sheet_name="Cases",
            index=False,
        )

        run.investigation_report.to_excel(
            writer,
            sheet_name="Investigation",
            index=False,
        )

        # ----------------------------------------------------
        # Full technical trace
        # ----------------------------------------------------

        run.final_report.to_excel(
            writer,
            sheet_name="Full report",
            index=False,
        )

        run.mapping.to_excel(
            writer,
            sheet_name="Mapping",
            index=False,
        )

        run.assignment_matches.to_excel(
            writer,
            sheet_name="Assignment matches",
            index=False,
        )

        run.employee_matches.to_excel(
            writer,
            sheet_name="Employee matches",
            index=False,
        )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        run.ai_queue.to_excel(
            writer,
            sheet_name="AI queue",
            index=False,
        )

        run.ai_assignment_analysis.to_excel(
            writer,
            sheet_name="AI assignments",
            index=False,
        )

        run.ai_priorities.to_excel(
            writer,
            sheet_name="AI priorities",
            index=False,
        )

        run.ai_patterns.to_excel(
            writer,
            sheet_name="AI patterns",
            index=False,
        )

        # ----------------------------------------------------
        # Audit
        # ----------------------------------------------------

        pd.DataFrame(
            [
                {
                    key:
                        (
                            json.dumps(
                                value,
                                ensure_ascii=False,
                                default=str,
                            )
                            if isinstance(
                                value,
                                (
                                    dict,
                                    list,
                                ),
                            )
                            else
                            value
                        )
                    for (
                        key,
                        value,
                    )
                    in run.audit.items()
                }
            ]
        ).to_excel(
            writer,
            sheet_name="Run audit",
            index=False,
        )

        _format_workbook(
            writer
        )

    return output.getvalue()


# ============================================================
# JSON AUDIT
# ============================================================

def audit_to_json(
    run: ReconciliationRun,
) -> bytes:
    """Export reproducibility metadata independently."""

    return json.dumps(
        run.audit,
        indent=2,
        ensure_ascii=False,
        default=str,
    ).encode(
        "utf-8"
    )
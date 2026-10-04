"""Auditable reconciliation pipeline for the CorroborIA challenge.

This module is the shared orchestration layer used by the Streamlit
application and, eventually, the command-line interface.

Important design principle:

    Deterministic rules establish the corroboration verdict.
    AI may assist with ambiguous matching, prioritization, and pattern
    analysis, but it never silently overrides a deterministic verdict.

The pipeline:

    1. Loads the five approved challenge inputs
    2. Preserves the original source data
    3. Normalizes working copies
    4. Parses Mapping.xlsx
    5. Matches employees
    6. Matches assignments conservatively
    7. Runs direct field comparisons
    8. Applies deterministic business rules
    9. Builds the verified unified report
    10. Runs local AI analysis
    11. Converts results to reviewer-friendly cases

No input file is modified.
No external AI service is called.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd

from corroboria.assignment_matcher import match_assignments
from corroboria.business_rules import evaluate_rule_based_fields
from corroboria.comparator import compare_direct_mappings
from corroboria.mapping_parser import (
    parse_employment_rules,
    parse_mapping_sheet,
    validate_direct_mappings,
)
from corroboria.matcher import (
    find_missing_employee_ids,
    match_employees,
)
from corroboria.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_identifier,
    normalize_number,
    normalize_text,
)

# ============================================================
# VERIFIED FINAL REPORT LAYER
# ============================================================

from corroboria.final_report import (
    build_ai_queue,
    build_final_report,
    build_investigation_report,
)

# ============================================================
# LOCAL AI LAYER
# ============================================================

from corroboria.ai_analyzer import (
    analyze_ambiguous_assignments,
    prioritize_anomalies,
    summarize_anomaly_patterns,
)


# ============================================================
# TYPES
# ============================================================

InputValue = Path | BinaryIO


# ============================================================
# REVIEWER-FACING VERDICTS
# ============================================================

VERDICTS = {
    "Match",
    "Justified difference",
    "Actual anomaly",
    "Needs review",
}


# ============================================================
# CASE OUTPUT COLUMNS
# ============================================================

CASE_COLUMNS = [
    "case_id",
    "record_identifier",
    "assignment_type",
    "source_row",
    "destination_row",
    "mapping_row",
    "field",
    "description",
    "source_value",
    "source_normalized_value",
    "destination_value",
    "destination_normalized_value",
    "expected_value",
    "verdict",
    "rule_ids",
    "decision_method",
    "priority",
    "priority_reason",
    "confidence",
    "limitation_code",
    "explanation",
    "supporting_records",
    "ai_contributed",
    "ai_status",
    "ai_score",
    "pattern_type",
]


# ============================================================
# EXCEPTIONS
# ============================================================

class InputValidationError(ValueError):
    """Raised when an input cannot support reliable reconciliation."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))


# ============================================================
# INPUT PATHS
# ============================================================

@dataclass(frozen=True)
class InputPaths:
    """The five approved challenge inputs required for one run."""

    source: InputValue
    destination: InputValue
    mapping: InputValue
    job_details: InputValue
    employment_reasons: InputValue

    @classmethod
    def from_data_directory(
        cls,
        data_directory: Path,
    ) -> "InputPaths":
        """Locate the supplied challenge files without relying on CWD."""

        def one(pattern: str) -> Path:
            matches = sorted(
                data_directory.glob(pattern)
            )

            if len(matches) != 1:
                raise InputValidationError(
                    [
                        (
                            f"Expected exactly one '{pattern}' file "
                            f"in {data_directory}; found {len(matches)}."
                        )
                    ]
                )

            return matches[0]

        return cls(
            source=one(
                "Employe_Source_*.xlsx"
            ),
            destination=one(
                "Employe_Destination_*.xlsx"
            ),
            mapping=one(
                "Mapping.xlsx"
            ),
            job_details=one(
                "d*tail_du_poste.xlsx"
            ),
            employment_reasons=one(
                "Motif de la situation d'emploi.xlsx"
            ),
        )


# ============================================================
# COMPLETE RECONCILIATION RESULT
# ============================================================

@dataclass
class ReconciliationRun:
    """A complete, reproducible CorroborIA result."""

    # Reviewer-facing data
    cases: pd.DataFrame
    mapping: pd.DataFrame
    employee_matches: pd.DataFrame
    assignment_matches: pd.DataFrame
    validation_issues: pd.DataFrame
    audit: dict[str, object]

    # Full technical outputs
    final_report: pd.DataFrame
    investigation_report: pd.DataFrame
    ai_queue: pd.DataFrame

    # AI outputs
    ai_assignment_analysis: pd.DataFrame
    ai_priorities: pd.DataFrame
    ai_patterns: pd.DataFrame

    @property
    def summary(self) -> pd.DataFrame:
        """Return reviewer-facing verdict counts."""

        counts = (
            self.cases[
                "verdict"
            ]
            .value_counts()
            .reindex(
                [
                    "Actual anomaly",
                    "Needs review",
                    "Justified difference",
                    "Match",
                ],
                fill_value=0,
            )
            .rename_axis(
                "verdict"
            )
            .reset_index(
                name="field_comparisons_or_cases"
            )
        )

        return counts


# ============================================================
# FILE READING HELPERS
# ============================================================

def _file_name(
    value: InputValue,
) -> str:
    """Return a lowercase input filename when available."""

    return str(
        getattr(
            value,
            "name",
            value,
        )
    ).lower()


def _rewind(
    value: InputValue,
) -> None:
    """Reset uploaded streams before reuse."""

    if isinstance(
        value,
        Path,
    ):
        return

    if hasattr(
        value,
        "seek",
    ):
        try:
            value.seek(0)
        except Exception:
            pass


def _read_table(
    value: InputValue,
) -> pd.DataFrame:
    """Load a CSV or first worksheet from an Excel file."""

    _rewind(
        value
    )

    name = _file_name(
        value
    )

    if name.endswith(
        ".csv"
    ):
        return pd.read_csv(
            value,
            dtype=object,
        )

    return pd.read_excel(
        value,
        dtype=object,
        engine="openpyxl",
    )


def _read_workbook(
    value: InputValue,
) -> dict[str, pd.DataFrame]:
    """Load every worksheet in an Excel workbook."""

    _rewind(
        value
    )

    name = _file_name(
        value
    )

    if name.endswith(
        ".csv"
    ):
        raise InputValidationError(
            [
                (
                    "Mapping and lookup inputs that require "
                    "multiple sheets must be Excel workbooks."
                )
            ]
        )

    return pd.read_excel(
        value,
        sheet_name=None,
        dtype=object,
        engine="openpyxl",
    )


def _only_sheet(
    workbook: dict[str, pd.DataFrame],
    label: str,
) -> pd.DataFrame:
    """Return the only worksheet from a one-sheet workbook."""

    if len(
        workbook
    ) != 1:
        raise InputValidationError(
            [
                (
                    f"{label} must contain exactly one worksheet; "
                    f"found {len(workbook)}."
                )
            ]
        )

    return next(
        iter(
            workbook.values()
        )
    ).copy()


def _read_single_input(
    value: InputValue,
    label: str,
) -> pd.DataFrame:
    """Load a supplementary one-table input."""

    name = _file_name(
        value
    )

    if name.endswith(
        ".csv"
    ):
        return _read_table(
            value
        )

    return _only_sheet(
        _read_workbook(
            value
        ),
        label,
    )


# ============================================================
# JOB DETAIL REPAIR
# ============================================================

def _repair_job_details(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Repair comma-separated data embedded inside one Excel column."""

    if len(
        frame.columns
    ) != 1:
        return frame.copy()

    header = str(
        frame.columns[
            0
        ]
    )

    if "," not in header:
        return frame.copy()

    rows = [
        header
    ]

    for value in frame.iloc[
        :,
        0
    ]:
        if pd.isna(
            value
        ):
            rows.append(
                ""
            )
        else:
            rows.append(
                str(
                    value
                )
            )

    csv_text = "\n".join(
        rows
    )

    return pd.read_csv(
        StringIO(
            csv_text
        ),
        dtype=object,
    )


# ============================================================
# GENERIC NORMALIZATION
# ============================================================

def _normalise(
    frame: pd.DataFrame,
    columns: dict[str, Any],
) -> pd.DataFrame:
    """Apply normalizers to a working copy of a dataframe."""

    result = frame.copy()

    for (
        column,
        function,
    ) in columns.items():

        if column in result.columns:
            result[
                column
            ] = result[
                column
            ].map(
                function
            )

    return result


# ============================================================
# SYSTEM A NORMALIZATION
# ============================================================

def _normalise_source(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    identifier = (
        normalize_identifier
    )

    return _normalise(
        frame,
        {
            # -----------------------------------------------
            # IDENTIFIERS
            # -----------------------------------------------

            "Matricule":
                identifier,

            "CodePoste":
                identifier,

            "CodeEmploi":
                identifier,

            "ÉchelleSalariale":
                identifier,

            "CodeImputation":
                identifier,

            "CodeDirection":
                identifier,

            "CodeSite":
                identifier,

            "CatégorieEmploi":
                identifier,

            "CodeStatutEmploi":
                identifier,

            "CodeRaisonStatut":
                identifier,

            "CodeSuspensionAccès":
                identifier,

            "IdentifiantResponsable":
                identifier,

            "CodeQuart":
                identifier,

            # -----------------------------------------------
            # TEXT
            # -----------------------------------------------

            "NomFamille":
                normalize_text,

            "PrénomUsuel":
                normalize_text,

            "TypeAffectation":
                normalize_text,

            "IntituléPoste":
                normalize_text,

            "IntituléEmploi":
                normalize_text,

            "LibelléÉchelleSalariale":
                normalize_text,

            "LibelléImputation":
                normalize_text,

            "LibelléDirection":
                normalize_text,

            "LibelléSite":
                normalize_text,

            "LibelléRaisonStatut":
                normalize_text,

            "NomResponsable":
                normalize_text,

            # -----------------------------------------------
            # DATES
            # -----------------------------------------------

            "DateEmbaucheRécente":
                normalize_date,

            "DateEntréePoste":
                normalize_date,

            "DateSortiePoste":
                normalize_date,

            "DateEffetRaison":
                normalize_date,

            "DateRetourAnticipée":
                normalize_date,

            # -----------------------------------------------
            # BOOLEANS
            # -----------------------------------------------

            "EstPermanent":
                normalize_boolean,

            "EstTempsPlein":
                normalize_boolean,

            # -----------------------------------------------
            # NUMERIC
            # -----------------------------------------------

            "HeuresNormeHebdo":
                normalize_number,

            "HeuresNormeQuotidienne":
                normalize_number,
        },
    )


# ============================================================
# SYSTEM B NORMALIZATION
# ============================================================

def _normalise_destination(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    identifier = (
        normalize_identifier
    )

    return _normalise(
        frame,
        {
            # -----------------------------------------------
            # IDENTIFIERS
            # -----------------------------------------------

            "personId":
                identifier,

            "statusReasonCode":
                identifier,

            "siteId":
                identifier,

            "siteCode":
                identifier,

            "divisionId":
                identifier,

            "divisionCode":
                identifier,

            "positionId":
                identifier,

            "positionCode":
                identifier,

            "payGradeId":
                identifier,

            "externalReferenceId":
                identifier,

            # -----------------------------------------------
            # TEXT
            # -----------------------------------------------

            "givenName":
                normalize_text,

            "surname":
                normalize_text,

            "contactEmail":
                normalize_text,

            "activityStatus":
                normalize_text,

            "contractTypeCode":
                normalize_text,

            "detailedStatus":
                normalize_text,

            "siteName":
                normalize_text,

            "divisionName":
                normalize_text,

            "positionName":
                normalize_text,

            # -----------------------------------------------
            # DATES
            # -----------------------------------------------

            "onboardDate":
                normalize_date,

            "expectedReturnDate":
                normalize_date,

            "assignmentStartDate":
                normalize_date,

            "assignmentEndDate":
                normalize_date,

            "termStartDate":
                normalize_date,

            "termEndDate":
                normalize_date,

            # -----------------------------------------------
            # BOOLEANS
            # -----------------------------------------------

            "isPrimaryAssignment":
                normalize_boolean,

            "isTemporaryAssignment":
                normalize_boolean,

            # -----------------------------------------------
            # NUMBERS
            # -----------------------------------------------

            "wageOverrideAmount":
                normalize_number,

            "wageMultiplierFactor":
                normalize_number,

            "weeklyHoursOverride":
                normalize_number,

            "dailyHoursOverride":
                normalize_number,
        },
    )


# ============================================================
# JOB DETAIL NORMALIZATION
# ============================================================

def _normalise_job_details(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    identifier = (
        normalize_identifier
    )

    return _normalise(
        frame,
        {
            "IdentifiantPoste":
                identifier,

            "IdentifiantEmploi":
                identifier,

            "CodeDirectionAffectée":
                identifier,

            "CodeBudget":
                identifier,

            "IndicateurGestion":
                identifier,

            "CodePosteSecondaire":
                identifier,

            "MatriculeGestionnaire":
                identifier,

            "DateEffetAffectation":
                normalize_date,

            "HeuresSemaineContrat":
                normalize_number,

            "HeuresJourContrat":
                normalize_number,

            "JoursTravailléesSemaine":
                normalize_number,
        },
    )


# ============================================================
# EMPLOYMENT REASON NORMALIZATION
# ============================================================

def _normalise_employment_reasons(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    identifier = (
        normalize_identifier
    )

    return _normalise(
        frame,
        {
            "CodeCatégorieStatut":
                identifier,

            "CodeStatutSystèmeExterne":
                identifier,

            "CodeGestionAccès":
                identifier,
        },
    )


# ============================================================
# VALIDATION HELPERS
# ============================================================

def _required_columns(
    frame: pd.DataFrame,
    name: str,
    columns: set[str],
) -> list[str]:
    """Return validation errors for required columns."""

    missing = sorted(
        columns.difference(
            frame.columns
        )
    )

    if not missing:
        return []

    return [
        (
            f"{name} is missing required column(s): "
            f"{', '.join(missing)}."
        )
    ]


def _mapping_sheet(
    workbook: dict[str, pd.DataFrame],
    name: str,
) -> pd.DataFrame:
    """Return a required Mapping.xlsx worksheet."""

    if name not in workbook:
        raise InputValidationError(
            [
                (
                    f"Mapping.xlsx is missing required worksheet "
                    f"'{name}'."
                )
            ]
        )

    return workbook[
        name
    ].copy()


# ============================================================
# SAFE VALUES / JSON
# ============================================================

def _value(
    value: object,
) -> object:
    """Convert pandas values into export-safe values."""

    if value is None:
        return None

    if isinstance(
        value,
        (
            list,
            dict,
            tuple,
        ),
    ):
        return value

    try:
        if pd.isna(
            value
        ):
            return None
    except (
        TypeError,
        ValueError,
    ):
        pass

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    return value


def _json(
    value: object,
) -> str:
    """Serialize evidence consistently."""

    if value is None:
        return "{}"

    if isinstance(
        value,
        str,
    ):
        # If it already contains JSON, preserve it.
        try:
            json.loads(
                value
            )
            return value
        except (
            json.JSONDecodeError,
            TypeError,
        ):
            pass

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
        sort_keys=True,
    )


# ============================================================
# CASE ID
# ============================================================

def _case_id(
    record: dict[str, object],
) -> str:
    """Build a stable case ID from traceable case identity."""

    identity = "|".join(
        str(
            record.get(
                key,
                "",
            )
        )
        for key in (
            "record_identifier",
            "assignment_type",
            "source_row",
            "destination_row",
            "field",
            "rule_ids",
            "decision_method",
        )
    )

    digest = sha256(
        identity.encode(
            "utf-8"
        )
    ).hexdigest()[
        :12
    ].upper()

    return (
        f"CASE-{digest}"
    )


# ============================================================
# VERDICT TRANSLATION
# ============================================================

FINAL_TO_UI_VERDICT = {
    "CONFORME":
        "Match",

    "ECART_JUSTIFIE":
        "Justified difference",

    "ANOMALIE":
        "Actual anomaly",

    "A_INVESTIGUER":
        "Needs review",
}


# ============================================================
# PRIORITY TRANSLATION
# ============================================================

FINAL_TO_UI_PRIORITY = {
    "CRITIQUE":
        "High",

    "ÉLEVÉE":
        "High",

    "MOYENNE":
        "Medium",

    "FAIBLE":
        "Low",
}


# ============================================================
# DECISION METHOD TRANSLATION
# ============================================================

def _decision_method(
    row: pd.Series,
) -> str:

    layer = row.get(
        "comparison_layer"
    )

    if layer == "DIRECT":
        return (
            "direct comparison"
        )

    if layer == "BUSINESS_RULE":
        return (
            "deterministic business rule"
        )

    if layer == "STRUCTURAL":
        return (
            "assignment matching"
        )

    return (
        "input validation"
    )


# ============================================================
# PRIORITY REASON
# ============================================================

def _priority_reason(
    row: pd.Series,
) -> str:

    verdict = row.get(
        "verdict"
    )

    priority = row.get(
        "priority"
    )

    comparison_type = row.get(
        "comparison_type"
    )

    if priority == "CRITIQUE":
        return (
            "A structural record exists in only one system "
            "and requires immediate investigation."
        )

    if verdict == "ANOMALIE":
        return (
            "A deterministic expected value differs from "
            "System B."
        )

    if verdict == "A_INVESTIGUER":

        if (
            comparison_type
            ==
            "AMBIGUOUS_ASSIGNMENT_MATCH"
        ):
            return (
                "Multiple assignment candidates exist and "
                "deterministic matching cannot safely choose "
                "between them."
            )

        return (
            "Available evidence is incomplete, ambiguous, "
            "or affected by a known dataset limitation."
        )

    if verdict == "ECART_JUSTIFIE":
        return (
            "Raw values differ but approved normalization "
            "shows they represent the same information."
        )

    return (
        "The approved mapping and comparison logic agree."
    )


# ============================================================
# AI LOOKUPS
# ============================================================

def _build_ai_priority_lookup(
    ai_priorities: pd.DataFrame,
) -> dict[str, dict[str, object]]:
    """Build employee-level AI prioritization lookup."""

    lookup: dict[
        str,
        dict[str, object],
    ] = {}

    if ai_priorities.empty:
        return lookup

    for _, row in ai_priorities.iterrows():

        employee_id = str(
            row[
                "employee_id"
            ]
        )

        lookup[
            employee_id
        ] = {
            "score":
                _value(
                    row.get(
                        "ai_anomaly_score"
                    )
                ),

            "priority":
                _value(
                    row.get(
                        "ai_priority"
                    )
                ),

            "explanation":
                _value(
                    row.get(
                        "ai_explanation"
                    )
                ),
        }

    return lookup


def _build_pattern_lookup(
    ai_patterns: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, object]]:
    """Build field/verdict pattern lookup."""

    lookup: dict[
        tuple[str, str],
        dict[str, object],
    ] = {}

    if ai_patterns.empty:
        return lookup

    for _, row in ai_patterns.iterrows():

        field = str(
            row.get(
                "field"
            )
        )

        verdict = str(
            row.get(
                "verdict"
            )
        )

        lookup[
            (
                field,
                verdict,
            )
        ] = {
            "pattern_type":
                _value(
                    row.get(
                        "pattern_type"
                    )
                ),

            "prevalence":
                _value(
                    row.get(
                        "employee_prevalence"
                    )
                ),

            "affected_employees":
                _value(
                    row.get(
                        "affected_employees"
                    )
                ),

            "interpretation":
                _value(
                    row.get(
                        "ai_interpretation"
                    )
                ),
        }

    return lookup


def _build_assignment_ai_lookup(
    ai_assignment_analysis: pd.DataFrame,
) -> dict[str, dict[str, object]]:
    """Build one AI recommendation summary per ambiguous employee."""

    lookup: dict[
        str,
        dict[str, object],
    ] = {}

    if ai_assignment_analysis.empty:
        return lookup

    for employee_id, group in (
        ai_assignment_analysis.groupby(
            "employee_id"
        )
    ):

        employee_key = str(
            employee_id
        )

        selected = group[
            group[
                "selected_by_best_matching"
            ]
            ==
            True
        ]

        if selected.empty:

            lookup[
                employee_key
            ] = {
                "status":
                    "REVUE_HUMAINE",

                "score":
                    None,

                "confidence":
                    _value(
                        group[
                            "matching_confidence"
                        ].dropna().iloc[
                            0
                        ]
                    )
                    if (
                        "matching_confidence"
                        in group.columns
                        and
                        not group[
                            "matching_confidence"
                        ].dropna().empty
                    )
                    else
                    None,

                "pairs":
                    [],
            }

            continue

        pairs = []

        for _, row in selected.iterrows():

            pairs.append(
                {
                    "source_row":
                        int(
                            row[
                                "source_row_index"
                            ]
                        ),

                    "destination_row":
                        int(
                            row[
                                "destination_row_index"
                            ]
                        ),

                    "pair_match_score":
                        float(
                            row[
                                "pair_match_score"
                            ]
                        ),
                }
            )

        first = selected.iloc[
            0
        ]

        lookup[
            employee_key
        ] = {
            "status":
                str(
                    first.get(
                        "recommendation",
                        "PROPOSITION_IA",
                    )
                ),

            "score":
                _value(
                    first.get(
                        "best_matching_score"
                    )
                ),

            "confidence":
                _value(
                    first.get(
                        "matching_confidence"
                    )
                ),

            "margin":
                _value(
                    first.get(
                        "matching_margin"
                    )
                ),

            "pairs":
                pairs,

            "method":
                _value(
                    first.get(
                        "ai_method"
                    )
                ),
        }

    return lookup


# ============================================================
# DESCRIPTION LOOKUP
# ============================================================

def _mapping_description_lookup(
    mapping: pd.DataFrame,
) -> dict[int, object]:
    """Map Mapping.xlsx row numbers to human-readable descriptions."""

    result: dict[
        int,
        object,
    ] = {}

    for _, row in mapping.iterrows():

        mapping_row = row.get(
            "mapping_row"
        )

        if mapping_row is None:
            continue

        try:
            mapping_row_int = int(
                mapping_row
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        description = _value(
            row.get(
                "description"
            )
        )

        result[
            mapping_row_int
        ] = description

    return result


# ============================================================
# CONVERT VERIFIED FINAL REPORT TO APP CASES
# ============================================================

def _cases_from_final_report(
    final_report: pd.DataFrame,
    mapping: pd.DataFrame,
    ai_assignment_analysis: pd.DataFrame,
    ai_priorities: pd.DataFrame,
    ai_patterns: pd.DataFrame,
) -> pd.DataFrame:
    """Convert the verified report into the UI case schema."""

    if final_report.empty:
        return pd.DataFrame(
            columns=CASE_COLUMNS
        )

    description_lookup = (
        _mapping_description_lookup(
            mapping
        )
    )

    priority_lookup = (
        _build_ai_priority_lookup(
            ai_priorities
        )
    )

    pattern_lookup = (
        _build_pattern_lookup(
            ai_patterns
        )
    )

    assignment_ai_lookup = (
        _build_assignment_ai_lookup(
            ai_assignment_analysis
        )
    )

    records: list[
        dict[str, object]
    ] = []

    for _, row in final_report.iterrows():

        final_verdict = str(
            row[
                "verdict"
            ]
        )

        ui_verdict = (
            FINAL_TO_UI_VERDICT.get(
                final_verdict,
                "Needs review",
            )
        )

        final_priority = str(
            row.get(
                "priority",
                "FAIBLE",
            )
        )

        ui_priority = (
            FINAL_TO_UI_PRIORITY.get(
                final_priority,
                "Low",
            )
        )

        employee_id = _value(
            row.get(
                "employee_id"
            )
        )

        employee_key = (
            str(
                employee_id
            )
            if employee_id
            is not None
            else
            ""
        )

        mapping_row = _value(
            row.get(
                "mapping_row"
            )
        )

        description = None

        if mapping_row is not None:

            try:
                description = (
                    description_lookup.get(
                        int(
                            mapping_row
                        )
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

        if not description:

            description = (
                _value(
                    row.get(
                        "rule_name"
                    )
                )
            )

        if not description:

            if (
                row.get(
                    "comparison_layer"
                )
                ==
                "STRUCTURAL"
            ):
                description = (
                    "Employee or assignment matching"
                )
            else:
                description = (
                    str(
                        row.get(
                            "field",
                            "",
                        )
                    )
                )

        # ====================================================
        # DEFAULT AI VALUES
        # ====================================================

        ai_contributed = False
        ai_status = (
            "not configured"
        )
        ai_score = None

        # ====================================================
        # EMPLOYEE-LEVEL AI PRIORITIZATION
        # ====================================================

        employee_ai = (
            priority_lookup.get(
                employee_key
            )
        )

        if (
            employee_ai
            is not None
            and
            final_verdict
            ==
            "ANOMALIE"
        ):

            ai_contributed = True

            ai_score = (
                employee_ai.get(
                    "score"
                )
            )

            ai_status = (
                "Local AI prioritization: "
                f"score={employee_ai.get('score')}; "
                f"priority={employee_ai.get('priority')}. "
                f"{employee_ai.get('explanation')}"
            )

        # ====================================================
        # AMBIGUOUS ASSIGNMENT AI
        # ====================================================

        if (
            row.get(
                "comparison_type"
            )
            ==
            "AMBIGUOUS_ASSIGNMENT_MATCH"
        ):

            assignment_ai = (
                assignment_ai_lookup.get(
                    employee_key
                )
            )

            if assignment_ai:

                ai_contributed = True

                ai_score = (
                    assignment_ai.get(
                        "score"
                    )
                )

                pair_text = "; ".join(
                    (
                        f"source {pair['source_row']} "
                        f"→ destination {pair['destination_row']} "
                        f"(score {pair['pair_match_score']:.3f})"
                    )
                    for pair
                    in assignment_ai.get(
                        "pairs",
                        [],
                    )
                )

                ai_status = (
                    f"{assignment_ai.get('status')}. "
                    f"Suggested matching: {pair_text}. "
                    f"Matching confidence="
                    f"{assignment_ai.get('confidence')}."
                )

        # ====================================================
        # PATTERN ANALYSIS
        # ====================================================

        pattern_key = (
            str(
                row.get(
                    "field"
                )
            ),
            final_verdict,
        )

        pattern = (
            pattern_lookup.get(
                pattern_key
            )
        )

        pattern_type = None

        if pattern:

            pattern_type = (
                pattern.get(
                    "pattern_type"
                )
            )

        # ====================================================
        # SUPPORTING EVIDENCE
        # ====================================================

        supporting = {
            "comparison_layer":
                _value(
                    row.get(
                        "comparison_layer"
                    )
                ),

            "comparison_type":
                _value(
                    row.get(
                        "comparison_type"
                    )
                ),

            "decision_source":
                _value(
                    row.get(
                        "decision_source"
                    )
                ),

            "mapping_row":
                mapping_row,

            "rule_inputs":
                _value(
                    row.get(
                        "rule_inputs"
                    )
                ),

            "limitation_code":
                _value(
                    row.get(
                        "limitation_code"
                    )
                ),

            "deterministic_confidence":
                _value(
                    row.get(
                        "confidence"
                    )
                ),
        }

        if pattern:

            supporting[
                "pattern_analysis"
            ] = pattern

        # ====================================================
        # RECORD
        # ====================================================

        record = {
            "record_identifier":
                employee_id,

            "assignment_type":
                _value(
                    row.get(
                        "assignment_type"
                    )
                ),

            "source_row":
                _value(
                    row.get(
                        "source_row_index"
                    )
                ),

            "destination_row":
                _value(
                    row.get(
                        "destination_row_index"
                    )
                ),

            "mapping_row":
                mapping_row,

            "field":
                _value(
                    row.get(
                        "field"
                    )
                ),

            "description":
                description,

            "source_value":
                _value(
                    row.get(
                        "source_raw_value"
                    )
                ),

            "source_normalized_value":
                _value(
                    row.get(
                        "source_normalized_value"
                    )
                ),

            "destination_value":
                _value(
                    row.get(
                        "destination_raw_value"
                    )
                ),

            "destination_normalized_value":
                _value(
                    row.get(
                        "destination_normalized_value"
                    )
                ),

            "expected_value":
                _value(
                    row.get(
                        "expected_value"
                    )
                ),

            "verdict":
                ui_verdict,

            "rule_ids":
                (
                    _value(
                        row.get(
                            "rule_id"
                        )
                    )
                    or
                    ""
                ),

            "decision_method":
                _decision_method(
                    row
                ),

            "priority":
                ui_priority,

            "priority_reason":
                _priority_reason(
                    row
                ),

            "confidence":
                _value(
                    row.get(
                        "confidence"
                    )
                ),

            "limitation_code":
                _value(
                    row.get(
                        "limitation_code"
                    )
                ),

            "explanation":
                _value(
                    row.get(
                        "explanation"
                    )
                ),

            "supporting_records":
                _json(
                    supporting
                ),

            "ai_contributed":
                ai_contributed,

            "ai_status":
                ai_status,

            "ai_score":
                ai_score,

            "pattern_type":
                pattern_type,
        }

        record[
            "case_id"
        ] = _case_id(
            record
        )

        records.append(
            record
        )

    result = pd.DataFrame(
        records
    )

    # ========================================================
    # ENSURE ALL REQUIRED COLUMNS EXIST
    # ========================================================

    for column in CASE_COLUMNS:

        if column not in result.columns:
            result[
                column
            ] = None

    # ========================================================
    # REVIEW-FRIENDLY SORT
    # ========================================================

    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    verdict_order = {
        "Actual anomaly": 0,
        "Needs review": 1,
        "Justified difference": 2,
        "Match": 3,
    }

    result[
        "_priority_order"
    ] = result[
        "priority"
    ].map(
        priority_order
    )

    result[
        "_verdict_order"
    ] = result[
        "verdict"
    ].map(
        verdict_order
    )

    result = (
        result
        .sort_values(
            by=[
                "_priority_order",
                "_verdict_order",
                "record_identifier",
                "field",
            ],
            na_position="last",
        )
        .drop(
            columns=[
                "_priority_order",
                "_verdict_order",
            ]
        )
        .loc[
            :,
            CASE_COLUMNS,
        ]
        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# INPUT HASHING / AUDIT
# ============================================================

def _input_bytes(
    value: InputValue,
) -> bytes:
    """Read bytes without permanently moving stream position."""

    if isinstance(
        value,
        Path,
    ):
        return value.read_bytes()

    if hasattr(
        value,
        "getvalue",
    ):
        return value.getvalue()  # type: ignore[union-attr]

    position = None

    try:
        position = value.tell()
    except Exception:
        pass

    try:
        value.seek(0)
    except Exception:
        pass

    contents = value.read()

    if isinstance(
        contents,
        str,
    ):
        contents = contents.encode(
            "utf-8"
        )

    if (
        position
        is not None
    ):
        try:
            value.seek(
                position
            )
        except Exception:
            pass

    return contents


def _digest(
    value: InputValue,
) -> str:

    return sha256(
        _input_bytes(
            value
        )
    ).hexdigest()


def _audit(
    inputs: InputPaths,
    final_report: pd.DataFrame,
    ai_queue: pd.DataFrame,
    ai_assignment_analysis: pd.DataFrame,
    ai_priorities: pd.DataFrame,
    ai_patterns: pd.DataFrame,
) -> dict[str, object]:
    """Create reproducibility and governance metadata."""

    verdict_counts = (
        final_report[
            "verdict"
        ]
        .value_counts()
        .to_dict()
    )

    return {
        "run_at_utc":
            datetime.now(
                UTC
            ).isoformat(),

        "source_files_read_only":
            True,

        "rule_version":
            (
                "Mapping.xlsx + deterministic catalogue "
                "+ final-report policy v2"
            ),

        "ai_configuration":
            (
                "Local scikit-learn only. "
                "RandomForestClassifier assists ambiguous "
                "assignment matching; IsolationForest assists "
                "anomaly prioritization. No external AI "
                "provider receives challenge data."
            ),

        "ai_external_data_transfer":
            False,

        "ai_random_state":
            42,

        "report_row_count":
            int(
                len(
                    final_report
                )
            ),

        "verdict_counts":
            {
                str(
                    key
                ):
                    int(
                        value
                    )
                for (
                    key,
                    value,
                ) in verdict_counts.items()
            },

        "ai_queue_rows":
            int(
                len(
                    ai_queue
                )
            ),

        "ai_assignment_candidate_rows":
            int(
                len(
                    ai_assignment_analysis
                )
            ),

        "ai_priority_rows":
            int(
                len(
                    ai_priorities
                )
            ),

        "ai_pattern_rows":
            int(
                len(
                    ai_patterns
                )
            ),

        "input_sha256":
            {
                "source":
                    _digest(
                        inputs.source
                    ),

                "destination":
                    _digest(
                        inputs.destination
                    ),

                "mapping":
                    _digest(
                        inputs.mapping
                    ),

                "job_details":
                    _digest(
                        inputs.job_details
                    ),

                "employment_reasons":
                    _digest(
                        inputs.employment_reasons
                    ),
            },
    }


# ============================================================
# SANITY VALIDATION
# ============================================================

def _validate_verified_baseline(
    final_report: pd.DataFrame,
) -> None:
    """Check internal consistency without hard-coding dataset answers."""

    if final_report.empty:
        raise InputValidationError(
            [
                "The reconciliation produced no report rows."
            ]
        )

    allowed = {
        "CONFORME",
        "ECART_JUSTIFIE",
        "ANOMALIE",
        "A_INVESTIGUER",
    }

    observed = set(
        final_report[
            "verdict"
        ].dropna()
    )

    unexpected = (
        observed
        -
        allowed
    )

    if unexpected:
        raise InputValidationError(
            [
                (
                    "Unexpected final verdict(s): "
                    +
                    ", ".join(
                        sorted(
                            unexpected
                        )
                    )
                )
            ]
        )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_reconciliation(
    inputs: InputPaths,
) -> ReconciliationRun:
    """Run the complete CorroborIA hybrid reconciliation workflow."""

    # ========================================================
    # 1. LOAD ORIGINAL INPUTS
    # ========================================================

    source_raw = (
        _read_table(
            inputs.source
        )
    )

    destination_raw = (
        _read_table(
            inputs.destination
        )
    )

    mapping_book = (
        _read_workbook(
            inputs.mapping
        )
    )

    job_raw = (
        _repair_job_details(
            _read_single_input(
                inputs.job_details,
                "Job details",
            )
        )
    )

    reasons_raw = (
        _read_single_input(
            inputs.employment_reasons,
            "Employment reasons",
        )
    )

    # ========================================================
    # 2. LOAD AUTHORITY SHEETS BY NAME
    # ========================================================

    mapping_raw = (
        _mapping_sheet(
            mapping_book,
            "Mapping",
        )
    )

    employment_rules_raw = (
        _mapping_sheet(
            mapping_book,
            "Règles situation d'emploi",
        )
    )

    # Validate that supporting join-definition sheets exist,
    # even though the actual join logic is implemented inside
    # our deterministic rule engine.
    _mapping_sheet(
        mapping_book,
        "Jointure - Détail du poste",
    )

    _mapping_sheet(
        mapping_book,
        "Jointure - Motif des situations",
    )

    # ========================================================
    # 3. REQUIRED INPUT VALIDATION
    # ========================================================

    issues: list[
        str
    ] = []

    issues.extend(
        _required_columns(
            source_raw,
            "System A",
            {
                "Matricule",
                "TypeAffectation",
            },
        )
    )

    issues.extend(
        _required_columns(
            destination_raw,
            "System B",
            {
                "personId",
                "isPrimaryAssignment",
                "isTemporaryAssignment",
            },
        )
    )

    issues.extend(
        _required_columns(
            job_raw,
            "Job details",
            {
                "IdentifiantPoste",
                "IdentifiantEmploi",
                "CodeDirectionAffectée",
                "DateEffetAffectation",
            },
        )
    )

    issues.extend(
        _required_columns(
            reasons_raw,
            "Employment reasons",
            {
                "CodeCatégorieStatut",
                "CodeStatutSystèmeExterne",
                "CodeGestionAccès",
            },
        )
    )

    if issues:
        raise InputValidationError(
            issues
        )

    # ========================================================
    # 4. NORMALIZE WORKING COPIES
    # ========================================================

    source = (
        _normalise_source(
            source_raw
        )
    )

    destination = (
        _normalise_destination(
            destination_raw
        )
    )

    job_details = (
        _normalise_job_details(
            job_raw
        )
    )

    employment_reasons = (
        _normalise_employment_reasons(
            reasons_raw
        )
    )

    # ========================================================
    # 5. PARSE MAPPING / BUSINESS RULE TABLE
    # ========================================================

    mapping = (
        parse_mapping_sheet(
            mapping_raw
        )
    )

    employment_rules = (
        parse_employment_rules(
            employment_rules_raw
        )
    )

    # ========================================================
    # 6. VALIDATE DIRECT MAPPINGS
    # ========================================================

    mapping_issues = (
        validate_direct_mappings(
            parsed_mapping_df=
                mapping,

            source_df=
                source,

            destination_df=
                destination,
        )
    )

    if not mapping_issues.empty:

        problems = []

        for row in mapping_issues.itertuples():

            problems.append(
                (
                    f"Mapping row {row.mapping_row}: "
                    f"{row.problem} ({row.field})."
                )
            )

        raise InputValidationError(
            problems
        )

    # ========================================================
    # 7. EMPLOYEE MATCHING
    # ========================================================

    (
        source_missing_ids,
        destination_missing_ids,
    ) = find_missing_employee_ids(
        source_df=
            source,

        destination_df=
            destination,
    )

    employee_matches = (
        match_employees(
            source_df=
                source,

            destination_df=
                destination,
        )
    )

    # ========================================================
    # 8. ASSIGNMENT MATCHING
    # ========================================================

    assignment_matches = (
        match_assignments(
            source_df=
                source,

            destination_df=
                destination,

            employee_matches_df=
                employee_matches,
        )
    )

    # ========================================================
    # 9. DIRECT COMPARISONS
    # ========================================================

    direct_results = (
        compare_direct_mappings(
            raw_source_df=
                source_raw,

            raw_destination_df=
                destination_raw,

            source_df=
                source,

            destination_df=
                destination,

            parsed_mapping_df=
                mapping,

            assignment_matches_df=
                assignment_matches,
        )
    )

    # ========================================================
    # 10. DETERMINISTIC BUSINESS RULES
    # ========================================================

    rule_results = (
        evaluate_rule_based_fields(
            raw_destination_df=
                destination_raw,

            source_df=
                source,

            destination_df=
                destination,

            job_details_df=
                job_details,

            employment_reasons_df=
                employment_reasons,

            employment_rules_df=
                employment_rules,

            assignment_matches_df=
                assignment_matches,
        )
    )

    # ========================================================
    # 11. VERIFIED UNIFIED FINAL REPORT
    # ========================================================

    final_report = (
        build_final_report(
            comparison_df=
                direct_results,

            rule_results_df=
                rule_results,

            assignment_matches_df=
                assignment_matches,
        )
    )

    _validate_verified_baseline(
        final_report
    )

    # ========================================================
    # 12. INVESTIGATION VIEW
    # ========================================================

    investigation_report = (
        build_investigation_report(
            final_report_df=
                final_report,
        )
    )

    # ========================================================
    # 13. TRUE AI QUEUE
    # ========================================================

    ai_queue = (
        build_ai_queue(
            final_report_df=
                final_report,
        )
    )

    # ========================================================
    # 14. AI AMBIGUOUS ASSIGNMENT ANALYSIS
    # ========================================================

    ai_assignment_analysis = (
        analyze_ambiguous_assignments(
            source_df=
                source,

            destination_df=
                destination,

            assignment_matches_df=
                assignment_matches,
        )
    )

    # ========================================================
    # 15. AI ANOMALY PRIORITIZATION
    # ========================================================

    ai_priorities = (
        prioritize_anomalies(
            final_report_df=
                final_report,
        )
    )

    # ========================================================
    # 16. PATTERN ANALYSIS
    # ========================================================

    ai_patterns = (
        summarize_anomaly_patterns(
            final_report_df=
                final_report,
        )
    )

    # ========================================================
    # 17. CONVERT TO STREAMLIT REVIEW CASES
    # ========================================================

    cases = (
        _cases_from_final_report(
            final_report=
                final_report,

            mapping=
                mapping,

            ai_assignment_analysis=
                ai_assignment_analysis,

            ai_priorities=
                ai_priorities,

            ai_patterns=
                ai_patterns,
        )
    )

    # ========================================================
    # 18. FINAL SANITY CHECK
    # ========================================================

    if len(
        cases
    ) != len(
        final_report
    ):

        raise InputValidationError(
            [
                (
                    "Internal report conversion error: "
                    f"{len(final_report)} technical rows became "
                    f"{len(cases)} reviewer cases."
                )
            ]
        )

    # ========================================================
    # 19. AUDIT TRAIL
    # ========================================================

    audit = (
        _audit(
            inputs=
                inputs,

            final_report=
                final_report,

            ai_queue=
                ai_queue,

            ai_assignment_analysis=
                ai_assignment_analysis,

            ai_priorities=
                ai_priorities,

            ai_patterns=
                ai_patterns,
        )
    )

    # Include missing-ID counts in audit rather than silently
    # discarding those validation results.
    audit[
        "missing_employee_ids"
    ] = {
        "system_a":
            int(
                len(
                    source_missing_ids
                )
            ),

        "system_b":
            int(
                len(
                    destination_missing_ids
                )
            ),
    }

    # ========================================================
    # 20. RETURN COMPLETE RUN
    # ========================================================

    return ReconciliationRun(
        cases=
            cases,

        mapping=
            mapping,

        employee_matches=
            employee_matches,

        assignment_matches=
            assignment_matches,

        validation_issues=
            mapping_issues,

        audit=
            audit,

        final_report=
            final_report,

        investigation_report=
            investigation_report,

        ai_queue=
            ai_queue,

        ai_assignment_analysis=
            ai_assignment_analysis,

        ai_priorities=
            ai_priorities,

        ai_patterns=
            ai_patterns,
    )
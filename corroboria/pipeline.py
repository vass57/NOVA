"""Auditable reconciliation pipeline for the CorroborIA challenge.

The pipeline deliberately separates loading, representation normalisation,
matching, deterministic decisions, and presentation/export concerns.  It never
writes to an input file and it only evaluates fields present in Mapping.xlsx.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from corroboria.assignment_matcher import match_assignments
from corroboria.business_rules import evaluate_rule_based_fields
from corroboria.comparator import compare_direct_mappings
from corroboria.mapping_parser import (
    parse_employment_rules,
    parse_mapping_sheet,
    validate_direct_mappings,
)
from corroboria.matcher import find_missing_employee_ids, match_employees
from corroboria.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_identifier,
    normalize_number,
    normalize_text,
)


InputValue = Path | BinaryIO

VERDICTS = {
    "Match",
    "Justified difference",
    "Actual anomaly",
    "Needs review",
}

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
    "explanation",
    "supporting_records",
    "ai_contributed",
    "ai_status",
]


class InputValidationError(ValueError):
    """Raised when an input cannot support a reliable reconciliation."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))


@dataclass(frozen=True)
class InputPaths:
    """The five approved challenge inputs required for one run."""

    source: InputValue
    destination: InputValue
    mapping: InputValue
    job_details: InputValue
    employment_reasons: InputValue

    @classmethod
    def from_data_directory(cls, data_directory: Path) -> "InputPaths":
        """Locate the supplied challenge files without relying on CWD."""

        def one(pattern: str) -> Path:
            matches = sorted(data_directory.glob(pattern))
            if len(matches) != 1:
                raise InputValidationError(
                    [
                        f"Expected exactly one '{pattern}' file in "
                        f"{data_directory}; found {len(matches)}."
                    ]
                )
            return matches[0]

        return cls(
            source=one("Employe_Source_*.xlsx"),
            destination=one("Employe_Destination_*.xlsx"),
            mapping=one("Mapping.xlsx"),
            job_details=one("d*tail_du_poste.xlsx"),
            employment_reasons=one("Motif de la situation d'emploi.xlsx"),
        )


@dataclass
class ReconciliationRun:
    """A complete, reproducible result of one reconciliation."""

    cases: pd.DataFrame
    mapping: pd.DataFrame
    employee_matches: pd.DataFrame
    assignment_matches: pd.DataFrame
    validation_issues: pd.DataFrame
    audit: dict[str, object]

    @property
    def summary(self) -> pd.DataFrame:
        """Return verdict counts measured in field comparisons/cases."""

        counts = (
            self.cases["verdict"]
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
            .rename_axis("verdict")
            .reset_index(name="field_comparisons_or_cases")
        )
        return counts


def _read_table(value: InputValue) -> pd.DataFrame:
    """Load CSV or Excel data while preserving source values as objects."""

    name = getattr(value, "name", str(value)).lower()
    if name.endswith(".csv"):
        return pd.read_csv(value, dtype=object)
    return pd.read_excel(value, dtype=object, engine="openpyxl")


def _read_workbook(value: InputValue) -> dict[str, pd.DataFrame]:
    """Load every Excel worksheet. Mapping workbooks must be Excel files."""

    name = getattr(value, "name", str(value)).lower()
    if name.endswith(".csv"):
        raise InputValidationError(["Mapping and lookup inputs must be Excel workbooks."])
    return pd.read_excel(value, sheet_name=None, dtype=object, engine="openpyxl")


def _only_sheet(workbook: dict[str, pd.DataFrame], label: str) -> pd.DataFrame:
    if len(workbook) != 1:
        raise InputValidationError(
            [f"{label} must contain exactly one worksheet; found {len(workbook)}."]
        )
    return next(iter(workbook.values())).copy()


def _read_single_input(value: InputValue, label: str) -> pd.DataFrame:
    """Load a one-table supplementary input from CSV or one-sheet Excel."""

    name = getattr(value, "name", str(value)).lower()
    if name.endswith(".csv"):
        return _read_table(value)
    return _only_sheet(_read_workbook(value), label)


def _repair_job_details(frame: pd.DataFrame) -> pd.DataFrame:
    """Parse the supplied one-column CSV payload embedded in an Excel sheet."""

    if len(frame.columns) != 1:
        return frame.copy()

    header = str(frame.columns[0])
    if "," not in header:
        return frame.copy()

    csv_text = "\n".join([header, *frame.iloc[:, 0].fillna("").astype(str)])
    return pd.read_csv(StringIO(csv_text), dtype=object)


def _normalise(frame: pd.DataFrame, columns: dict[str, object]) -> pd.DataFrame:
    result = frame.copy()
    for column, function in columns.items():
        if column in result.columns:
            result[column] = result[column].map(function)
    return result


def _normalise_source(frame: pd.DataFrame) -> pd.DataFrame:
    identifier = normalize_identifier
    return _normalise(
        frame,
        {
            "Matricule": identifier,
            "CodePoste": identifier,
            "CodeEmploi": identifier,
            "\u00c9chelleSalariale": identifier,
            "CodeImputation": identifier,
            "CodeDirection": identifier,
            "CodeSite": identifier,
            "Cat\u00e9gorieEmploi": identifier,
            "CodeStatutEmploi": identifier,
            "CodeRaisonStatut": identifier,
            "CodeSuspensionAcc\u00e8s": identifier,
            "IdentifiantResponsable": identifier,
            "CodeQuart": identifier,
            "NomFamille": normalize_text,
            "Pr\u00e9nomUsuel": normalize_text,
            "TypeAffectation": normalize_text,
            "Intitul\u00e9Poste": normalize_text,
            "Intitul\u00e9Emploi": normalize_text,
            "Libell\u00e9\u00c9chelleSalariale": normalize_text,
            "Libell\u00e9Imputation": normalize_text,
            "Libell\u00e9Direction": normalize_text,
            "Libell\u00e9Site": normalize_text,
            "Libell\u00e9RaisonStatut": normalize_text,
            "NomResponsable": normalize_text,
            "DateEmbaucheR\u00e9cente": normalize_date,
            "DateEntr\u00e9ePoste": normalize_date,
            "DateSortiePoste": normalize_date,
            "DateEffetRaison": normalize_date,
            "DateRetourAnticip\u00e9e": normalize_date,
            "EstPermanent": normalize_boolean,
            "EstTempsPlein": normalize_boolean,
            "HeuresNormeHebdo": normalize_number,
            "HeuresNormeQuotidienne": normalize_number,
        },
    )


def _normalise_destination(frame: pd.DataFrame) -> pd.DataFrame:
    identifier = normalize_identifier
    return _normalise(
        frame,
        {
            "personId": identifier,
            "statusReasonCode": identifier,
            "siteId": identifier,
            "siteCode": identifier,
            "divisionId": identifier,
            "divisionCode": identifier,
            "positionId": identifier,
            "positionCode": identifier,
            "payGradeId": identifier,
            "externalReferenceId": identifier,
            "givenName": normalize_text,
            "surname": normalize_text,
            "contactEmail": normalize_text,
            "activityStatus": normalize_text,
            "contractTypeCode": normalize_text,
            "detailedStatus": normalize_text,
            "siteName": normalize_text,
            "divisionName": normalize_text,
            "positionName": normalize_text,
            "onboardDate": normalize_date,
            "expectedReturnDate": normalize_date,
            "assignmentStartDate": normalize_date,
            "assignmentEndDate": normalize_date,
            "termStartDate": normalize_date,
            "termEndDate": normalize_date,
            "isPrimaryAssignment": normalize_boolean,
            "isTemporaryAssignment": normalize_boolean,
            "wageOverrideAmount": normalize_number,
            "wageMultiplierFactor": normalize_number,
            "weeklyHoursOverride": normalize_number,
            "dailyHoursOverride": normalize_number,
        },
    )


def _normalise_job_details(frame: pd.DataFrame) -> pd.DataFrame:
    identifier = normalize_identifier
    return _normalise(
        frame,
        {
            "IdentifiantPoste": identifier,
            "IdentifiantEmploi": identifier,
            "CodeDirectionAffect\u00e9e": identifier,
            "CodeBudget": identifier,
            "IndicateurGestion": identifier,
            "CodePosteSecondaire": identifier,
            "MatriculeGestionnaire": identifier,
            "DateEffetAffectation": normalize_date,
            "HeuresSemaineContrat": normalize_number,
            "HeuresJourContrat": normalize_number,
            "JoursTravaill\u00e9esSemaine": normalize_number,
        },
    )


def _normalise_employment_reasons(frame: pd.DataFrame) -> pd.DataFrame:
    identifier = normalize_identifier
    return _normalise(
        frame,
        {
            "CodeCat\u00e9gorieStatut": identifier,
            "CodeStatutSyst\u00e8meExterne": identifier,
            "CodeGestionAcc\u00e8s": identifier,
        },
    )


def _required_columns(frame: pd.DataFrame, name: str, columns: set[str]) -> list[str]:
    missing = sorted(columns.difference(frame.columns))
    if not missing:
        return []
    return [f"{name} is missing required column(s): {', '.join(missing)}."]


def _value(value: object) -> object:
    """Make nullable pandas values safe for exports and case ids."""

    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)


def _case_id(record: dict[str, object]) -> str:
    identity = "|".join(
        str(record.get(key, ""))
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
    return f"CASE-{sha256(identity.encode()).hexdigest()[:12].upper()}"


def _priority(verdict: str, field: str, repeated: int) -> tuple[str, str]:
    if verdict == "Actual anomaly":
        if repeated >= 3:
            return "High", f"Deterministic anomaly repeated in {repeated} cases for {field}."
        return "High", "Deterministic expected value does not match the destination value."
    if verdict == "Needs review":
        return "Medium", "Matching or supporting evidence is incomplete or ambiguous."
    if verdict == "Justified difference":
        return "Low", "A deterministic mapping rule explains the destination value."
    return "Low", "Mapped values agree under the approved comparison logic."


def _case_from_direct(row: pd.Series) -> dict[str, object]:
    verdict = "Match" if row["verdict"] == "CONFORME" else "Actual anomaly"
    return {
        "record_identifier": row["employee_id"],
        "assignment_type": row["assignment_type"],
        "source_row": row["source_row_index"],
        "destination_row": row["destination_row_index"],
        "mapping_row": row["mapping_row"],
        "field": row["destination_field"],
        "description": row["description"],
        "source_value": _value(row["source_raw_value"]),
        "source_normalized_value": _value(row["source_normalized_value"]),
        "destination_value": _value(row["destination_raw_value"]),
        "destination_normalized_value": _value(row["destination_normalized_value"]),
        "expected_value": _value(row["source_normalized_value"]),
        "verdict": verdict,
        "rule_ids": "",
        "decision_method": "direct comparison",
        "explanation": row["explanation"],
        "supporting_records": _json({"mapping_row": row["mapping_row"]}),
        "ai_contributed": False,
        "ai_status": "not configured",
    }


def _case_from_rule(row: pd.Series) -> dict[str, object]:
    if row["verdict"] == "CONFORME":
        verdict = "Justified difference"
    elif row["verdict"] == "ANOMALIE":
        verdict = "Actual anomaly"
    else:
        verdict = "Needs review"
    return {
        "record_identifier": row["employee_id"],
        "assignment_type": row["assignment_type"],
        "source_row": row["source_row_index"],
        "destination_row": row["destination_row_index"],
        "mapping_row": row["mapping_row"],
        "field": row["destination_field"],
        "description": row["rule_name"],
        "source_value": _json(row["source_inputs"]),
        "source_normalized_value": _json(row["source_inputs"]),
        "destination_value": _value(row["destination_raw_value"]),
        "destination_normalized_value": _value(row["destination_normalized_value"]),
        "expected_value": _value(row["expected_value"]),
        "verdict": verdict,
        "rule_ids": row["rule_id"],
        "decision_method": "deterministic business rule",
        "explanation": row["explanation"],
        "supporting_records": _json(row["source_inputs"]),
        "ai_contributed": False,
        "ai_status": "not configured",
    }


def _structural_cases(
    employee_matches: pd.DataFrame,
    assignment_matches: pd.DataFrame,
    source_missing_ids: pd.DataFrame,
    destination_missing_ids: pd.DataFrame,
) -> list[dict[str, object]]:
    """Turn unmatched or ambiguous input relationships into review cases."""

    records: list[dict[str, object]] = []

    def add(
        *,
        identifier: object,
        assignment_type: object,
        source_row: object,
        destination_row: object,
        method: str,
        explanation: str,
        evidence: object,
    ) -> None:
        records.append(
            {
                "record_identifier": identifier,
                "assignment_type": assignment_type,
                "source_row": source_row,
                "destination_row": destination_row,
                "mapping_row": None,
                "field": "record matching",
                "description": "Employee or assignment matching",
                "source_value": None,
                "source_normalized_value": None,
                "destination_value": None,
                "destination_normalized_value": None,
                "expected_value": None,
                "verdict": "Needs review",
                "rule_ids": "",
                "decision_method": method,
                "explanation": explanation,
                "supporting_records": _json(evidence),
                "ai_contributed": False,
                "ai_status": "not configured",
            }
        )

    for _, row in employee_matches.loc[
        employee_matches["employee_match_status"] != "BOTH"
    ].iterrows():
        add(
            identifier=row["employee_id"],
            assignment_type=None,
            source_row=None,
            destination_row=None,
            method="employee matching",
            explanation=(
                "Employee is present in only one system; no cross-system record "
                "can be compared safely."
            ),
            evidence={
                "employee_match_status": row["employee_match_status"],
                "source_rows": row["source_row_indices"],
                "destination_rows": row["destination_row_indices"],
            },
        )

    for _, row in assignment_matches.loc[
        assignment_matches["assignment_match_status"] != "MATCHED"
    ].iterrows():
        add(
            identifier=row["employee_id"],
            assignment_type=row["assignment_type"],
            source_row=row["source_row_index"],
            destination_row=row["destination_row_index"],
            method="assignment matching",
            explanation=row["explanation"],
            evidence={
                "assignment_match_status": row["assignment_match_status"],
                "source_candidates": row["source_candidate_indices"],
                "destination_candidates": row["destination_candidate_indices"],
            },
        )

    for index in source_missing_ids.index:
        add(
            identifier=None,
            assignment_type=None,
            source_row=index,
            destination_row=None,
            method="input validation",
            explanation="System A row has no Matricule and cannot be matched.",
            evidence={"system": "System A", "row": int(index), "missing_field": "Matricule"},
        )
    for index in destination_missing_ids.index:
        add(
            identifier=None,
            assignment_type=None,
            source_row=None,
            destination_row=index,
            method="input validation",
            explanation="System B row has no personId and cannot be matched.",
            evidence={"system": "System B", "row": int(index), "missing_field": "personId"},
        )
    return records


def _finalise_cases(records: list[dict[str, object]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=CASE_COLUMNS)

    result = pd.DataFrame(records)
    repeats = result.groupby("field")["field"].transform("size")
    priorities = [
        _priority(verdict, field, int(repeated))
        for verdict, field, repeated in zip(result["verdict"], result["field"], repeats)
    ]
    result[["priority", "priority_reason"]] = pd.DataFrame(priorities, index=result.index)
    result.insert(0, "case_id", result.apply(_case_id, axis=1))
    return result.loc[:, CASE_COLUMNS].sort_values(
        ["priority", "verdict", "record_identifier", "field"],
        key=lambda column: column.map({"High": 0, "Medium": 1, "Low": 2})
        if column.name == "priority"
        else column,
        na_position="last",
    ).reset_index(drop=True)


def _remap_rule_references(
    rule_results: pd.DataFrame, mapping: pd.DataFrame
) -> pd.DataFrame:
    """Use Mapping.xlsx row numbers in output instead of implementation constants."""

    result = rule_results.copy()
    for index, row in result.iterrows():
        field = row["destination_field"]
        candidates = mapping.loc[mapping["destination_field"].eq(field), "mapping_row"]
        if candidates.empty and field in {"isPrimaryAssignment", "isTemporaryAssignment"}:
            candidates = mapping.loc[
                mapping["destination_field"].fillna("").str.contains("isPrimaryAssignment"),
                "mapping_row",
            ]
        if not candidates.empty:
            result.at[index, "mapping_row"] = int(candidates.iloc[0])
    return result


def _audit(inputs: InputPaths) -> dict[str, object]:
    def digest(value: InputValue) -> str:
        if isinstance(value, Path):
            return sha256(value.read_bytes()).hexdigest()
        if hasattr(value, "getvalue"):
            return sha256(value.getvalue()).hexdigest()  # type: ignore[union-attr]
        position = value.tell()
        value.seek(0)
        contents = value.read()
        value.seek(position)
        return sha256(contents).hexdigest()

    return {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "rule_version": "Mapping.xlsx + deterministic catalogue v1",
        "ai_configuration": "disabled; no data sent to an external provider",
        "input_sha256": {
            "source": digest(inputs.source),
            "destination": digest(inputs.destination),
            "mapping": digest(inputs.mapping),
            "job_details": digest(inputs.job_details),
            "employment_reasons": digest(inputs.employment_reasons),
        },
    }


def run_reconciliation(inputs: InputPaths) -> ReconciliationRun:
    """Run the approved deterministic workflow and return review-ready cases."""

    source_raw = _read_table(inputs.source)
    destination_raw = _read_table(inputs.destination)
    mapping_book = _read_workbook(inputs.mapping)

    mapping_sheets = list(mapping_book.values())
    if len(mapping_sheets) < 4:
        raise InputValidationError(["Mapping.xlsx must contain four authority worksheets."])

    job_raw = _repair_job_details(_read_single_input(inputs.job_details, "Job details"))
    reasons_raw = _read_single_input(inputs.employment_reasons, "Employment reasons")
    mapping = parse_mapping_sheet(mapping_sheets[0])
    employment_rules = parse_employment_rules(mapping_sheets[1])

    issues = []
    issues.extend(_required_columns(source_raw, "System A", {"Matricule", "TypeAffectation"}))
    issues.extend(
        _required_columns(
            destination_raw,
            "System B",
            {"personId", "isPrimaryAssignment", "isTemporaryAssignment"},
        )
    )
    issues.extend(
        _required_columns(
            job_raw,
            "Job details",
            {
                "IdentifiantPoste",
                "IdentifiantEmploi",
                "CodeDirectionAffect\u00e9e",
                "DateEffetAffectation",
            },
        )
    )
    issues.extend(
        _required_columns(
            reasons_raw,
            "Employment reasons",
            {
                "CodeCat\u00e9gorieStatut",
                "CodeStatutSyst\u00e8meExterne",
                "CodeGestionAcc\u00e8s",
            },
        )
    )
    if issues:
        raise InputValidationError(issues)

    source = _normalise_source(source_raw)
    destination = _normalise_destination(destination_raw)
    job_details = _normalise_job_details(job_raw)
    employment_reasons = _normalise_employment_reasons(reasons_raw)

    mapping_issues = validate_direct_mappings(mapping, source, destination)
    if not mapping_issues.empty:
        problems = [
            f"Mapping row {row.mapping_row}: {row.problem} ({row.field})."
            for row in mapping_issues.itertuples()
        ]
        raise InputValidationError(problems)

    source_missing_ids, destination_missing_ids = find_missing_employee_ids(source, destination)
    employee_matches = match_employees(source, destination)
    assignment_matches = match_assignments(source, destination, employee_matches)

    direct_results = compare_direct_mappings(
        source_raw,
        destination_raw,
        source,
        destination,
        mapping,
        assignment_matches,
    )
    rule_results = evaluate_rule_based_fields(
        destination_raw,
        source,
        destination,
        job_details,
        employment_reasons,
        employment_rules,
        assignment_matches,
    )
    rule_results = _remap_rule_references(rule_results, mapping)

    records = [
        *(_case_from_direct(row) for _, row in direct_results.iterrows()),
        *(_case_from_rule(row) for _, row in rule_results.iterrows()),
        *_structural_cases(
            employee_matches,
            assignment_matches,
            source_missing_ids,
            destination_missing_ids,
        ),
    ]

    return ReconciliationRun(
        cases=_finalise_cases(records),
        mapping=mapping,
        employee_matches=employee_matches,
        assignment_matches=assignment_matches,
        validation_issues=mapping_issues,
        audit=_audit(inputs),
    )

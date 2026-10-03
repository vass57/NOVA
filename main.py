# ============================================================
# CORROBORIA
# PERSON 1 - DATA + RULE ENGINE
# ============================================================
#
# CURRENT STATUS
#
# STEP 1
#   ✅ Load files
#   ✅ Validate files
#   ✅ Repair malformed job-details workbook
#
# STEP 2
#   ✅ Preserve raw data
#   ✅ Normalize all datasets
#
# STEP 3
#   ✅ Parse mapping
#   ✅ Classify direct / rule-based mappings
#   ✅ Parse supporting rule tables
#   ✅ Validate direct mappings
#   ✅ Print detailed rule instructions
#
# STEP 4
#   ✅ Match employees
#
# STEP 5
#   ✅ Match assignments conservatively
#
# STEP 6
#   ✅ Compare direct mapped fields
#   ✅ Detect exact / normalized / discrepant values
#
# NEXT
#   ⬜ Implement deterministic business rules
#   ⬜ Derive expected values
#   ⬜ Apply final deterministic verdicts
#   ⬜ Send ambiguous cases to AI layer
#   ⬜ Generate final report
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
from io import StringIO

import pandas as pd


# ============================================================
# CORROBORIA MODULES
# ============================================================

from corroboria.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_identifier,
    normalize_number,
    normalize_text,
)

from corroboria.mapping_parser import (
    parse_employment_rules,
    parse_join_sheet,
    parse_mapping_sheet,
    preview_mapping_analysis,
    validate_direct_mappings,
)

from corroboria.matcher import (
    find_missing_employee_ids,
    match_employees,
    preview_employee_matching,
)

from corroboria.assignment_matcher import (
    match_assignments,
    preview_assignment_matching,
)

from corroboria.comparator import (
    compare_direct_mappings,
    preview_direct_comparisons,
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"


# ============================================================
# INPUT FILES
# ============================================================

FILES = {

    "source":
        DATA_DIR / "Employe_Source_Anonymise_VF.xlsx",

    "destination":
        DATA_DIR / "Employe_Destination_Anonymise_VF.xlsx",

    "mapping":
        DATA_DIR / "Mapping.xlsx",

    "job_details":
        DATA_DIR / "détail_du_poste.xlsx",

    "employment_reasons":
        DATA_DIR / "Motif de la situation d'emploi.xlsx",
}


# ============================================================
# STEP 1A
# VERIFY REQUIRED FILES
# ============================================================

def check_files_exist() -> None:
    """
    Ensure that every required file exists.
    """

    missing_files = []

    for name, path in FILES.items():

        if not path.exists():

            missing_files.append(
                f"{name}: {path}"
            )

    if missing_files:

        raise FileNotFoundError(
            "The following required files are missing:\n"
            + "\n".join(missing_files)
        )


# ============================================================
# STEP 1B
# LOAD ONE EXCEL WORKBOOK
# ============================================================

def load_excel_file(
    path: Path
) -> dict[str, pd.DataFrame]:
    """
    Load every worksheet from an Excel workbook.
    """

    return pd.read_excel(
        path,
        sheet_name=None,
        dtype=object,
        engine="openpyxl",
    )


# ============================================================
# STEP 1C
# REPAIR DETAIL_DU_POSTE
# ============================================================

def fix_comma_separated_sheet(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Repair job-detail workbook if all CSV data was placed
    inside one Excel column.
    """

    if len(df.columns) != 1:

        return df


    column_name = str(
        df.columns[0]
    )


    if "," not in column_name:

        return df


    rows = [
        column_name
    ]


    for value in df.iloc[:, 0]:

        if pd.isna(value):

            rows.append("")

        else:

            rows.append(
                str(value)
            )


    csv_text = "\n".join(
        rows
    )


    corrected_df = pd.read_csv(
        StringIO(csv_text),
        sep=",",
        dtype=object,
    )


    return corrected_df


# ============================================================
# STEP 1D
# LOAD ALL DATA
# ============================================================

def load_all_data() -> dict[str, dict[str, pd.DataFrame]]:
    """
    Load all challenge workbooks.
    """

    check_files_exist()


    workbooks = {}


    for name, path in FILES.items():

        print(
            f"Loading {name}: {path.name}"
        )


        sheets = load_excel_file(
            path
        )


        # ----------------------------------------------------
        # Special repair for job-detail workbook
        # ----------------------------------------------------

        if name == "job_details":

            for sheet_name, df in sheets.items():

                sheets[sheet_name] = (
                    fix_comma_separated_sheet(
                        df
                    )
                )


        workbooks[name] = sheets


    return workbooks


# ============================================================
# STEP 1E
# INSPECT INPUT FILES
# ============================================================

def inspect_workbooks(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> None:
    """
    Print workbook structures.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - INPUT DATA SUMMARY"
    )

    print(
        "=" * 70
    )


    for workbook_name, sheets in workbooks.items():

        print(
            f"\n[{workbook_name.upper()}]"
        )


        for sheet_name, df in sheets.items():

            print(
                f"\n  Sheet: {sheet_name}"
            )

            print(
                f"  Rows: {len(df)}"
            )

            print(
                f"  Columns: {len(df.columns)}"
            )

            print(
                "  Column names:"
            )


            for column in df.columns:

                print(
                    f"    - {column}"
                )


# ============================================================
# STEP 2A
# EXTRACT REQUIRED DATAFRAMES
# ============================================================

def extract_dataframes(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> dict[str, pd.DataFrame]:
    """
    Extract worksheets required by CorroborIA.
    """

    return {

        "source":
            workbooks[
                "source"
            ][
                "Employe_Source"
            ].copy(),

        "destination":
            workbooks[
                "destination"
            ][
                "Employe_Destination"
            ].copy(),

        "mapping":
            workbooks[
                "mapping"
            ][
                "Mapping"
            ].copy(),

        "employment_rules":
            workbooks[
                "mapping"
            ][
                "Règles situation d'emploi"
            ].copy(),

        "job_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Détail du poste"
            ].copy(),

        "employment_reason_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Motif des situations"
            ].copy(),

        "job_details":
            workbooks[
                "job_details"
            ][
                "Feuil1"
            ].copy(),

        "employment_reasons":
            workbooks[
                "employment_reasons"
            ][
                "Sheet1"
            ].copy(),
    }


# ============================================================
# STEP 2B
# NORMALIZE SYSTEM A
# ============================================================

def normalize_source_data(
    source_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize System A values.
    """

    df = source_df.copy()


    # --------------------------------------------------------
    # IDENTIFIERS
    # --------------------------------------------------------

    identifier_columns = [
        "Matricule",
        "CodePoste",
        "CodeEmploi",
        "ÉchelleSalariale",
        "CodeImputation",
        "CodeDirection",
        "CodeSite",
        "CatégorieEmploi",
        "CodeStatutEmploi",
        "CodeRaisonStatut",
        "CodeSuspensionAccès",
        "IdentifiantResponsable",
        "CodeQuart",
    ]


    for column in identifier_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_identifier
                )
            )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    text_columns = [
        "NomFamille",
        "PrénomUsuel",
        "TypeAffectation",
        "IntituléPoste",
        "IntituléEmploi",
        "LibelléÉchelleSalariale",
        "LibelléImputation",
        "LibelléDirection",
        "LibelléSite",
        "LibelléRaisonStatut",
        "NomResponsable",
    ]


    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_text
                )
            )


    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    date_columns = [
        "DateEmbaucheRécente",
        "DateEntréePoste",
        "DateSortiePoste",
        "DateEffetRaison",
        "DateRetourAnticipée",
    ]


    for column in date_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_date
                )
            )


    # --------------------------------------------------------
    # BOOLEANS
    # --------------------------------------------------------

    boolean_columns = [
        "EstPermanent",
        "EstTempsPlein",
    ]


    for column in boolean_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_boolean
                )
            )


    # --------------------------------------------------------
    # NUMERIC VALUES
    # --------------------------------------------------------

    numeric_columns = [
        "HeuresNormeHebdo",
        "HeuresNormeQuotidienne",
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_number
                )
            )


    return df


# ============================================================
# STEP 2C
# NORMALIZE SYSTEM B
# ============================================================

def normalize_destination_data(
    destination_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize System B values.
    """

    df = destination_df.copy()


    # --------------------------------------------------------
    # IDENTIFIERS
    # --------------------------------------------------------

    identifier_columns = [
        "personId",
        "statusReasonCode",
        "siteId",
        "siteCode",
        "divisionId",
        "divisionCode",
        "positionId",
        "positionCode",
        "payGradeId",
        "externalReferenceId",
    ]


    for column in identifier_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_identifier
                )
            )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    text_columns = [
        "givenName",
        "surname",
        "contactEmail",
        "activityStatus",
        "contractTypeCode",
        "detailedStatus",
        "siteName",
        "divisionName",
        "positionName",
    ]


    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_text
                )
            )


    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    date_columns = [
        "onboardDate",
        "expectedReturnDate",
        "assignmentStartDate",
        "assignmentEndDate",
        "termStartDate",
        "termEndDate",
    ]


    for column in date_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_date
                )
            )


    # --------------------------------------------------------
    # BOOLEANS
    # --------------------------------------------------------

    boolean_columns = [
        "isPrimaryAssignment",
        "isTemporaryAssignment",
    ]


    for column in boolean_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_boolean
                )
            )


    # --------------------------------------------------------
    # NUMERIC VALUES
    # --------------------------------------------------------

    numeric_columns = [
        "wageOverrideAmount",
        "wageMultiplierFactor",
        "weeklyHoursOverride",
        "dailyHoursOverride",
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_number
                )
            )


    return df


# ============================================================
# STEP 2D
# NORMALIZE JOB DETAILS
# ============================================================

def normalize_job_details_data(
    job_details_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize job-detail lookup/history.
    """

    df = job_details_df.copy()


    identifier_columns = [
        "IdentifiantPoste",
        "IdentifiantEmploi",
        "CodeDirectionAffectée",
        "CodeBudget",
        "IndicateurGestion",
        "CodePosteSecondaire",
        "MatriculeGestionnaire",
    ]


    for column in identifier_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_identifier
                )
            )


    if "DateEffetAffectation" in df.columns:

        df[
            "DateEffetAffectation"
        ] = (
            df[
                "DateEffetAffectation"
            ]
            .apply(
                normalize_date
            )
        )


    numeric_columns = [
        "HeuresSemaineContrat",
        "HeuresJourContrat",
        "JoursTravailléesSemaine",
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_number
                )
            )


    return df


# ============================================================
# STEP 2E
# NORMALIZE EMPLOYMENT REASONS
# ============================================================

def normalize_employment_reasons_data(
    employment_reasons_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize employment-reason lookup.
    """

    df = employment_reasons_df.copy()


    identifier_columns = [
        "CodeCatégorieStatut",
        "CodeStatutSystèmeExterne",
        "CodeGestionAccès",
    ]


    for column in identifier_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .apply(
                    normalize_identifier
                )
            )


    return df


# ============================================================
# STEP 2F
# NORMALIZATION TRACE
# ============================================================

def print_normalization_example(
    dataset_name: str,
    raw_df: pd.DataFrame,
    normalized_df: pd.DataFrame,
    columns: list[str],
) -> None:
    """
    Display original and normalized values.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        f"CORROBORIA - NORMALIZATION TRACE: {dataset_name}"
    )

    print(
        "=" * 70
    )


    if raw_df.empty:

        print(
            "Dataset is empty."
        )

        return


    raw_row = raw_df.iloc[0]

    normalized_row = normalized_df.iloc[0]


    for column in columns:

        if (
            column in raw_df.columns
            and column in normalized_df.columns
        ):

            print(
                f"\n{column}"
            )

            print(
                f"  RAW:        {raw_row[column]!r}"
            )

            print(
                f"  NORMALIZED: {normalized_row[column]!r}"
            )


# ============================================================
# STEP 2G
# PREVIEW NORMALIZED DATA
# ============================================================

def preview_normalized_data(
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    job_details_df: pd.DataFrame,
    employment_reasons_df: pd.DataFrame,
) -> None:
    """
    Display normalized dataset samples.
    """

    # --------------------------------------------------------
    # SYSTEM A
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED SOURCE DATA"
    )

    print(
        "=" * 70
    )

    print(
        source_df.head(5)
    )


    # --------------------------------------------------------
    # SYSTEM B
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED DESTINATION DATA"
    )

    print(
        "=" * 70
    )


    destination_preview_columns = [
        "personId",
        "givenName",
        "surname",
        "onboardDate",
        "contractTypeCode",
        "detailedStatus",
        "siteCode",
        "divisionId",
        "positionId",
        "positionName",
        "isPrimaryAssignment",
        "isTemporaryAssignment",
        "assignmentStartDate",
        "weeklyHoursOverride",
        "dailyHoursOverride",
    ]


    destination_preview_columns = [
        column
        for column in destination_preview_columns
        if column in destination_df.columns
    ]


    print(
        destination_df[
            destination_preview_columns
        ].head(5)
    )


    # --------------------------------------------------------
    # JOB DETAILS
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED JOB DETAILS"
    )

    print(
        "=" * 70
    )

    print(
        job_details_df.head(5)
    )


    # --------------------------------------------------------
    # EMPLOYMENT REASONS
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED EMPLOYMENT REASONS"
    )

    print(
        "=" * 70
    )

    print(
        employment_reasons_df.head(5)
    )


# ============================================================
# STEP 3G
# PRINT FULL BUSINESS RULE DETAILS
# ============================================================

def preview_full_rule_details(
    parsed_mapping_df: pd.DataFrame
) -> None:
    """
    Print every rule-driven or supporting mapping row together
    with its original rule text.

    This is temporary diagnostic output used before business
    rules are implemented.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - FULL RULE-BASED MAPPING DETAILS"
    )

    print(
        "=" * 70
    )


    rule_rows = parsed_mapping_df[

        parsed_mapping_df[
            "row_type"
        ].isin(
            [
                "RULE_BASED",
                "RULE_CONTINUATION",
                "SUPPORTING_SOURCE",
            ]
        )

    ]


    if rule_rows.empty:

        print(
            "\nNo rule-based mapping rows found."
        )

        return


    for _, row in rule_rows.iterrows():

        print(
            f"\nExcel row {row['mapping_row']}"
        )

        print(
            f"  Type:        {row['row_type']}"
        )

        print(
            f"  Description: {row['description']}"
        )

        print(
            f"  Source:      {row['source_field']}"
        )

        print(
            f"  Destination: {row['destination_field']}"
        )

        print(
            f"  Rule:        {row['rule_text']}"
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # STEP 1
    # LOAD INPUT FILES
    # ========================================================

    workbooks = load_all_data()


    # ========================================================
    # INPUT STRUCTURE
    # ========================================================

    inspect_workbooks(
        workbooks
    )


    # ========================================================
    # STEP 2A
    # EXTRACT DATAFRAMES
    # ========================================================

    dataframes = extract_dataframes(
        workbooks
    )


    # ========================================================
    # PRESERVE RAW DATA
    # ========================================================

    raw_source_df = (
        dataframes[
            "source"
        ].copy()
    )


    raw_destination_df = (
        dataframes[
            "destination"
        ].copy()
    )


    raw_job_details_df = (
        dataframes[
            "job_details"
        ].copy()
    )


    raw_employment_reasons_df = (
        dataframes[
            "employment_reasons"
        ].copy()
    )


    # ========================================================
    # STEP 2B
    # NORMALIZE SYSTEM A
    # ========================================================

    source_df = normalize_source_data(
        raw_source_df
    )


    # ========================================================
    # STEP 2C
    # NORMALIZE SYSTEM B
    # ========================================================

    destination_df = normalize_destination_data(
        raw_destination_df
    )


    # ========================================================
    # STEP 2D
    # NORMALIZE JOB DETAILS
    # ========================================================

    job_details_df = normalize_job_details_data(
        raw_job_details_df
    )


    # ========================================================
    # STEP 2E
    # NORMALIZE EMPLOYMENT REASONS
    # ========================================================

    employment_reasons_df = (
        normalize_employment_reasons_data(
            raw_employment_reasons_df
        )
    )


    # ========================================================
    # DISPLAY NORMALIZED DATA
    # ========================================================

    preview_normalized_data(
        source_df=source_df,
        destination_df=destination_df,
        job_details_df=job_details_df,
        employment_reasons_df=employment_reasons_df,
    )


    # ========================================================
    # NORMALIZATION TRACE - SYSTEM A
    # ========================================================

    print_normalization_example(
        dataset_name="SYSTEM A",
        raw_df=raw_source_df,
        normalized_df=source_df,
        columns=[
            "Matricule",
            "DateEmbaucheRécente",
            "EstPermanent",
            "HeuresNormeHebdo",
        ],
    )


    # ========================================================
    # NORMALIZATION TRACE - SYSTEM B
    # ========================================================

    print_normalization_example(
        dataset_name="SYSTEM B",
        raw_df=raw_destination_df,
        normalized_df=destination_df,
        columns=[
            "personId",
            "onboardDate",
            "isPrimaryAssignment",
            "weeklyHoursOverride",
        ],
    )


    # ========================================================
    # NORMALIZATION TRACE - JOB DETAILS
    # ========================================================

    print_normalization_example(
        dataset_name="JOB DETAILS",
        raw_df=raw_job_details_df,
        normalized_df=job_details_df,
        columns=[
            "IdentifiantPoste",
            "DateEffetAffectation",
            "HeuresSemaineContrat",
        ],
    )


    # ========================================================
    # STEP 3A
    # PARSE MAIN MAPPING
    # ========================================================

    parsed_mapping_df = parse_mapping_sheet(
        dataframes[
            "mapping"
        ]
    )


    # ========================================================
    # STEP 3B
    # PARSE EMPLOYMENT STATUS RULES
    # ========================================================

    employment_rules_df = parse_employment_rules(
        dataframes[
            "employment_rules"
        ]
    )


    # ========================================================
    # STEP 3C
    # PARSE JOB DETAIL JOIN INSTRUCTIONS
    # ========================================================

    job_join_df = parse_join_sheet(
        dataframes[
            "job_join"
        ]
    )


    # ========================================================
    # STEP 3D
    # PARSE EMPLOYMENT REASON JOIN INSTRUCTIONS
    # ========================================================

    employment_reason_join_df = parse_join_sheet(
        dataframes[
            "employment_reason_join"
        ]
    )


    # ========================================================
    # STEP 3E
    # VALIDATE DIRECT MAPPINGS
    # ========================================================

    direct_mapping_issues_df = (
        validate_direct_mappings(

            parsed_mapping_df=
                parsed_mapping_df,

            source_df=
                source_df,

            destination_df=
                destination_df,
        )
    )


    # ========================================================
    # STEP 3F
    # DISPLAY MAPPING ANALYSIS
    # ========================================================

    preview_mapping_analysis(

        parsed_mapping_df=
            parsed_mapping_df,

        employment_rules_df=
            employment_rules_df,

        job_join_df=
            job_join_df,

        employment_reason_join_df=
            employment_reason_join_df,

        validation_issues_df=
            direct_mapping_issues_df,
    )


    # ========================================================
    # STEP 3G
    # DISPLAY FULL RULE TEXT
    # ========================================================

    preview_full_rule_details(
        parsed_mapping_df=
            parsed_mapping_df
    )


    # ========================================================
    # STEP 4A
    # FIND MISSING EMPLOYEE IDS
    # ========================================================

    (
        source_missing_ids_df,
        destination_missing_ids_df,
    ) = find_missing_employee_ids(

        source_df=
            source_df,

        destination_df=
            destination_df,
    )


    # ========================================================
    # STEP 4B
    # MATCH EMPLOYEES
    # ========================================================

    employee_matches_df = match_employees(

        source_df=
            source_df,

        destination_df=
            destination_df,
    )


    # ========================================================
    # STEP 4C
    # DISPLAY EMPLOYEE MATCHING
    # ========================================================

    preview_employee_matching(

        employee_matches_df=
            employee_matches_df,

        source_df=
            source_df,

        destination_df=
            destination_df,

        source_missing_ids_df=
            source_missing_ids_df,

        destination_missing_ids_df=
            destination_missing_ids_df,
    )


    # ========================================================
    # STEP 5A
    # MATCH ASSIGNMENTS
    # ========================================================

    assignment_matches_df = match_assignments(

        source_df=
            source_df,

        destination_df=
            destination_df,

        employee_matches_df=
            employee_matches_df,
    )


    # ========================================================
    # STEP 5B
    # DISPLAY ASSIGNMENT MATCHING
    # ========================================================

    preview_assignment_matching(

        assignment_matches_df=
            assignment_matches_df,
    )


    # ========================================================
    # STEP 6A
    # DIRECT FIELD CORROBORATION
    # ========================================================

    comparison_df = compare_direct_mappings(

        raw_source_df=
            raw_source_df,

        raw_destination_df=
            raw_destination_df,

        source_df=
            source_df,

        destination_df=
            destination_df,

        parsed_mapping_df=
            parsed_mapping_df,

        assignment_matches_df=
            assignment_matches_df,
    )


    # ========================================================
    # STEP 6B
    # DISPLAY DIRECT COMPARISON RESULTS
    # ========================================================

    preview_direct_comparisons(

        comparison_df=
            comparison_df,
    )


    # ========================================================
    # STEP 6C
    # SANITY CHECK
    # ========================================================

    deterministic_match_count = len(

        assignment_matches_df[

            assignment_matches_df[
                "assignment_match_status"
            ] == "MATCHED"

        ]

    )


    direct_mapping_count = len(

        parsed_mapping_df[

            parsed_mapping_df[
                "row_type"
            ] == "DIRECT"

        ]

    )


    expected_comparison_count = (
        deterministic_match_count
        *
        direct_mapping_count
    )


    actual_comparison_count = len(
        comparison_df
    )


    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - DIRECT COMPARISON SANITY CHECK"
    )

    print(
        "=" * 70
    )


    print(
        f"\nDeterministic assignment matches: "
        f"{deterministic_match_count}"
    )


    print(
        f"Direct mappings: "
        f"{direct_mapping_count}"
    )


    print(
        f"Expected direct comparisons: "
        f"{expected_comparison_count}"
    )


    print(
        f"Actual direct comparisons: "
        f"{actual_comparison_count}"
    )


    if (
        actual_comparison_count
        ==
        expected_comparison_count
    ):

        print(
            "\nDirect comparison count is correct."
        )

    else:

        print(
            "\nWARNING: Direct comparison count does not "
            "match the expected number."
        )


    # ========================================================
    # FINAL SUCCESS MESSAGE
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "CorroborIA loading, normalization, mapping, "
        "employee matching, assignment matching and "
        "direct field corroboration completed successfully."
    )

    print(
        "Raw values and normalized values were preserved "
        "for traceability."
    )

    print(
        "Business rules have not yet been applied."
    )

    print(
        "Full mapping rule instructions were displayed "
        "for review before rule implementation."
    )

    print(
        "=" * 70
    )
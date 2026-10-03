# ============================================================
# CORROBORIA
# PERSON 1 - DATA + RULE ENGINE
# ============================================================
#
# CURRENT STATUS
#
# STEP 1
#
#   ✅ Locate files
#   ✅ Verify files exist
#   ✅ Load Excel workbooks
#   ✅ Repair malformed job-details workbook
#
#
# STEP 2
#
#   ✅ Extract useful worksheets
#   ✅ Preserve raw data
#   ✅ Normalize System A
#   ✅ Normalize System B
#   ✅ Normalize job details
#   ✅ Normalize employment reasons
#
#
# STEP 3
#
#   ✅ Parse Mapping.xlsx
#   ✅ Classify direct vs rule-based mappings
#   ✅ Parse supporting rule sheets
#   ✅ Validate direct mappings
#
#
# STEP 4
#
#   ✅ Match employees using Matricule <-> personId
#   ✅ Detect employees present in only one system
#   ✅ Count rows belonging to each employee
#   ✅ Identify employees requiring assignment matching
#
#
# STEP 5
#
#   ✅ Interpret assignment type P / A / S
#   ✅ Match assignments conservatively
#   ✅ Detect source-only assignments
#   ✅ Detect destination-only assignments
#   ✅ Preserve ambiguous assignment groups
#
#
# NOT IMPLEMENTED YET
#
#   ⬜ Direct field corroboration
#   ⬜ Business-rule execution
#   ⬜ Final comparison DataFrame
#   ⬜ AI analysis
#   ⬜ Final report
#
#
# IMPORTANT ARCHITECTURE RULES
#
#   1. Original Excel files remain read-only.
#
#   2. Raw values are preserved for traceability.
#
#   3. Normalization changes representation only.
#
#   4. Mapping.xlsx decides which fields are corroborated.
#
#   5. Employee matching happens before assignment matching.
#
#   6. Assignment matching does NOT use fields that will later
#      be corroborated to force a match.
#
#   7. Ambiguous assignment groups remain ambiguous.
#
#   8. Deterministic business rules execute before AI.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
from io import StringIO

import pandas as pd


# ============================================================
# NORMALIZATION FUNCTIONS
# ============================================================

from corroboria.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_identifier,
    normalize_number,
    normalize_text,
)


# ============================================================
# MAPPING PARSER FUNCTIONS
# ============================================================

from corroboria.mapping_parser import (
    parse_employment_rules,
    parse_join_sheet,
    parse_mapping_sheet,
    preview_mapping_analysis,
    validate_direct_mappings,
)


# ============================================================
# EMPLOYEE MATCHING FUNCTIONS
# ============================================================

from corroboria.matcher import (
    find_missing_employee_ids,
    match_employees,
    preview_employee_matching,
)


# ============================================================
# ASSIGNMENT MATCHING FUNCTIONS
# ============================================================

from corroboria.assignment_matcher import (
    match_assignments,
    preview_assignment_matching,
)


# ============================================================
# PROJECT PATHS
# ============================================================

# Folder containing this main.py file.
BASE_DIR = Path(__file__).resolve().parent


# Folder containing challenge input files.
DATA_DIR = BASE_DIR / "data"


# ============================================================
# INPUT FILES
# ============================================================

FILES = {

    # --------------------------------------------------------
    # SYSTEM A - HR
    # --------------------------------------------------------

    "source":
        DATA_DIR / "Employe_Source_Anonymise_VF.xlsx",


    # --------------------------------------------------------
    # SYSTEM B - TIME
    # --------------------------------------------------------

    "destination":
        DATA_DIR / "Employe_Destination_Anonymise_VF.xlsx",


    # --------------------------------------------------------
    # MAPPING + BUSINESS RULES
    # --------------------------------------------------------

    "mapping":
        DATA_DIR / "Mapping.xlsx",


    # --------------------------------------------------------
    # JOB / POSITION HISTORY
    # --------------------------------------------------------

    "job_details":
        DATA_DIR / "détail_du_poste.xlsx",


    # --------------------------------------------------------
    # EMPLOYMENT REASONS
    # --------------------------------------------------------

    "employment_reasons":
        DATA_DIR / "Motif de la situation d'emploi.xlsx",
}


# ============================================================
# STEP 1A
# VERIFY REQUIRED FILES
# ============================================================

def check_files_exist() -> None:
    """
    Ensure that every required input file exists.

    This function does not modify any file.
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
    Load every worksheet from one Excel workbook.

    sheet_name=None means all worksheets are loaded.

    Nothing is written back to the original file.
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
    Repair an Excel worksheet containing comma-separated
    information inside one column.

    This occurs in:

        détail_du_poste.xlsx
    """

    # --------------------------------------------------------
    # Already contains several columns.
    # Nothing needs repairing.
    # --------------------------------------------------------

    if len(df.columns) != 1:

        return df


    # Get the only column name.
    column_name = str(
        df.columns[0]
    )


    # --------------------------------------------------------
    # If there is no comma, this may be a legitimate
    # one-column sheet.
    # --------------------------------------------------------

    if "," not in column_name:

        return df


    # --------------------------------------------------------
    # RECONSTRUCT CSV TEXT
    # --------------------------------------------------------

    # The Excel column header is actually the real CSV header.
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


    # Join all rows with newline characters.
    csv_text = "\n".join(
        rows
    )


    # --------------------------------------------------------
    # PARSE THE RECONSTRUCTED CSV
    # --------------------------------------------------------

    corrected_df = pd.read_csv(

        StringIO(csv_text),

        sep=",",

        dtype=object,
    )


    return corrected_df


# ============================================================
# STEP 1D
# LOAD ALL WORKBOOKS
# ============================================================

def load_all_data() -> dict[str, dict[str, pd.DataFrame]]:
    """
    Load every CorroborIA workbook.
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
        # SPECIAL CASE:
        # Repair malformed job-details workbook.
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
# INSPECT WORKBOOK STRUCTURE
# ============================================================

def inspect_workbooks(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> None:
    """
    Display workbook structure during development.
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
# EXTRACT USEFUL DATAFRAMES
# ============================================================

def extract_dataframes(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> dict[str, pd.DataFrame]:
    """
    Extract worksheets required by the project.

    .copy() prevents changes to the originally loaded
    workbook DataFrames.
    """

    return {

        # ----------------------------------------------------
        # SYSTEM A
        # ----------------------------------------------------

        "source":
            workbooks[
                "source"
            ][
                "Employe_Source"
            ].copy(),


        # ----------------------------------------------------
        # SYSTEM B
        # ----------------------------------------------------

        "destination":
            workbooks[
                "destination"
            ][
                "Employe_Destination"
            ].copy(),


        # ----------------------------------------------------
        # MAIN MAPPING
        # ----------------------------------------------------

        "mapping":
            workbooks[
                "mapping"
            ][
                "Mapping"
            ].copy(),


        # ----------------------------------------------------
        # EMPLOYMENT STATUS RULES
        # ----------------------------------------------------

        "employment_rules":
            workbooks[
                "mapping"
            ][
                "Règles situation d'emploi"
            ].copy(),


        # ----------------------------------------------------
        # JOB DETAIL JOIN INSTRUCTIONS
        # ----------------------------------------------------

        "job_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Détail du poste"
            ].copy(),


        # ----------------------------------------------------
        # EMPLOYMENT REASON JOIN INSTRUCTIONS
        # ----------------------------------------------------

        "employment_reason_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Motif des situations"
            ].copy(),


        # ----------------------------------------------------
        # JOB DETAILS
        # ----------------------------------------------------

        "job_details":
            workbooks[
                "job_details"
            ][
                "Feuil1"
            ].copy(),


        # ----------------------------------------------------
        # EMPLOYMENT REASONS
        # ----------------------------------------------------

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
    Normalize System A / HR values.

    This changes representation only.

    It does NOT determine whether data is correct.
    """

    df = source_df.copy()


    # ========================================================
    # IDENTIFIERS / CODES
    # ========================================================

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


    # ========================================================
    # TEXT
    # ========================================================

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


    # ========================================================
    # DATES
    # ========================================================

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


    # ========================================================
    # BOOLEANS
    # ========================================================

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


    # ========================================================
    # NUMERIC QUANTITIES
    # ========================================================

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
    Normalize System B / Time data.

    Mapping.xlsx will later decide which fields participate
    in corroboration.
    """

    df = destination_df.copy()


    # ========================================================
    # IDENTIFIERS / CODES
    # ========================================================

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


    # ========================================================
    # TEXT
    # ========================================================

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


    # ========================================================
    # DATES
    # ========================================================

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


    # ========================================================
    # BOOLEANS
    # ========================================================

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


    # ========================================================
    # NUMERIC QUANTITIES
    # ========================================================

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
    Normalize historical position/job information.

    No business meaning is inferred here.
    """

    df = job_details_df.copy()


    # ========================================================
    # IDENTIFIERS / CODES
    # ========================================================

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


    # ========================================================
    # EFFECTIVE DATE
    # ========================================================

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


    # ========================================================
    # NUMERIC QUANTITIES
    # ========================================================

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
    Normalize employment-reason lookup codes.
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
    Display raw and normalized values side-by-side.

    This proves that raw values remain available for
    traceability.
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
    Display small samples from normalized datasets.
    """

    # ========================================================
    # SYSTEM A
    # ========================================================

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


    # ========================================================
    # SYSTEM B
    # ========================================================

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


    # ========================================================
    # JOB DETAILS
    # ========================================================

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


    # ========================================================
    # EMPLOYMENT REASONS
    # ========================================================

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
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # STEP 1
    # LOAD WORKBOOKS
    # ========================================================

    workbooks = load_all_data()


    # ========================================================
    # INSPECT INPUT STRUCTURE
    # ========================================================

    inspect_workbooks(
        workbooks
    )


    # ========================================================
    # STEP 2A
    # EXTRACT WORKSHEETS
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

        raw_df=
            raw_source_df,

        normalized_df=
            source_df,

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

        raw_df=
            raw_destination_df,

        normalized_df=
            destination_df,

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

        raw_df=
            raw_job_details_df,

        normalized_df=
            job_details_df,

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
    # PARSE EMPLOYMENT-REASON JOIN INSTRUCTIONS
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
    # STEP 4A
    # FIND ROWS WITH MISSING EMPLOYEE IDS
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
    #
    # IMPORTANT:
    #
    # Assignment matching is deliberately conservative.
    #
    # We use:
    #
    #     employee identity
    #
    # and:
    #
    #     assignment type
    #
    # We DO NOT use fields such as positionId to force a match,
    # because positionId itself must later be corroborated.
    #
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
    # FINAL SUCCESS MESSAGE
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "CorroborIA loading, normalization, mapping, "
        "employee matching and assignment matching "
        "completed successfully."
    )

    print(
        "Raw datasets were preserved for traceability."
    )

    print(
        "No field corroboration or business-rule verdicts "
        "have been executed yet."
    )

    print(
        "=" * 70
    )
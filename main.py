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
# NOT IMPLEMENTED YET
#
#   ⬜ Mapping parser
#   ⬜ Employee matching
#   ⬜ Assignment matching
#   ⬜ Raw comparisons
#   ⬜ Business rules
#   ⬜ AI
#   ⬜ Final report
#
#
# IMPORTANT ARCHITECTURE RULES
#
#   1. Original input files are read-only.
#
#   2. Raw values are preserved for traceability.
#
#   3. Normalization does not decide whether data is correct.
#
#   4. Mapping.xlsx will decide which fields are corroborated.
#
#   5. Business rules will execute before AI.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
from io import StringIO

import pandas as pd


from corroboria.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_identifier,
    normalize_number,
    normalize_text,
)


# ============================================================
# PROJECT PATHS
# ============================================================

# Directory containing main.py
BASE_DIR = Path(__file__).resolve().parent


# Directory containing challenge files
DATA_DIR = BASE_DIR / "data"


# ============================================================
# INPUT FILES
# ============================================================

FILES = {

    # System A - HR source
    "source":
        DATA_DIR / "Employe_Source_Anonymise_VF.xlsx",

    # System B - Time destination
    "destination":
        DATA_DIR / "Employe_Destination_Anonymise_VF.xlsx",

    # Mapping and business-rule workbook
    "mapping":
        DATA_DIR / "Mapping.xlsx",

    # Historical position/job details
    "job_details":
        DATA_DIR / "détail_du_poste.xlsx",

    # Employment situation/reason lookup
    "employment_reasons":
        DATA_DIR / "Motif de la situation d'emploi.xlsx",
}


# ============================================================
# STEP 1A
# VERIFY REQUIRED FILES
# ============================================================

def check_files_exist() -> None:
    """
    Ensure that all required input files exist.

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
    Load every worksheet from an Excel workbook.

    sheet_name=None means that all worksheets are loaded.

    IMPORTANT:

    This only reads the workbook.

    Nothing is written back to Excel.
    """

    return pd.read_excel(
        path,
        sheet_name=None,
        dtype=object,
        engine="openpyxl",
    )


# ============================================================
# STEP 1C
# REPAIR JOB-DETAILS WORKBOOK
# ============================================================

def fix_comma_separated_sheet(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Repair a worksheet that contains CSV-like information
    inside a single Excel column.

    This occurs in:

        détail_du_poste.xlsx
    """

    # Already normal.
    if len(df.columns) != 1:
        return df


    column_name = str(
        df.columns[0]
    )


    # A legitimate one-column worksheet should not be changed.
    if "," not in column_name:
        return df


    # The current Excel column header is actually the CSV header.
    rows = [
        column_name
    ]


    # Add every row stored inside the single column.
    for value in df.iloc[:, 0]:

        if pd.isna(value):

            rows.append("")

        else:

            rows.append(
                str(value)
            )


    # Rebuild CSV text.
    csv_text = "\n".join(
        rows
    )


    # Parse reconstructed CSV.
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
    Load all CorroborIA input workbooks.

    Returned structure:

        workbooks["source"]["Employe_Source"]

        workbooks["destination"]["Employe_Destination"]

        workbooks["mapping"]["Mapping"]

        etc.
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
        # Repair job-details workbook
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
# INSPECT INPUT STRUCTURE
# ============================================================

def inspect_workbooks(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> None:
    """
    Display workbook structure.

    This is useful during development.
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
    Extract the worksheets required by the project.

    .copy() is important.

    We work on copies rather than modifying the DataFrames
    stored inside the original workbook structure.
    """

    return {

        # System A
        "source":
            workbooks[
                "source"
            ][
                "Employe_Source"
            ].copy(),


        # System B
        "destination":
            workbooks[
                "destination"
            ][
                "Employe_Destination"
            ].copy(),


        # Main mapping
        "mapping":
            workbooks[
                "mapping"
            ][
                "Mapping"
            ].copy(),


        # Employment-status rules
        "employment_rules":
            workbooks[
                "mapping"
            ][
                "Règles situation d'emploi"
            ].copy(),


        # Join definition for job details
        "job_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Détail du poste"
            ].copy(),


        # Join definition for employment reasons
        "employment_reason_join":
            workbooks[
                "mapping"
            ][
                "Jointure - Motif des situations"
            ].copy(),


        # Job/position history
        "job_details":
            workbooks[
                "job_details"
            ][
                "Feuil1"
            ].copy(),


        # Employment-reason lookup
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
    Normalize System A / HR employee data.

    This changes representation only.

    It does NOT determine whether a value is correct.
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

    Only representation is normalized here.

    Mapping.xlsx will later determine which fields actually
    participate in corroboration.
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
    Normalize historical job/position data.

    IMPORTANT:

    No business meaning is inferred here.

    For example, IndicateurGestion is treated as a code rather
    than automatically assuming that it represents a boolean.
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
# NORMALIZE EMPLOYMENT-REASON LOOKUP
# ============================================================

def normalize_employment_reasons_data(
    employment_reasons_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize employment-reason lookup values.

    These fields are treated as codes.
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
# BASIC NORMALIZATION TRACE
# ============================================================

def print_normalization_example(
    dataset_name: str,
    raw_df: pd.DataFrame,
    normalized_df: pd.DataFrame,
    columns: list[str],
) -> None:
    """
    Display raw and normalized values side-by-side.

    This is useful for traceability.

    Later, the final corroboration result will preserve:
        raw value
        normalized value
        expected value
        destination value

    For now this function simply proves that we retain both
    raw and normalized datasets.
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
    Show small samples from all normalized datasets.
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
    # DEVELOPMENT INSPECTION
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
    #
    # These raw DataFrames remain available later so that
    # reports can show exactly what was originally supplied.
    #

    raw_source_df = (
        dataframes["source"].copy()
    )

    raw_destination_df = (
        dataframes["destination"].copy()
    )

    raw_job_details_df = (
        dataframes["job_details"].copy()
    )

    raw_employment_reasons_df = (
        dataframes["employment_reasons"].copy()
    )


    # ========================================================
    # NORMALIZE SYSTEM A
    # ========================================================

    source_df = normalize_source_data(
        raw_source_df
    )


    # ========================================================
    # NORMALIZE SYSTEM B
    # ========================================================

    destination_df = normalize_destination_data(
        raw_destination_df
    )


    # ========================================================
    # NORMALIZE JOB DETAILS
    # ========================================================

    job_details_df = normalize_job_details_data(
        raw_job_details_df
    )


    # ========================================================
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
        source_df,
        destination_df,
        job_details_df,
        employment_reasons_df,
    )


    # ========================================================
    # SHOW RAW → NORMALIZED TRACE EXAMPLES
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
    # FINAL MESSAGE
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "All CorroborIA datasets normalized successfully."
    )

    print(
        "Raw datasets were preserved for future traceability."
    )

    print(
        "=" * 70
    )
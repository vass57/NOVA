# ============================================================
# CORROBORIA
# MAIN PIPELINE
# ============================================================
#
# STEP 1
#   Load and validate files
#
# STEP 2
#   Preserve raw data and normalize datasets
#
# STEP 3
#   Parse mapping and supplied business rules
#
# STEP 4
#   Match employees
#
# STEP 5
#   Match assignments conservatively
#
# STEP 6
#   Compare direct mappings
#
# STEP 7
#   Apply deterministic business rules
#
# STEP 8
#   Diagnostic validation
#
# STEP 9
#   Build unified corroboration report
#   Build analyst investigation view
#   Build AI queue
#   Export deterministic reports
#
# STEP 10
#   Analyze ambiguous assignment matches with ML
#   Prioritize anomaly profiles with ML
#   Detect systematic discrepancy patterns
#   Export AI results
#
#
# IMPORTANT PRINCIPLE
#
# Deterministic rules remain authoritative.
#
# AI may:
#   - analyze ambiguity
#   - rank candidates
#   - prioritize anomalies
#   - identify patterns
#   - generate useful explanations
#
# AI does NOT silently override deterministic verdicts.
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

from corroboria.business_rules import (
    evaluate_rule_based_fields,
    preview_rule_based_results,
)

from corroboria.final_report import (
    build_ai_queue,
    build_final_report,
    build_investigation_report,
    export_reports,
    preview_final_report,
)

from corroboria.ai_analyzer import (
    analyze_ambiguous_assignments,
    export_ai_analysis,
    preview_ai_analysis,
    prioritize_anomalies,
    summarize_anomaly_patterns,
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


DATA_DIR = (
    BASE_DIR
    /
    "data"
)


OUTPUT_DIR = (
    BASE_DIR
    /
    "output"
)


# ============================================================
# INPUT FILES
# ============================================================

FILES = {

    "source":
        DATA_DIR
        /
        "Employe_Source_Anonymise_VF.xlsx",

    "destination":
        DATA_DIR
        /
        "Employe_Destination_Anonymise_VF.xlsx",

    "mapping":
        DATA_DIR
        /
        "Mapping.xlsx",

    "job_details":
        DATA_DIR
        /
        "détail_du_poste.xlsx",

    "employment_reasons":
        DATA_DIR
        /
        "Motif de la situation d'emploi.xlsx",
}


# ============================================================
# STEP 1A
# VERIFY REQUIRED FILES
# ============================================================

def check_files_exist() -> None:
    """
    Ensure that every required challenge file exists.
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
            +
            "\n".join(
                missing_files
            )
        )


# ============================================================
# STEP 1B
# LOAD ONE EXCEL WORKBOOK
# ============================================================

def load_excel_file(
    path: Path
) -> dict[str, pd.DataFrame]:
    """
    Load all worksheets from an Excel workbook.
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
    Repair a worksheet containing comma-separated data
    inside one Excel column.
    """

    if len(
        df.columns
    ) != 1:

        return df


    column_name = str(
        df.columns[
            0
        ]
    )


    if "," not in column_name:

        return df


    rows = [
        column_name
    ]


    for value in df.iloc[
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


    corrected_df = pd.read_csv(
        StringIO(
            csv_text
        ),
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
        # SPECIAL CASE:
        # Repair malformed job-detail workbook
        # ----------------------------------------------------

        if name == "job_details":

            for (
                sheet_name,
                df,
            ) in sheets.items():

                sheets[
                    sheet_name
                ] = (
                    fix_comma_separated_sheet(
                        df
                    )
                )


        workbooks[
            name
        ] = sheets


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
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - INPUT DATA SUMMARY"
    )

    print(
        "=" * 70
    )


    for (
        workbook_name,
        sheets,
    ) in workbooks.items():

        print(
            f"\n[{workbook_name.upper()}]"
        )


        for (
            sheet_name,
            df,
        ) in sheets.items():

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

    df = (
        source_df
        .copy()
    )


    # ========================================================
    # IDENTIFIERS
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
                .apply(
                    normalize_boolean
                )
            )


    # ========================================================
    # NUMBERS
    # ========================================================

    numeric_columns = [
        "HeuresNormeHebdo",
        "HeuresNormeQuotidienne",
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[
                column
            ] = (
                df[
                    column
                ]
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

    df = (
        destination_df
        .copy()
    )


    # ========================================================
    # IDENTIFIERS
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
                .apply(
                    normalize_boolean
                )
            )


    # ========================================================
    # NUMBERS
    # ========================================================

    numeric_columns = [
        "wageOverrideAmount",
        "wageMultiplierFactor",
        "weeklyHoursOverride",
        "dailyHoursOverride",
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[
                column
            ] = (
                df[
                    column
                ]
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
    Normalize job-detail history.
    """

    df = (
        job_details_df
        .copy()
    )


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

            df[
                column
            ] = (
                df[
                    column
                ]
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

            df[
                column
            ] = (
                df[
                    column
                ]
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

    df = (
        employment_reasons_df
        .copy()
    )


    identifier_columns = [
        "CodeCatégorieStatut",
        "CodeStatutSystèmeExterne",
        "CodeGestionAccès",
    ]


    for column in identifier_columns:

        if column in df.columns:

            df[
                column
            ] = (
                df[
                    column
                ]
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
    Display raw vs normalized values.
    """

    print(
        "\n"
        +
        "=" * 70
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


    raw_row = (
        raw_df
        .iloc[
            0
        ]
    )


    normalized_row = (
        normalized_df
        .iloc[
            0
        ]
    )


    for column in columns:

        if (
            column in raw_df.columns
            and
            column in normalized_df.columns
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
    Preview normalized datasets.
    """

    # ========================================================
    # SOURCE
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED SOURCE DATA"
    )

    print(
        "=" * 70
    )

    print(
        source_df.head(
            5
        )
    )


    # ========================================================
    # DESTINATION
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
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

        for column
        in destination_preview_columns

        if column
        in destination_df.columns

    ]


    print(
        destination_df[
            destination_preview_columns
        ].head(
            5
        )
    )


    # ========================================================
    # JOB DETAILS
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED JOB DETAILS"
    )

    print(
        "=" * 70
    )

    print(
        job_details_df.head(
            5
        )
    )


    # ========================================================
    # EMPLOYMENT REASONS
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - NORMALIZED EMPLOYMENT REASONS"
    )

    print(
        "=" * 70
    )

    print(
        employment_reasons_df.head(
            5
        )
    )


# ============================================================
# STEP 3G
# FULL BUSINESS RULE DETAILS
# ============================================================

def preview_full_rule_details(
    parsed_mapping_df: pd.DataFrame
) -> None:
    """
    Display full rule text from Mapping.xlsx.
    """

    print(
        "\n"
        +
        "=" * 70
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
# STEP 8
# BUSINESS RULE DEBUG DATA
# ============================================================

def preview_rule_debug_data(
    source_df: pd.DataFrame,
    raw_job_details_df: pd.DataFrame,
    job_details_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    assignment_matches_df: pd.DataFrame,
) -> None:
    """
    Diagnostic output used to validate business-rule
    assumptions.
    """

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - BUSINESS RULE DEBUG DATA"
    )

    print(
        "=" * 70
    )


    safe_matches = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ]
        ==
        "MATCHED"

    ].copy()


    # ========================================================
    # POSITION + EMAIL
    # ========================================================

    print(
        "\nPOSITION / EMAIL DIAGNOSTIC"
    )

    print(
        "-" * 70
    )


    debug_rows = []


    for _, match in safe_matches.iterrows():

        source_index = int(
            match[
                "source_row_index"
            ]
        )


        destination_index = int(
            match[
                "destination_row_index"
            ]
        )


        source_row = (
            source_df.loc[
                source_index
            ]
        )


        destination_row = (
            destination_df.loc[
                destination_index
            ]
        )


        debug_rows.append(
            {
                "employee_id":
                    match[
                        "employee_id"
                    ],

                "source_index":
                    source_index,

                "destination_index":
                    destination_index,

                "CodePoste":
                    source_row.get(
                        "CodePoste"
                    ),

                "IntituléPoste":
                    source_row.get(
                        "IntituléPoste"
                    ),

                "CodeEmploi":
                    source_row.get(
                        "CodeEmploi"
                    ),

                "IntituléEmploi":
                    source_row.get(
                        "IntituléEmploi"
                    ),

                "positionId":
                    destination_row.get(
                        "positionId"
                    ),

                "positionCode":
                    destination_row.get(
                        "positionCode"
                    ),

                "positionName":
                    destination_row.get(
                        "positionName"
                    ),

                "PrénomUsuel":
                    source_row.get(
                        "PrénomUsuel"
                    ),

                "NomFamille":
                    source_row.get(
                        "NomFamille"
                    ),

                "Matricule":
                    source_row.get(
                        "Matricule"
                    ),

                "contactEmail":
                    destination_row.get(
                        "contactEmail"
                    ),
            }
        )


    debug_df = pd.DataFrame(
        debug_rows
    )


    if debug_df.empty:

        print(
            "No deterministic assignment matches."
        )

    else:

        print(
            debug_df.to_string(
                index=False
            )
        )


    # ========================================================
    # JOB DETAIL DATE DIAGNOSTIC
    # ========================================================

    print(
        "\nJOB DETAIL DATE DIAGNOSTIC"
    )

    print(
        "-" * 70
    )


    required_columns = [
        "IdentifiantPoste",
        "IdentifiantEmploi",
        "CodeDirectionAffectée",
        "DateEffetAffectation",
    ]


    missing_columns = [

        column

        for column
        in required_columns

        if column
        not in job_details_df.columns

    ]


    if missing_columns:

        print(
            "Cannot display job-detail date diagnostic."
        )

        print(
            "Missing columns:"
        )


        for column in missing_columns:

            print(
                f"  - {column}"
            )


    else:

        date_debug_df = pd.DataFrame(
            {
                "row_index":
                    job_details_df.index,

                "position":
                    job_details_df[
                        "IdentifiantPoste"
                    ],

                "employment":
                    job_details_df[
                        "IdentifiantEmploi"
                    ],

                "direction":
                    job_details_df[
                        "CodeDirectionAffectée"
                    ],

                "raw_date":
                    raw_job_details_df[
                        "DateEffetAffectation"
                    ],

                "current_normalized_date":
                    job_details_df[
                        "DateEffetAffectation"
                    ],
            }
        )


        print(
            date_debug_df.head(
                40
            ).to_string(
                index=False
            )
        )


    # ========================================================
    # MATCHED JOB HISTORIES
    # ========================================================

    print(
        "\nJOB HISTORY USED BY MATCHED ASSIGNMENTS"
    )

    print(
        "-" * 70
    )


    matched_positions = set()


    for _, match in safe_matches.iterrows():

        source_index = int(
            match[
                "source_row_index"
            ]
        )


        source_row = (
            source_df.loc[
                source_index
            ]
        )


        position = source_row.get(
            "CodePoste"
        )


        if position is not None:

            matched_positions.add(
                str(
                    position
                )
            )


    history_rows = []


    for index, row in job_details_df.iterrows():

        position = str(
            row.get(
                "IdentifiantPoste"
            )
        )


        if position not in matched_positions:

            continue


        history_rows.append(
            {
                "job_detail_index":
                    index,

                "position":
                    row.get(
                        "IdentifiantPoste"
                    ),

                "employment":
                    row.get(
                        "IdentifiantEmploi"
                    ),

                "direction":
                    row.get(
                        "CodeDirectionAffectée"
                    ),

                "raw_date":
                    raw_job_details_df.loc[
                        index,
                        "DateEffetAffectation"
                    ],

                "current_normalized_date":
                    row.get(
                        "DateEffetAffectation"
                    ),
            }
        )


    history_df = pd.DataFrame(
        history_rows
    )


    if history_df.empty:

        print(
            "No matching job-detail history found."
        )

    else:

        print(
            history_df.to_string(
                index=False
            )
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # STEP 1
    # LOAD INPUT FILES
    # ========================================================

    workbooks = (
        load_all_data()
    )


    inspect_workbooks(
        workbooks
    )


    # ========================================================
    # STEP 2
    # EXTRACT DATAFRAMES
    # ========================================================

    dataframes = (
        extract_dataframes(
            workbooks
        )
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
    # STEP 2
    # NORMALIZATION
    # ========================================================

    source_df = (
        normalize_source_data(
            raw_source_df
        )
    )


    destination_df = (
        normalize_destination_data(
            raw_destination_df
        )
    )


    job_details_df = (
        normalize_job_details_data(
            raw_job_details_df
        )
    )


    employment_reasons_df = (
        normalize_employment_reasons_data(
            raw_employment_reasons_df
        )
    )


    # ========================================================
    # PREVIEW NORMALIZED DATA
    # ========================================================

    preview_normalized_data(

        source_df=
            source_df,

        destination_df=
            destination_df,

        job_details_df=
            job_details_df,

        employment_reasons_df=
            employment_reasons_df,
    )


    # ========================================================
    # NORMALIZATION TRACE
    # ========================================================

    print_normalization_example(

        dataset_name=
            "SYSTEM A",

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


    print_normalization_example(

        dataset_name=
            "SYSTEM B",

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


    print_normalization_example(

        dataset_name=
            "JOB DETAILS",

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
    # STEP 3
    # PARSE MAPPING
    # ========================================================

    parsed_mapping_df = (
        parse_mapping_sheet(
            dataframes[
                "mapping"
            ]
        )
    )


    employment_rules_df = (
        parse_employment_rules(
            dataframes[
                "employment_rules"
            ]
        )
    )


    job_join_df = (
        parse_join_sheet(
            dataframes[
                "job_join"
            ]
        )
    )


    employment_reason_join_df = (
        parse_join_sheet(
            dataframes[
                "employment_reason_join"
            ]
        )
    )


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


    preview_full_rule_details(

        parsed_mapping_df=
            parsed_mapping_df
    )


    # ========================================================
    # STEP 4
    # EMPLOYEE MATCHING
    # ========================================================

    (
        source_missing_ids_df,
        destination_missing_ids_df,
    ) = (
        find_missing_employee_ids(

            source_df=
                source_df,

            destination_df=
                destination_df,
        )
    )


    employee_matches_df = (
        match_employees(

            source_df=
                source_df,

            destination_df=
                destination_df,
        )
    )


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
    # STEP 5
    # ASSIGNMENT MATCHING
    # ========================================================

    assignment_matches_df = (
        match_assignments(

            source_df=
                source_df,

            destination_df=
                destination_df,

            employee_matches_df=
                employee_matches_df,
        )
    )


    preview_assignment_matching(

        assignment_matches_df=
            assignment_matches_df,
    )


    # ========================================================
    # STEP 6
    # DIRECT COMPARISONS
    # ========================================================

    comparison_df = (
        compare_direct_mappings(

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
    )


    preview_direct_comparisons(

        comparison_df=
            comparison_df,
    )


    # ========================================================
    # STEP 6
    # DIRECT SANITY CHECK
    # ========================================================

    deterministic_match_count = len(

        assignment_matches_df[

            assignment_matches_df[
                "assignment_match_status"
            ]
            ==
            "MATCHED"

        ]

    )


    direct_mapping_count = len(

        parsed_mapping_df[

            parsed_mapping_df[
                "row_type"
            ]
            ==
            "DIRECT"

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
        "\n"
        +
        "=" * 70
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
            "match expected count."
        )


    # ========================================================
    # STEP 7
    # BUSINESS RULE ENGINE
    # ========================================================

    rule_results_df = (
        evaluate_rule_based_fields(

            raw_destination_df=
                raw_destination_df,

            source_df=
                source_df,

            destination_df=
                destination_df,

            job_details_df=
                job_details_df,

            employment_reasons_df=
                employment_reasons_df,

            employment_rules_df=
                employment_rules_df,

            assignment_matches_df=
                assignment_matches_df,
        )
    )


    preview_rule_based_results(

        rule_results_df=
            rule_results_df,
    )


    # ========================================================
    # STEP 7
    # BUSINESS RULE SANITY CHECK
    # ========================================================

    expected_rule_comparisons = (
        deterministic_match_count
        *
        12
    )


    actual_rule_comparisons = len(
        rule_results_df
    )


    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - BUSINESS RULE SANITY CHECK"
    )

    print(
        "=" * 70
    )


    print(
        f"\nDeterministic assignment matches: "
        f"{deterministic_match_count}"
    )


    print(
        "Rule-based destination comparisons "
        "per assignment: 12"
    )


    print(
        f"Expected rule-based comparisons: "
        f"{expected_rule_comparisons}"
    )


    print(
        f"Actual rule-based comparisons: "
        f"{actual_rule_comparisons}"
    )


    if (
        actual_rule_comparisons
        ==
        expected_rule_comparisons
    ):

        print(
            "\nBusiness-rule comparison count is correct."
        )

    else:

        print(
            "\nWARNING: Business-rule comparison count "
            "does not match expected count."
        )


    # ========================================================
    # STEP 7
    # CURRENT DETERMINISTIC SUMMARY
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - CURRENT DETERMINISTIC VERDICT SUMMARY"
    )

    print(
        "=" * 70
    )


    print(
        "\nDIRECT FIELD RESULTS"
    )

    print(
        "-" * 70
    )


    for (
        verdict,
        count,
    ) in (
        comparison_df[
            "verdict"
        ]
        .value_counts()
        .items()
    ):

        print(
            f"{verdict}: {count}"
        )


    print(
        "\nRULE-BASED RESULTS"
    )

    print(
        "-" * 70
    )


    for (
        verdict,
        count,
    ) in (
        rule_results_df[
            "verdict"
        ]
        .value_counts()
        .items()
    ):

        print(
            f"{verdict}: {count}"
        )


    # ========================================================
    # STEP 8
    # DIAGNOSTIC OUTPUT
    # ========================================================

    preview_rule_debug_data(

        source_df=
            source_df,

        raw_job_details_df=
            raw_job_details_df,

        job_details_df=
            job_details_df,

        destination_df=
            destination_df,

        assignment_matches_df=
            assignment_matches_df,
    )


    # ========================================================
    # STEP 9A
    # BUILD UNIFIED FINAL REPORT
    # ========================================================

    final_report_df = (
        build_final_report(

            comparison_df=
                comparison_df,

            rule_results_df=
                rule_results_df,

            assignment_matches_df=
                assignment_matches_df,
        )
    )


    # ========================================================
    # STEP 9B
    # INVESTIGATION VIEW
    # ========================================================

    investigation_df = (
        build_investigation_report(

            final_report_df=
                final_report_df,
        )
    )


    # ========================================================
    # STEP 9C
    # AI QUEUE
    # ========================================================

    ai_queue_df = (
        build_ai_queue(

            final_report_df=
                final_report_df,
        )
    )


    # ========================================================
    # STEP 9D
    # FINAL REPORT SANITY CHECK
    # ========================================================

    structural_issue_count = len(

        assignment_matches_df[

            assignment_matches_df[
                "assignment_match_status"
            ]
            !=
            "MATCHED"

        ]

    )


    expected_report_rows = (
        len(
            comparison_df
        )
        +
        len(
            rule_results_df
        )
        +
        structural_issue_count
    )


    actual_report_rows = len(
        final_report_df
    )


    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - FINAL REPORT SANITY CHECK"
    )

    print(
        "=" * 70
    )


    print(
        f"\nDirect comparison rows: "
        f"{len(comparison_df)}"
    )


    print(
        f"Business-rule rows: "
        f"{len(rule_results_df)}"
    )


    print(
        f"Structural issue rows: "
        f"{structural_issue_count}"
    )


    print(
        f"Expected unified report rows: "
        f"{expected_report_rows}"
    )


    print(
        f"Actual unified report rows: "
        f"{actual_report_rows}"
    )


    if (
        expected_report_rows
        ==
        actual_report_rows
    ):

        print(
            "\nUnified report row count is correct."
        )

    else:

        print(
            "\nWARNING: Unified report row count does not "
            "match expected count."
        )


    # ========================================================
    # STEP 9E
    # PREVIEW FINAL REPORT
    # ========================================================

    preview_final_report(

        final_report_df=
            final_report_df,

        investigation_df=
            investigation_df,

        ai_queue_df=
            ai_queue_df,
    )


    # ========================================================
    # STEP 9F
    # EXPORT DETERMINISTIC REPORTS
    # ========================================================

    exported_files = (
        export_reports(

            final_report_df=
                final_report_df,

            investigation_df=
                investigation_df,

            ai_queue_df=
                ai_queue_df,

            output_dir=
                OUTPUT_DIR,
        )
    )


    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - EXPORTED REPORTS"
    )

    print(
        "=" * 70
    )


    for (
        report_name,
        report_path,
    ) in exported_files.items():

        print(
            f"{report_name}: {report_path}"
        )


    # ========================================================
    # STEP 10A
    # AI ANALYSIS OF AMBIGUOUS ASSIGNMENTS
    # ========================================================

    ambiguous_ai_df = (
        analyze_ambiguous_assignments(

            source_df=
                source_df,

            destination_df=
                destination_df,

            assignment_matches_df=
                assignment_matches_df,
        )
    )


    # ========================================================
    # STEP 10B
    # AI PRIORITIZATION OF ANOMALIES
    # ========================================================

    ai_priority_df = (
        prioritize_anomalies(

            final_report_df=
                final_report_df,
        )
    )


    # ========================================================
    # STEP 10C
    # AI PATTERN ANALYSIS
    # ========================================================

    ai_pattern_df = (
        summarize_anomaly_patterns(

            final_report_df=
                final_report_df,
        )
    )


    # ========================================================
    # STEP 10D
    # AI SANITY CHECK
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - AI SANITY CHECK"
    )

    print(
        "=" * 70
    )


    ambiguous_group_count = len(

        assignment_matches_df[

            assignment_matches_df[
                "assignment_match_status"
            ]
            ==
            "AMBIGUOUS_ASSIGNMENT_MATCH"

        ]

    )


    print(
        f"\nAmbiguous assignment groups: "
        f"{ambiguous_group_count}"
    )


    print(
        f"AI candidate-pair rows: "
        f"{len(ambiguous_ai_df)}"
    )


    print(
        f"AI employee priority rows: "
        f"{len(ai_priority_df)}"
    )


    print(
        f"AI pattern rows: "
        f"{len(ai_pattern_df)}"
    )


    # ========================================================
    # STEP 10E
    # PREVIEW AI ANALYSIS
    # ========================================================

    preview_ai_analysis(

        ambiguous_df=
            ambiguous_ai_df,

        priority_df=
            ai_priority_df,

        pattern_df=
            ai_pattern_df,
    )


    # ========================================================
    # STEP 10F
    # EXPORT AI ANALYSIS
    # ========================================================

    ai_exported_files = (
        export_ai_analysis(

            ambiguous_df=
                ambiguous_ai_df,

            priority_df=
                ai_priority_df,

            pattern_df=
                ai_pattern_df,

            excel_path=
                exported_files[
                    "excel"
                ],

            output_dir=
                OUTPUT_DIR,
        )
    )


    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - AI OUTPUTS"
    )

    print(
        "=" * 70
    )


    for (
        name,
        path,
    ) in ai_exported_files.items():

        print(
            f"{name}: {path}"
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    print(
        "\n"
        +
        "=" * 70
    )

    print(
        "CORROBORIA - PIPELINE COMPLETE"
    )

    print(
        "=" * 70
    )


    print(
        "\nCorroborIA completed successfully."
    )


    print(
        "The deterministic corroboration layer compared "
        "direct fields, applied supplied business rules "
        "and detected structural assignment issues."
    )


    print(
        "The unified report distinguishes CONFORME, "
        "ECART_JUSTIFIE, ANOMALIE and A_INVESTIGUER."
    )


    print(
        "Known anonymization limitations remain visible "
        "without being incorrectly sent to AI."
    )


    print(
        "The AI layer analyzed ambiguous assignment "
        "candidates using known deterministic matches."
    )


    print(
        "The AI layer also prioritized anomaly profiles "
        "and detected recurring discrepancy patterns."
    )


    print(
        "Deterministic verdicts were not overridden by AI."
    )


    print(
        "All reports were exported to the output directory."
    )


    print(
        "\nAI analysis completed successfully."
    )


    print(
        "=" * 70
    )
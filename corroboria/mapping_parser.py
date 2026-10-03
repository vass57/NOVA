# ============================================================
# CORROBORIA
# MAPPING PARSER
# ============================================================
#
# This module reads and structures Mapping.xlsx.
#
# IMPORTANT:
#
# It does NOT execute business rules.
#
# Its responsibilities are:
#
#   1. Clean mapping cells
#   2. Correctly recognize missing Excel values
#   3. Classify mapping rows
#   4. Parse supporting mapping worksheets
#   5. Validate direct mappings
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd


# ============================================================
# HELPER
# CHECK WHETHER A VALUE IS MISSING
# ============================================================

def is_missing(value) -> bool:
    """
    Return True when a mapping value should be considered empty.

    This is important because pandas may represent an empty
    Excel cell as:

        NaN

    rather than:

        None
    """

    # --------------------------------------------------------
    # NONE
    # --------------------------------------------------------

    if value is None:
        return True


    # --------------------------------------------------------
    # PANDAS / NUMPY MISSING VALUE
    # --------------------------------------------------------

    try:

        if pd.isna(value):
            return True

    except (
        TypeError,
        ValueError,
    ):

        pass


    # --------------------------------------------------------
    # TEXT REPRESENTATIONS OF MISSING VALUES
    # --------------------------------------------------------

    if isinstance(value, str):

        cleaned = value.strip().lower()

        if cleaned in {
            "",
            "nan",
            "none",
            "null",
        }:

            return True


    return False


# ============================================================
# HELPER
# CLEAN A MAPPING CELL
# ============================================================

def clean_mapping_cell(value):
    """
    Clean one Mapping.xlsx cell.

    Blank Excel cells become None.

    Text is stripped of leading/trailing spaces.

    IMPORTANT:

    We preserve:

        "-"
        "N/A"

    because they have meaning inside the mapping.
    """

    if is_missing(value):
        return None


    return str(value).strip()


# ============================================================
# HELPER
# CHECK WHETHER A RULE IS EMPTY
# ============================================================

def has_no_rule(rule_text) -> bool:
    """
    Determine whether a mapping row has no special business rule.

    Both a blank rule and N/A mean that no special rule needs
    to be interpreted.
    """

    if is_missing(rule_text):
        return True


    text = str(rule_text).strip().upper()


    return text in {
        "N/A",
        "NA",
    }


# ============================================================
# HELPER
# CHECK WHETHER A SOURCE FIELD REALLY EXISTS
# ============================================================

def has_source_field(source_field) -> bool:
    """
    Return True when the mapping contains an actual source field.

    A dash means that there is no direct System A field.
    """

    if is_missing(source_field):
        return False


    if str(source_field).strip() == "-":
        return False


    return True


# ============================================================
# HELPER
# CHECK WHETHER A DESTINATION FIELD REALLY EXISTS
# ============================================================

def has_destination_field(destination_field) -> bool:
    """
    Return True when the mapping contains an actual destination
    field.

    A dash means explicitly:

        not corroborated
    """

    if is_missing(destination_field):
        return False


    if str(destination_field).strip() == "-":
        return False


    return True


# ============================================================
# CLASSIFY ONE MAPPING ROW
# ============================================================

def classify_mapping_row(
    source_field,
    destination_field,
    rule_text,
):
    """
    Classify one row from Mapping.xlsx.

    Possible classifications:

        DIRECT

            A System A field directly corresponds to a
            System B field.

            Example:

                PrénomUsuel -> givenName


        RULE_BASED

            The System B value must be calculated or validated
            using business logic.


        SUPPORTING_SOURCE

            A System A field contributes to another business
            rule but does not directly map to System B.


        RULE_CONTINUATION

            The Excel row contains additional business-rule
            text belonging to a previous mapping.


        NOT_CORROBORATED

            Mapping.xlsx explicitly contains "-"


        CONTEXT

            Informational row not directly usable as a field
            mapping.
    """

    # Clean everything first.
    source_field = clean_mapping_cell(
        source_field
    )

    destination_field = clean_mapping_cell(
        destination_field
    )

    rule_text = clean_mapping_cell(
        rule_text
    )


    # ========================================================
    # EXPLICITLY NOT CORROBORATED
    # ========================================================
    #
    # Destination "-" is the clearest signal.
    #
    if destination_field == "-":

        return "NOT_CORROBORATED"


    # ========================================================
    # DETERMINE WHETHER ACTUAL FIELDS EXIST
    # ========================================================

    source_exists = has_source_field(
        source_field
    )

    destination_exists = has_destination_field(
        destination_field
    )


    # ========================================================
    # SOURCE + DESTINATION
    # ========================================================

    if (
        source_exists
        and destination_exists
    ):

        # No special rule means a normal direct mapping.
        if has_no_rule(rule_text):

            return "DIRECT"


        # Otherwise the relationship requires business logic.
        return "RULE_BASED"


    # ========================================================
    # DESTINATION BUT NO DIRECT SOURCE
    # ========================================================
    #
    # Example:
    #
    # detailedStatus
    #
    # may depend on multiple System A values and lookup tables.
    #
    if (
        not source_exists
        and destination_exists
    ):

        return "RULE_BASED"


    # ========================================================
    # SOURCE BUT NO DESTINATION
    # ========================================================
    #
    # This source field probably participates in another rule.
    #
    if (
        source_exists
        and not destination_exists
    ):

        return "SUPPORTING_SOURCE"


    # ========================================================
    # RULE TEXT ONLY
    # ========================================================

    if not has_no_rule(rule_text):

        return "RULE_CONTINUATION"


    # ========================================================
    # OTHERWISE
    # ========================================================

    return "CONTEXT"


# ============================================================
# PARSE MAIN MAPPING SHEET
# ============================================================

def parse_mapping_sheet(
    mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Parse and clean the main Mapping worksheet.

    Original columns:

        Description

        Champ fichier
        Système A - RH

        Champs fichier
        Système B - Temps

        Règles


    Clean columns:

        mapping_row
        description
        source_field
        destination_field
        rule_text
        row_type
    """

    df = mapping_df.copy()


    # ========================================================
    # VERIFY STRUCTURE
    # ========================================================

    if len(df.columns) < 4:

        raise ValueError(
            "The Mapping worksheet must contain "
            "at least 4 columns."
        )


    # ========================================================
    # KEEP FIRST FOUR COLUMNS
    # ========================================================
    #
    # We deliberately use column position because the original
    # headers contain line breaks and spaces.
    #
    df = df.iloc[
        :,
        :4,
    ].copy()


    # ========================================================
    # RENAME COLUMNS
    # ========================================================

    df.columns = [
        "description",
        "source_field",
        "destination_field",
        "rule_text",
    ]


    # ========================================================
    # SAVE ORIGINAL EXCEL ROW NUMBER
    # ========================================================
    #
    # DataFrame index 0 corresponds to Excel row 2 because
    # row 1 contains column headers.
    #
    df.insert(
        0,
        "mapping_row",
        df.index + 2,
    )


    # ========================================================
    # CLEAN EACH CELL
    # ========================================================

    clean_columns = [
        "description",
        "source_field",
        "destination_field",
        "rule_text",
    ]


    for column in clean_columns:

        df[column] = (
            df[column]
            .apply(
                clean_mapping_cell
            )
        )


    # ========================================================
    # REMOVE COMPLETELY EMPTY ROWS
    # ========================================================

    def row_has_information(row):

        return any(
            not is_missing(
                row[column]
            )
            for column in clean_columns
        )


    df = df[
        df.apply(
            row_has_information,
            axis=1,
        )
    ].copy()


    # ========================================================
    # CLASSIFY EACH ROW
    # ========================================================

    df[
        "row_type"
    ] = df.apply(

        lambda row:
            classify_mapping_row(

                source_field=
                    row[
                        "source_field"
                    ],

                destination_field=
                    row[
                        "destination_field"
                    ],

                rule_text=
                    row[
                        "rule_text"
                    ],
            ),

        axis=1,
    )


    # Reset index after removing empty rows.
    df = df.reset_index(
        drop=True
    )


    return df


# ============================================================
# PARSE EMPLOYMENT STATUS RULES
# ============================================================

def parse_employment_rules(
    employment_rules_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean:

        Règles situation d'emploi

    These rules are only parsed here.

    They are NOT executed yet.
    """

    df = employment_rules_df.copy()


    if len(df.columns) < 4:

        raise ValueError(
            "The employment-rules worksheet "
            "must contain at least 4 columns."
        )


    df = df.iloc[
        :,
        :4,
    ].copy()


    df.columns = [
        "access_status_codes",
        "specific_status",
        "cad_rule",
        "cadp_rule",
    ]


    for column in df.columns:

        df[column] = (
            df[column]
            .apply(
                clean_mapping_cell
            )
        )


    return df


# ============================================================
# PARSE JOIN-DEFINITION SHEET
# ============================================================

def parse_join_sheet(
    join_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean a mapping join-definition worksheet.

    Original columns:

        Source SIGRH
        Mapping

    New columns:

        source_field_description
        mapping_instruction
    """

    df = join_df.copy()


    if len(df.columns) < 2:

        raise ValueError(
            "Join worksheet must contain "
            "at least 2 columns."
        )


    df = df.iloc[
        :,
        :2,
    ].copy()


    df.columns = [
        "source_field_description",
        "mapping_instruction",
    ]


    for column in df.columns:

        df[column] = (
            df[column]
            .apply(
                clean_mapping_cell
            )
        )


    return df


# ============================================================
# VALIDATE DIRECT MAPPINGS
# ============================================================

def validate_direct_mappings(
    parsed_mapping_df: pd.DataFrame,
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Verify that DIRECT mapping fields actually exist.

    Example:

        PrénomUsuel -> givenName

    requires:

        PrénomUsuel
            exists in System A

        givenName
            exists in System B
    """

    issues = []


    # ========================================================
    # SELECT DIRECT MAPPINGS ONLY
    # ========================================================

    direct_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "DIRECT"
    ]


    # ========================================================
    # VALIDATE EACH ONE
    # ========================================================

    for _, row in direct_rows.iterrows():

        source_field = (
            row[
                "source_field"
            ]
        )

        destination_field = (
            row[
                "destination_field"
            ]
        )


        # ----------------------------------------------------
        # SYSTEM A FIELD
        # ----------------------------------------------------

        if source_field not in source_df.columns:

            issues.append(
                {
                    "mapping_row":
                        row[
                            "mapping_row"
                        ],

                    "side":
                        "SYSTEM_A",

                    "field":
                        source_field,

                    "problem":
                        "Field does not exist "
                        "in System A",
                }
            )


        # ----------------------------------------------------
        # SYSTEM B FIELD
        # ----------------------------------------------------

        if destination_field not in destination_df.columns:

            issues.append(
                {
                    "mapping_row":
                        row[
                            "mapping_row"
                        ],

                    "side":
                        "SYSTEM_B",

                    "field":
                        destination_field,

                    "problem":
                        "Field does not exist "
                        "in System B",
                }
            )


    return pd.DataFrame(
        issues,
        columns=[
            "mapping_row",
            "side",
            "field",
            "problem",
        ],
    )


# ============================================================
# DISPLAY HELPER
# ============================================================

def display_mapping_value(value):
    """
    Create a clean value for console output.

    Missing values display as:

        -

    rather than:

        nan
    """

    if is_missing(value):
        return "-"


    return str(value)


# ============================================================
# PREVIEW MAPPING ANALYSIS
# ============================================================

def preview_mapping_analysis(
    parsed_mapping_df: pd.DataFrame,
    employment_rules_df: pd.DataFrame,
    job_join_df: pd.DataFrame,
    employment_reason_join_df: pd.DataFrame,
    validation_issues_df: pd.DataFrame,
) -> None:
    """
    Display a readable analysis of Mapping.xlsx.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - MAPPING ANALYSIS"
    )

    print(
        "=" * 70
    )


    # ========================================================
    # COUNTS
    # ========================================================

    print(
        "\nMapping row types:"
    )

    print(
        "-" * 70
    )


    counts = (
        parsed_mapping_df[
            "row_type"
        ]
        .value_counts()
    )


    for row_type, count in counts.items():

        print(
            f"{row_type}: {count}"
        )


    # ========================================================
    # DIRECT MAPPINGS
    # ========================================================

    print(
        "\nDIRECT FIELD MAPPINGS"
    )

    print(
        "-" * 70
    )


    direct_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "DIRECT"
    ]


    if direct_rows.empty:

        print(
            "No direct mappings detected."
        )


    for _, row in direct_rows.iterrows():

        print(
            f"Excel row "
            f"{row['mapping_row']}: "
            f"{display_mapping_value(row['source_field'])} "
            f"-> "
            f"{display_mapping_value(row['destination_field'])}"
        )


    # ========================================================
    # RULE-BASED MAPPINGS
    # ========================================================

    print(
        "\nRULE-BASED DESTINATION FIELDS"
    )

    print(
        "-" * 70
    )


    rule_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "RULE_BASED"
    ]


    if rule_rows.empty:

        print(
            "No rule-based mappings detected."
        )


    for _, row in rule_rows.iterrows():

        print(
            f"Excel row "
            f"{row['mapping_row']}: "
            f"{display_mapping_value(row['description'])}"
        )


        print(
            "    Source: "
            f"{display_mapping_value(row['source_field'])}"
        )


        print(
            "    Destination: "
            f"{display_mapping_value(row['destination_field'])}"
        )


    # ========================================================
    # SUPPORTING SOURCE FIELDS
    # ========================================================

    print(
        "\nSUPPORTING SOURCE FIELDS"
    )

    print(
        "-" * 70
    )


    support_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "SUPPORTING_SOURCE"
    ]


    if support_rows.empty:

        print(
            "No supporting source fields detected."
        )


    for _, row in support_rows.iterrows():

        print(
            f"Excel row "
            f"{row['mapping_row']}: "
            f"{display_mapping_value(row['source_field'])}"
        )


    # ========================================================
    # RULE CONTINUATIONS
    # ========================================================

    print(
        "\nRULE CONTINUATION ROWS"
    )

    print(
        "-" * 70
    )


    continuation_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "RULE_CONTINUATION"
    ]


    if continuation_rows.empty:

        print(
            "No rule continuation rows detected."
        )


    for _, row in continuation_rows.iterrows():

        print(
            f"Excel row "
            f"{row['mapping_row']}: "
            f"{display_mapping_value(row['rule_text'])}"
        )


    # ========================================================
    # NOT CORROBORATED
    # ========================================================

    print(
        "\nEXPLICITLY NOT CORROBORATED"
    )

    print(
        "-" * 70
    )


    ignored_rows = parsed_mapping_df[
        parsed_mapping_df[
            "row_type"
        ] == "NOT_CORROBORATED"
    ]


    if ignored_rows.empty:

        print(
            "No explicitly ignored fields detected."
        )


    for _, row in ignored_rows.iterrows():

        print(
            f"Excel row "
            f"{row['mapping_row']}: "
            f"{display_mapping_value(row['source_field'])} "
            f"-> -"
        )


    # ========================================================
    # DIRECT VALIDATION
    # ========================================================

    print(
        "\nDIRECT MAPPING VALIDATION"
    )

    print(
        "-" * 70
    )


    # Number of direct mappings actually checked.
    direct_count = len(
        direct_rows
    )


    print(
        f"Direct mappings checked: {direct_count}"
    )


    if direct_count == 0:

        print(
            "WARNING: No direct mappings were detected."
        )


    elif validation_issues_df.empty:

        print(
            "All direct mappings reference valid "
            "System A and System B columns."
        )


    else:

        print(
            validation_issues_df.to_string(
                index=False
            )
        )


    # ========================================================
    # EMPLOYMENT STATUS RULES
    # ========================================================

    print(
        "\nEMPLOYMENT STATUS RULE TABLE"
    )

    print(
        "-" * 70
    )


    print(
        employment_rules_df.to_string(
            index=False
        )
    )


    # ========================================================
    # JOB DETAIL JOINS
    # ========================================================

    print(
        "\nJOB DETAIL JOIN DEFINITIONS"
    )

    print(
        "-" * 70
    )


    print(
        job_join_df.to_string(
            index=False
        )
    )


    # ========================================================
    # EMPLOYMENT REASON JOINS
    # ========================================================

    print(
        "\nEMPLOYMENT REASON JOIN DEFINITIONS"
    )

    print(
        "-" * 70
    )


    print(
        employment_reason_join_df.to_string(
            index=False
        )
    )
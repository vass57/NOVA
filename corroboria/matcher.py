# ============================================================
# CORROBORIA
# EMPLOYEE MATCHER
# ============================================================
#
# PURPOSE
#
# Match employees between:
#
#     System A - RH
#
# and:
#
#     System B - Temps
#
#
# Employee identifier mapping:
#
#     System A: Matricule
#     System B: personId
#
#
# IMPORTANT:
#
# One employee can appear on MULTIPLE rows.
#
# That does NOT automatically mean duplicate data.
#
# Those rows may represent:
#
#     primary assignments
#     temporary assignments
#     secondary assignments
#
# Assignment matching will be performed in a later step.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

def validate_employee_id_columns(
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
) -> None:
    """
    Verify that the employee identifier columns exist.

    System A must contain:

        Matricule

    System B must contain:

        personId
    """

    if "Matricule" not in source_df.columns:

        raise ValueError(
            "System A does not contain the required "
            "'Matricule' column."
        )


    if "personId" not in destination_df.columns:

        raise ValueError(
            "System B does not contain the required "
            "'personId' column."
        )


# ============================================================
# FIND ROWS WITH MISSING EMPLOYEE IDs
# ============================================================

def find_missing_employee_ids(
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Find rows where an employee identifier is missing.

    This is important because a row without an employee ID
    cannot safely be matched to the other system.

    Returns:

        source_missing_ids
        destination_missing_ids
    """

    # --------------------------------------------------------
    # SYSTEM A
    # --------------------------------------------------------

    source_missing_ids = source_df[
        source_df["Matricule"].isna()
    ].copy()


    # --------------------------------------------------------
    # SYSTEM B
    # --------------------------------------------------------

    destination_missing_ids = destination_df[
        destination_df["personId"].isna()
    ].copy()


    return (
        source_missing_ids,
        destination_missing_ids,
    )


# ============================================================
# BUILD EMPLOYEE INDEX
# ============================================================

def build_employee_index(
    df: pd.DataFrame,
    employee_id_column: str,
    count_column_name: str,
    indices_column_name: str,
) -> pd.DataFrame:
    """
    Create one summary row per unique employee.

    Example input:

        Matricule
        ---------
        1545850
        1545850
        9989151

    becomes something like:

        employee_id   row_count   row_indices
        -------------------------------------
        1545850       2           [0, 1]
        9989151       1           [2]


    IMPORTANT:

    row_count > 1 does NOT mean duplicate employee.

    It means:

        this employee has multiple candidate rows

    Assignment matching will decide what those rows represent.
    """

    # --------------------------------------------------------
    # IGNORE ROWS WITHOUT EMPLOYEE ID
    # --------------------------------------------------------

    valid_df = df[
        df[employee_id_column].notna()
    ].copy()


    # --------------------------------------------------------
    # CREATE ONE RECORD PER EMPLOYEE
    # --------------------------------------------------------

    records = []


    for employee_id, group in valid_df.groupby(
        employee_id_column,
        sort=False,
    ):

        records.append(
            {
                "employee_id":
                    employee_id,

                count_column_name:
                    len(group),

                indices_column_name:
                    list(group.index),
            }
        )


    return pd.DataFrame(
        records,
        columns=[
            "employee_id",
            count_column_name,
            indices_column_name,
        ],
    )


# ============================================================
# MATCH EMPLOYEES
# ============================================================

def match_employees(
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match employees between System A and System B.

    Matching key:

        Matricule == personId


    Possible employee_match_status values:

        BOTH

            Employee exists in both systems.


        SOURCE_ONLY

            Employee exists in System A but not System B.


        DESTINATION_ONLY

            Employee exists in System B but not System A.


    The result also records how many rows belong to each
    employee in each system.
    """

    # ========================================================
    # VERIFY COLUMNS
    # ========================================================

    validate_employee_id_columns(
        source_df=source_df,
        destination_df=destination_df,
    )


    # ========================================================
    # BUILD SYSTEM A EMPLOYEE INDEX
    # ========================================================

    source_index = build_employee_index(

        df=source_df,

        employee_id_column=
            "Matricule",

        count_column_name=
            "source_row_count",

        indices_column_name=
            "source_row_indices",
    )


    # ========================================================
    # BUILD SYSTEM B EMPLOYEE INDEX
    # ========================================================

    destination_index = build_employee_index(

        df=destination_df,

        employee_id_column=
            "personId",

        count_column_name=
            "destination_row_count",

        indices_column_name=
            "destination_row_indices",
    )


    # ========================================================
    # OUTER JOIN
    # ========================================================
    #
    # Outer join is VERY important.
    #
    # It preserves:
    #
    #     employees found in both systems
    #
    #     employees only in System A
    #
    #     employees only in System B
    #
    employee_matches = source_index.merge(

        destination_index,

        on="employee_id",

        how="outer",

        indicator=True,
    )


    # ========================================================
    # TRANSLATE MERGE STATUS
    # ========================================================

    merge_status_mapping = {

        "both":
            "BOTH",

        "left_only":
            "SOURCE_ONLY",

        "right_only":
            "DESTINATION_ONLY",
    }


    employee_matches[
        "employee_match_status"
    ] = (
        employee_matches[
            "_merge"
        ]
        .map(
            merge_status_mapping
        )
    )


    # We no longer need pandas' internal merge column.
    employee_matches = (
        employee_matches
        .drop(
            columns=[
                "_merge"
            ]
        )
    )


    # ========================================================
    # REPLACE MISSING COUNTS WITH ZERO
    # ========================================================

    employee_matches[
        "source_row_count"
    ] = (
        employee_matches[
            "source_row_count"
        ]
        .fillna(0)
        .astype(int)
    )


    employee_matches[
        "destination_row_count"
    ] = (
        employee_matches[
            "destination_row_count"
        ]
        .fillna(0)
        .astype(int)
    )


    # ========================================================
    # INDICATE WHETHER ASSIGNMENT MATCHING IS NEEDED
    # ========================================================
    #
    # If either system contains multiple rows for an employee,
    # we will later need to determine which assignment belongs
    # with which assignment.
    #
    employee_matches[
        "needs_assignment_matching"
    ] = (

        (
            employee_matches[
                "source_row_count"
            ] > 1
        )

        |

        (
            employee_matches[
                "destination_row_count"
            ] > 1
        )
    )


    # ========================================================
    # SORT RESULT
    # ========================================================

    employee_matches = (
        employee_matches
        .sort_values(
            by=[
                "employee_id"
            ]
        )
        .reset_index(
            drop=True
        )
    )


    return employee_matches


# ============================================================
# PREVIEW EMPLOYEE MATCHING
# ============================================================

def preview_employee_matching(
    employee_matches_df: pd.DataFrame,
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    source_missing_ids_df: pd.DataFrame,
    destination_missing_ids_df: pd.DataFrame,
) -> None:
    """
    Print a readable employee-matching summary.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - EMPLOYEE MATCHING"
    )

    print(
        "=" * 70
    )


    # ========================================================
    # ORIGINAL ROW COUNTS
    # ========================================================

    print(
        f"\nSystem A rows: "
        f"{len(source_df)}"
    )

    print(
        f"System B rows: "
        f"{len(destination_df)}"
    )


    # ========================================================
    # UNIQUE EMPLOYEE COUNTS
    # ========================================================

    source_unique = (
        source_df[
            "Matricule"
        ]
        .dropna()
        .nunique()
    )


    destination_unique = (
        destination_df[
            "personId"
        ]
        .dropna()
        .nunique()
    )


    print(
        f"\nUnique employees in System A: "
        f"{source_unique}"
    )

    print(
        f"Unique employees in System B: "
        f"{destination_unique}"
    )


    # ========================================================
    # MATCH STATUS COUNTS
    # ========================================================

    print(
        "\nEMPLOYEE MATCH STATUS"
    )

    print(
        "-" * 70
    )


    status_counts = (
        employee_matches_df[
            "employee_match_status"
        ]
        .value_counts()
    )


    for status, count in status_counts.items():

        print(
            f"{status}: {count}"
        )


    # ========================================================
    # MISSING EMPLOYEE IDS
    # ========================================================

    print(
        "\nROWS WITH MISSING EMPLOYEE IDs"
    )

    print(
        "-" * 70
    )


    print(
        "System A missing Matricule: "
        f"{len(source_missing_ids_df)}"
    )


    print(
        "System B missing personId: "
        f"{len(destination_missing_ids_df)}"
    )


    # ========================================================
    # EMPLOYEES ONLY IN SYSTEM A
    # ========================================================

    source_only = employee_matches_df[
        employee_matches_df[
            "employee_match_status"
        ] == "SOURCE_ONLY"
    ]


    print(
        "\nEMPLOYEES ONLY IN SYSTEM A"
    )

    print(
        "-" * 70
    )


    if source_only.empty:

        print(
            "None."
        )

    else:

        print(
            source_only[
                [
                    "employee_id",
                    "source_row_count",
                    "source_row_indices",
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # EMPLOYEES ONLY IN SYSTEM B
    # ========================================================

    destination_only = employee_matches_df[
        employee_matches_df[
            "employee_match_status"
        ] == "DESTINATION_ONLY"
    ]


    print(
        "\nEMPLOYEES ONLY IN SYSTEM B"
    )

    print(
        "-" * 70
    )


    if destination_only.empty:

        print(
            "None."
        )

    else:

        print(
            destination_only[
                [
                    "employee_id",
                    "destination_row_count",
                    "destination_row_indices",
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # EMPLOYEES NEEDING ASSIGNMENT MATCHING
    # ========================================================

    assignment_candidates = employee_matches_df[
        (
            employee_matches_df[
                "employee_match_status"
            ] == "BOTH"
        )

        &

        (
            employee_matches_df[
                "needs_assignment_matching"
            ]
        )
    ]


    print(
        "\nEMPLOYEES NEEDING ASSIGNMENT MATCHING"
    )

    print(
        "-" * 70
    )


    if assignment_candidates.empty:

        print(
            "None."
        )

    else:

        print(
            assignment_candidates[
                [
                    "employee_id",
                    "source_row_count",
                    "destination_row_count",
                    "source_row_indices",
                    "destination_row_indices",
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # FULL MATCH TABLE
    # ========================================================

    print(
        "\nEMPLOYEE MATCH TABLE"
    )

    print(
        "-" * 70
    )


    print(
        employee_matches_df[
            [
                "employee_id",
                "source_row_count",
                "destination_row_count",
                "employee_match_status",
                "needs_assignment_matching",
            ]
        ].to_string(
            index=False
        )
    )
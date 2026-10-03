# ============================================================
# CORROBORIA
# ASSIGNMENT MATCHER
# ============================================================
#
# PURPOSE
#
# Match employee assignment rows between:
#
#     System A - RH
#
# and:
#
#     System B - Temps
#
#
# IMPORTANT DESIGN RULE:
#
# We only use assignment type to create deterministic matches.
#
# We DO NOT use:
#
#     positionId
#     positionCode
#     dates
#     division
#
# to force assignment matches because those fields will later
# be corroborated themselves.
#
#
# SYSTEM A
#
#     TypeAffectation
#
#         P = Primary
#         A = Temporary
#         S = Secondary
#
#
# SYSTEM B
#
#     isPrimaryAssignment
#     isTemporaryAssignment
#
#
# Conversion:
#
#     True,  False -> P
#     False, True  -> A
#     False, False -> S
#
#
#     True, True   -> INVALID
#
# Missing values produce:
#
#     UNKNOWN
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd


# ============================================================
# SOURCE ASSIGNMENT TYPE
# ============================================================

def get_source_assignment_type(value):
    """
    Convert System A TypeAffectation into a standard code.

    Expected values:

        P
        A
        S

    Anything else becomes UNKNOWN.
    """

    if value is None:
        return "UNKNOWN"


    try:

        if pd.isna(value):
            return "UNKNOWN"

    except (
        TypeError,
        ValueError,
    ):

        pass


    value = str(
        value
    ).strip().upper()


    if value in {
        "P",
        "A",
        "S",
    }:

        return value


    return "UNKNOWN"


# ============================================================
# DESTINATION ASSIGNMENT TYPE
# ============================================================

def get_destination_assignment_type(
    is_primary,
    is_temporary,
):
    """
    Convert System B assignment flags into P / A / S.

    Rules:

        primary=True
        temporary=False
            -> P


        primary=False
        temporary=True
            -> A


        primary=False
        temporary=False
            -> S


        primary=True
        temporary=True
            -> INVALID


        missing flag
            -> UNKNOWN
    """

    # ========================================================
    # MISSING VALUES
    # ========================================================

    if (
        is_primary is None
        or is_temporary is None
    ):

        return "UNKNOWN"


    try:

        if (
            pd.isna(is_primary)
            or pd.isna(is_temporary)
        ):

            return "UNKNOWN"

    except (
        TypeError,
        ValueError,
    ):

        pass


    # ========================================================
    # PRIMARY
    # ========================================================

    if (
        bool(is_primary) is True
        and bool(is_temporary) is False
    ):

        return "P"


    # ========================================================
    # TEMPORARY
    # ========================================================

    if (
        bool(is_primary) is False
        and bool(is_temporary) is True
    ):

        return "A"


    # ========================================================
    # SECONDARY
    # ========================================================

    if (
        bool(is_primary) is False
        and bool(is_temporary) is False
    ):

        return "S"


    # ========================================================
    # IMPOSSIBLE / INVALID COMBINATION
    # ========================================================

    if (
        bool(is_primary) is True
        and bool(is_temporary) is True
    ):

        return "INVALID"


    return "UNKNOWN"


# ============================================================
# ADD ASSIGNMENT TYPE TO SYSTEM A
# ============================================================

def add_source_assignment_type(
    source_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add an internal normalized assignment type to System A.
    """

    if "TypeAffectation" not in source_df.columns:

        raise ValueError(
            "System A is missing TypeAffectation."
        )


    df = source_df.copy()


    df[
        "_assignment_type"
    ] = (
        df[
            "TypeAffectation"
        ]
        .apply(
            get_source_assignment_type
        )
    )


    return df


# ============================================================
# ADD ASSIGNMENT TYPE TO SYSTEM B
# ============================================================

def add_destination_assignment_type(
    destination_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add an internal normalized assignment type to System B.
    """

    required_columns = [
        "isPrimaryAssignment",
        "isTemporaryAssignment",
    ]


    for column in required_columns:

        if column not in destination_df.columns:

            raise ValueError(
                f"System B is missing {column}."
            )


    df = destination_df.copy()


    df[
        "_assignment_type"
    ] = df.apply(

        lambda row:
            get_destination_assignment_type(

                row[
                    "isPrimaryAssignment"
                ],

                row[
                    "isTemporaryAssignment"
                ],
            ),

        axis=1,
    )


    return df


# ============================================================
# CREATE MATCH RESULT
# ============================================================

def create_match_record(
    employee_id,
    assignment_type,
    status,
    source_row_index=None,
    destination_row_index=None,
    source_candidate_indices=None,
    destination_candidate_indices=None,
    explanation=None,
):
    """
    Build one standardized assignment matching result.
    """

    return {

        "employee_id":
            employee_id,

        "assignment_type":
            assignment_type,

        "source_row_index":
            source_row_index,

        "destination_row_index":
            destination_row_index,

        "source_candidate_indices":
            source_candidate_indices
            if source_candidate_indices is not None
            else [],

        "destination_candidate_indices":
            destination_candidate_indices
            if destination_candidate_indices is not None
            else [],

        "assignment_match_status":
            status,

        "match_method":
            (
                "EMPLOYEE_ID_AND_ASSIGNMENT_TYPE"
                if status == "MATCHED"
                else None
            ),

        "explanation":
            explanation,
    }


# ============================================================
# MATCH ASSIGNMENTS
# ============================================================

def match_assignments(
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    employee_matches_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match assignments conservatively.

    A deterministic match happens only when:

        one source assignment of a given type

    corresponds to:

        one destination assignment of that same type


    Example:

        Source:
            P

        Destination:
            P

        -> MATCHED


    Example:

        Source:
            S
            S

        Destination:
            S
            S

        -> AMBIGUOUS_ASSIGNMENT_MATCH


    We deliberately refuse to guess which secondary record
    belongs to which destination record.
    """

    # ========================================================
    # ADD STANDARDIZED ASSIGNMENT TYPES
    # ========================================================

    source_with_types = (
        add_source_assignment_type(
            source_df
        )
    )


    destination_with_types = (
        add_destination_assignment_type(
            destination_df
        )
    )


    results = []


    # ========================================================
    # PROCESS EMPLOYEES THAT EXIST IN BOTH SYSTEMS
    # ========================================================

    matched_employees = employee_matches_df[

        employee_matches_df[
            "employee_match_status"
        ] == "BOTH"

    ]


    for _, employee_row in matched_employees.iterrows():

        employee_id = (
            employee_row[
                "employee_id"
            ]
        )


        # ----------------------------------------------------
        # GET ALL SOURCE ROWS FOR THIS EMPLOYEE
        # ----------------------------------------------------

        employee_source = source_with_types[

            source_with_types[
                "Matricule"
            ] == employee_id

        ]


        # ----------------------------------------------------
        # GET ALL DESTINATION ROWS FOR THIS EMPLOYEE
        # ----------------------------------------------------

        employee_destination = destination_with_types[

            destination_with_types[
                "personId"
            ] == employee_id

        ]


        # ====================================================
        # HANDLE EACH KNOWN ASSIGNMENT TYPE
        # ====================================================

        for assignment_type in [
            "P",
            "A",
            "S",
        ]:

            source_candidates = employee_source[

                employee_source[
                    "_assignment_type"
                ] == assignment_type

            ]


            destination_candidates = employee_destination[

                employee_destination[
                    "_assignment_type"
                ] == assignment_type

            ]


            source_indices = list(
                source_candidates.index
            )


            destination_indices = list(
                destination_candidates.index
            )


            source_count = len(
                source_indices
            )


            destination_count = len(
                destination_indices
            )


            # =================================================
            # NOTHING EXISTS ON EITHER SIDE
            # =================================================

            if (
                source_count == 0
                and destination_count == 0
            ):

                continue


            # =================================================
            # UNIQUE DETERMINISTIC MATCH
            # =================================================

            if (
                source_count == 1
                and destination_count == 1
            ):

                results.append(

                    create_match_record(

                        employee_id=
                            employee_id,

                        assignment_type=
                            assignment_type,

                        status=
                            "MATCHED",

                        source_row_index=
                            source_indices[0],

                        destination_row_index=
                            destination_indices[0],

                        source_candidate_indices=
                            source_indices,

                        destination_candidate_indices=
                            destination_indices,

                        explanation=(
                            "Unique assignment of this type "
                            "exists in both systems."
                        ),
                    )
                )


                continue


            # =================================================
            # SOURCE ASSIGNMENT WITHOUT DESTINATION
            # =================================================

            if (
                source_count > 0
                and destination_count == 0
            ):

                for source_index in source_indices:

                    results.append(

                        create_match_record(

                            employee_id=
                                employee_id,

                            assignment_type=
                                assignment_type,

                            status=
                                "SOURCE_ONLY_ASSIGNMENT",

                            source_row_index=
                                source_index,

                            source_candidate_indices=
                                [
                                    source_index
                                ],

                            destination_candidate_indices=
                                [],

                            explanation=(
                                "Assignment exists in System A "
                                "but no assignment of the same "
                                "type exists in System B."
                            ),
                        )
                    )


                continue


            # =================================================
            # DESTINATION ASSIGNMENT WITHOUT SOURCE
            # =================================================

            if (
                source_count == 0
                and destination_count > 0
            ):

                for destination_index in destination_indices:

                    results.append(

                        create_match_record(

                            employee_id=
                                employee_id,

                            assignment_type=
                                assignment_type,

                            status=
                                "DESTINATION_ONLY_ASSIGNMENT",

                            destination_row_index=
                                destination_index,

                            source_candidate_indices=
                                [],

                            destination_candidate_indices=
                                [
                                    destination_index
                                ],

                            explanation=(
                                "Assignment exists in System B "
                                "but no assignment of the same "
                                "type exists in System A."
                            ),
                        )
                    )


                continue


            # =================================================
            # AMBIGUOUS GROUP
            # =================================================
            #
            # Example:
            #
            #   Source:
            #       S
            #       S
            #
            #   Destination:
            #       S
            #       S
            #
            # There is no deterministic way to know which
            # source secondary assignment corresponds to which
            # destination secondary assignment.
            #
            results.append(

                create_match_record(

                    employee_id=
                        employee_id,

                    assignment_type=
                        assignment_type,

                    status=
                        "AMBIGUOUS_ASSIGNMENT_MATCH",

                    source_candidate_indices=
                        source_indices,

                    destination_candidate_indices=
                        destination_indices,

                    explanation=(
                        "Multiple assignment rows of the same "
                        "type exist. CorroborIA refuses to force "
                        "a pairing using fields that must later "
                        "be audited."
                    ),
                )
            )


        # ====================================================
        # UNKNOWN / INVALID SOURCE ASSIGNMENT TYPES
        # ====================================================

        unusual_source = employee_source[

            ~employee_source[
                "_assignment_type"
            ].isin(
                [
                    "P",
                    "A",
                    "S",
                ]
            )

        ]


        for source_index, row in unusual_source.iterrows():

            results.append(

                create_match_record(

                    employee_id=
                        employee_id,

                    assignment_type=
                        row[
                            "_assignment_type"
                        ],

                    status=
                        "UNRESOLVED_ASSIGNMENT_TYPE",

                    source_row_index=
                        source_index,

                    source_candidate_indices=
                        [
                            source_index
                        ],

                    explanation=(
                        "System A assignment type could not "
                        "be interpreted as P, A or S."
                    ),
                )
            )


        # ====================================================
        # UNKNOWN / INVALID DESTINATION ASSIGNMENT TYPES
        # ====================================================

        unusual_destination = employee_destination[

            ~employee_destination[
                "_assignment_type"
            ].isin(
                [
                    "P",
                    "A",
                    "S",
                ]
            )

        ]


        for destination_index, row in unusual_destination.iterrows():

            results.append(

                create_match_record(

                    employee_id=
                        employee_id,

                    assignment_type=
                        row[
                            "_assignment_type"
                        ],

                    status=
                        "UNRESOLVED_ASSIGNMENT_TYPE",

                    destination_row_index=
                        destination_index,

                    destination_candidate_indices=
                        [
                            destination_index
                        ],

                    explanation=(
                        "System B assignment flags could not "
                        "be interpreted as a valid P, A or S "
                        "assignment type."
                    ),
                )
            )


    # ========================================================
    # CREATE RESULT DATAFRAME
    # ========================================================

    result_df = pd.DataFrame(
        results,
        columns=[
            "employee_id",
            "assignment_type",
            "source_row_index",
            "destination_row_index",
            "source_candidate_indices",
            "destination_candidate_indices",
            "assignment_match_status",
            "match_method",
            "explanation",
        ],
    )


    return result_df


# ============================================================
# PREVIEW ASSIGNMENT MATCHING
# ============================================================

def preview_assignment_matching(
    assignment_matches_df: pd.DataFrame,
) -> None:
    """
    Print a readable summary of assignment matching.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - ASSIGNMENT MATCHING"
    )

    print(
        "=" * 70
    )


    if assignment_matches_df.empty:

        print(
            "No assignment results were produced."
        )

        return


    # ========================================================
    # STATUS COUNTS
    # ========================================================

    print(
        "\nASSIGNMENT MATCH STATUS"
    )

    print(
        "-" * 70
    )


    status_counts = (

        assignment_matches_df[
            "assignment_match_status"
        ]
        .value_counts()

    )


    for status, count in status_counts.items():

        print(
            f"{status}: {count}"
        )


    # ========================================================
    # MATCHED ASSIGNMENTS
    # ========================================================

    print(
        "\nDETERMINISTIC MATCHES"
    )

    print(
        "-" * 70
    )


    matched = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "MATCHED"

    ]


    if matched.empty:

        print(
            "None."
        )

    else:

        print(

            matched[
                [
                    "employee_id",
                    "assignment_type",
                    "source_row_index",
                    "destination_row_index",
                    "match_method",
                ]
            ].to_string(
                index=False
            )

        )


    # ========================================================
    # SOURCE ONLY
    # ========================================================

    print(
        "\nSOURCE-ONLY ASSIGNMENTS"
    )

    print(
        "-" * 70
    )


    source_only = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "SOURCE_ONLY_ASSIGNMENT"

    ]


    if source_only.empty:

        print(
            "None."
        )

    else:

        print(

            source_only[
                [
                    "employee_id",
                    "assignment_type",
                    "source_row_index",
                ]
            ].to_string(
                index=False
            )

        )


    # ========================================================
    # DESTINATION ONLY
    # ========================================================

    print(
        "\nDESTINATION-ONLY ASSIGNMENTS"
    )

    print(
        "-" * 70
    )


    destination_only = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "DESTINATION_ONLY_ASSIGNMENT"

    ]


    if destination_only.empty:

        print(
            "None."
        )

    else:

        print(

            destination_only[
                [
                    "employee_id",
                    "assignment_type",
                    "destination_row_index",
                ]
            ].to_string(
                index=False
            )

        )


    # ========================================================
    # AMBIGUOUS
    # ========================================================

    print(
        "\nAMBIGUOUS ASSIGNMENT GROUPS"
    )

    print(
        "-" * 70
    )


    ambiguous = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "AMBIGUOUS_ASSIGNMENT_MATCH"

    ]


    if ambiguous.empty:

        print(
            "None."
        )

    else:

        print(

            ambiguous[
                [
                    "employee_id",
                    "assignment_type",
                    "source_candidate_indices",
                    "destination_candidate_indices",
                ]
            ].to_string(
                index=False
            )

        )


    # ========================================================
    # UNRESOLVED TYPES
    # ========================================================

    print(
        "\nUNRESOLVED ASSIGNMENT TYPES"
    )

    print(
        "-" * 70
    )


    unresolved = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "UNRESOLVED_ASSIGNMENT_TYPE"

    ]


    if unresolved.empty:

        print(
            "None."
        )

    else:

        print(

            unresolved[
                [
                    "employee_id",
                    "assignment_type",
                    "source_row_index",
                    "destination_row_index",
                ]
            ].to_string(
                index=False
            )

        )
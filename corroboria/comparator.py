# ============================================================
# CORROBORIA
# DIRECT FIELD COMPARATOR
# ============================================================
#
# PURPOSE
#
# Compare fields that Mapping.xlsx identifies as DIRECT.
#
#
# IMPORTANT:
#
# This module DOES NOT execute business rules.
#
# It performs:
#
#     raw comparison
#     normalized comparison
#
#
# Possible comparison statuses:
#
#     EXACT_MATCH
#
#         Raw values are already equivalent.
#
#
#     NORMALIZED_MATCH
#
#         Raw values differ, but normalization proves that
#         they represent the same value.
#
#
#     DISCREPANCY
#
#         Normalized values are different.
#
#
# A discrepancy is NOT automatically an anomaly.
#
# Business rules will be applied later.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd


# ============================================================
# MISSING VALUE HELPER
# ============================================================

def is_missing(value) -> bool:
    """
    Return True when a value should be treated as missing.
    """

    if value is None:
        return True


    try:

        if pd.isna(value):
            return True

    except (
        TypeError,
        ValueError,
    ):

        pass


    return False


# ============================================================
# SAFE VALUE COMPARISON
# ============================================================

def values_equal(
    left,
    right,
) -> bool:
    """
    Compare two values safely.

    Rules:

        missing == missing
            True

        missing != value
            False

        otherwise
            normal Python equality
    """

    left_missing = is_missing(
        left
    )

    right_missing = is_missing(
        right
    )


    # --------------------------------------------------------
    # BOTH MISSING
    # --------------------------------------------------------

    if (
        left_missing
        and right_missing
    ):

        return True


    # --------------------------------------------------------
    # ONLY ONE MISSING
    # --------------------------------------------------------

    if (
        left_missing
        != right_missing
    ):

        return False


    # --------------------------------------------------------
    # NORMAL COMPARISON
    # --------------------------------------------------------

    try:

        return bool(
            left == right
        )

    except (
        TypeError,
        ValueError,
    ):

        return False


# ============================================================
# FORMAT VALUE FOR EXPLANATION
# ============================================================

def display_value(value) -> str:
    """
    Convert a value into readable text for explanations.
    """

    if is_missing(value):

        return "<VIDE>"


    return repr(
        value
    )


# ============================================================
# CLASSIFY ONE COMPARISON
# ============================================================

def classify_comparison(
    source_raw,
    destination_raw,
    source_normalized,
    destination_normalized,
):
    """
    Determine whether two mapped values are:

        EXACT_MATCH
        NORMALIZED_MATCH
        DISCREPANCY
    """

    # ========================================================
    # RAW COMPARISON
    # ========================================================

    raw_equal = values_equal(
        source_raw,
        destination_raw,
    )


    # ========================================================
    # NORMALIZED COMPARISON
    # ========================================================

    normalized_equal = values_equal(
        source_normalized,
        destination_normalized,
    )


    # ========================================================
    # CLASSIFY
    # ========================================================

    if raw_equal:

        comparison_status = (
            "EXACT_MATCH"
        )


    elif normalized_equal:

        comparison_status = (
            "NORMALIZED_MATCH"
        )


    else:

        comparison_status = (
            "DISCREPANCY"
        )


    return (
        raw_equal,
        normalized_equal,
        comparison_status,
    )


# ============================================================
# CREATE EXPLANATION
# ============================================================

def build_direct_explanation(
    source_field,
    destination_field,
    source_raw,
    destination_raw,
    source_normalized,
    destination_normalized,
    comparison_status,
):
    """
    Create a human-readable explanation for a direct
    comparison.
    """

    # ========================================================
    # EXACT MATCH
    # ========================================================

    if comparison_status == "EXACT_MATCH":

        return (
            f"Correspondance directe conforme: "
            f"{source_field} et {destination_field} "
            f"contiennent la même valeur."
        )


    # ========================================================
    # MATCH AFTER NORMALIZATION
    # ========================================================

    if comparison_status == "NORMALIZED_MATCH":

        return (
            f"Correspondance conforme après normalisation. "
            f"Valeur source brute: "
            f"{display_value(source_raw)}; "
            f"valeur cible brute: "
            f"{display_value(destination_raw)}. "
            f"Les deux deviennent "
            f"{display_value(source_normalized)} "
            f"après normalisation."
        )


    # ========================================================
    # DISCREPANCY
    # ========================================================

    return (
        f"Écart brut détecté entre "
        f"{source_field} et {destination_field}. "
        f"Valeur attendue normalisée: "
        f"{display_value(source_normalized)}; "
        f"valeur cible normalisée: "
        f"{display_value(destination_normalized)}. "
        f"Aucun verdict d'anomalie n'est encore attribué."
    )


# ============================================================
# COMPARE DIRECT MAPPINGS
# ============================================================

def compare_direct_mappings(
    raw_source_df: pd.DataFrame,
    raw_destination_df: pd.DataFrame,
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    parsed_mapping_df: pd.DataFrame,
    assignment_matches_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare all DIRECT mappings for deterministically matched
    assignments.

    Only assignment rows with:

        assignment_match_status == MATCHED

    are processed.

    Ambiguous and unmatched assignments are intentionally
    excluded.
    """

    results = []


    # ========================================================
    # GET DIRECT MAPPING ROWS
    # ========================================================

    direct_mappings = parsed_mapping_df[

        parsed_mapping_df[
            "row_type"
        ] == "DIRECT"

    ].copy()


    # ========================================================
    # GET SAFE ASSIGNMENT MATCHES
    # ========================================================

    safe_matches = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "MATCHED"

    ].copy()


    # ========================================================
    # LOOP THROUGH MATCHED ASSIGNMENTS
    # ========================================================

    for _, assignment in safe_matches.iterrows():

        employee_id = (
            assignment[
                "employee_id"
            ]
        )


        assignment_type = (
            assignment[
                "assignment_type"
            ]
        )


        # ----------------------------------------------------
        # ROW INDICES
        # ----------------------------------------------------

        source_row_index = int(
            assignment[
                "source_row_index"
            ]
        )


        destination_row_index = int(
            assignment[
                "destination_row_index"
            ]
        )


        # ====================================================
        # COMPARE EACH DIRECT FIELD
        # ====================================================

        for _, mapping in direct_mappings.iterrows():

            source_field = (
                mapping[
                    "source_field"
                ]
            )


            destination_field = (
                mapping[
                    "destination_field"
                ]
            )


            # ------------------------------------------------
            # SAFETY CHECK
            # ------------------------------------------------

            if source_field not in source_df.columns:

                raise ValueError(
                    f"Mapped source field "
                    f"'{source_field}' does not exist."
                )


            if destination_field not in destination_df.columns:

                raise ValueError(
                    f"Mapped destination field "
                    f"'{destination_field}' does not exist."
                )


            # =================================================
            # RAW VALUES
            # =================================================

            source_raw = (
                raw_source_df.at[
                    source_row_index,
                    source_field,
                ]
            )


            destination_raw = (
                raw_destination_df.at[
                    destination_row_index,
                    destination_field,
                ]
            )


            # =================================================
            # NORMALIZED VALUES
            # =================================================

            source_normalized = (
                source_df.at[
                    source_row_index,
                    source_field,
                ]
            )


            destination_normalized = (
                destination_df.at[
                    destination_row_index,
                    destination_field,
                ]
            )


            # =================================================
            # CLASSIFY COMPARISON
            # =================================================

            (
                raw_equal,
                normalized_equal,
                comparison_status,
            ) = classify_comparison(

                source_raw=
                    source_raw,

                destination_raw=
                    destination_raw,

                source_normalized=
                    source_normalized,

                destination_normalized=
                    destination_normalized,
            )


            # =================================================
            # TEMPORARY VERDICT
            # =================================================
            #
            # This is NOT the final business verdict.
            #
            # A discrepancy will later be evaluated by:
            #
            #     business rules
            #     AI if necessary
            #
            if comparison_status in {
                "EXACT_MATCH",
                "NORMALIZED_MATCH",
            }:

                verdict = (
                    "CONFORME"
                )

            else:

                verdict = (
                    "ECART_BRUT"
                )


            # =================================================
            # EXPLANATION
            # =================================================

            explanation = build_direct_explanation(

                source_field=
                    source_field,

                destination_field=
                    destination_field,

                source_raw=
                    source_raw,

                destination_raw=
                    destination_raw,

                source_normalized=
                    source_normalized,

                destination_normalized=
                    destination_normalized,

                comparison_status=
                    comparison_status,
            )


            # =================================================
            # RESULT RECORD
            # =================================================

            results.append(
                {
                    "employee_id":
                        employee_id,

                    "assignment_type":
                        assignment_type,

                    "source_row_index":
                        source_row_index,

                    "destination_row_index":
                        destination_row_index,

                    "mapping_row":
                        mapping[
                            "mapping_row"
                        ],

                    "description":
                        mapping[
                            "description"
                        ],

                    "source_field":
                        source_field,

                    "destination_field":
                        destination_field,

                    "source_raw_value":
                        source_raw,

                    "destination_raw_value":
                        destination_raw,

                    "source_normalized_value":
                        source_normalized,

                    "destination_normalized_value":
                        destination_normalized,

                    "raw_equal":
                        raw_equal,

                    "normalized_equal":
                        normalized_equal,

                    "comparison_status":
                        comparison_status,

                    "decision_source":
                        "DIRECT_COMPARISON",

                    "verdict":
                        verdict,

                    "rule_id":
                        None,

                    "explanation":
                        explanation,
                }
            )


    # ========================================================
    # BUILD DATAFRAME
    # ========================================================

    comparison_df = pd.DataFrame(
        results,
        columns=[
            "employee_id",
            "assignment_type",
            "source_row_index",
            "destination_row_index",
            "mapping_row",
            "description",
            "source_field",
            "destination_field",
            "source_raw_value",
            "destination_raw_value",
            "source_normalized_value",
            "destination_normalized_value",
            "raw_equal",
            "normalized_equal",
            "comparison_status",
            "decision_source",
            "verdict",
            "rule_id",
            "explanation",
        ],
    )


    return comparison_df


# ============================================================
# PREVIEW DIRECT COMPARISONS
# ============================================================

def preview_direct_comparisons(
    comparison_df: pd.DataFrame,
) -> None:
    """
    Display summary information for direct corroboration.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - DIRECT FIELD CORROBORATION"
    )

    print(
        "=" * 70
    )


    if comparison_df.empty:

        print(
            "No direct comparisons were produced."
        )

        return


    # ========================================================
    # TOTAL COMPARISONS
    # ========================================================

    print(
        f"\nTotal direct comparisons: "
        f"{len(comparison_df)}"
    )


    # ========================================================
    # COMPARISON STATUS COUNTS
    # ========================================================

    print(
        "\nCOMPARISON STATUS"
    )

    print(
        "-" * 70
    )


    status_counts = (
        comparison_df[
            "comparison_status"
        ]
        .value_counts()
    )


    for status, count in status_counts.items():

        print(
            f"{status}: {count}"
        )


    # ========================================================
    # VERDICT COUNTS
    # ========================================================

    print(
        "\nCURRENT VERDICTS"
    )

    print(
        "-" * 70
    )


    verdict_counts = (
        comparison_df[
            "verdict"
        ]
        .value_counts()
    )


    for verdict, count in verdict_counts.items():

        print(
            f"{verdict}: {count}"
        )


    # ========================================================
    # RAW DISCREPANCIES
    # ========================================================

    discrepancies = comparison_df[

        comparison_df[
            "comparison_status"
        ] == "DISCREPANCY"

    ]


    print(
        "\nRAW DISCREPANCIES"
    )

    print(
        "-" * 70
    )


    if discrepancies.empty:

        print(
            "None."
        )

    else:

        print(
            discrepancies[
                [
                    "employee_id",
                    "assignment_type",
                    "source_field",
                    "destination_field",
                    "source_normalized_value",
                    "destination_normalized_value",
                    "verdict",
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # NORMALIZATION-ONLY MATCHES
    # ========================================================

    normalized_matches = comparison_df[

        comparison_df[
            "comparison_status"
        ] == "NORMALIZED_MATCH"

    ]


    print(
        "\nMATCHES CREATED BY NORMALIZATION"
    )

    print(
        "-" * 70
    )


    if normalized_matches.empty:

        print(
            "None."
        )

    else:

        print(
            normalized_matches[
                [
                    "employee_id",
                    "source_field",
                    "destination_field",
                    "source_raw_value",
                    "destination_raw_value",
                    "source_normalized_value",
                ]
            ].to_string(
                index=False
            )
        )
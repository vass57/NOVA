# ============================================================
# CORROBORIA
# DETERMINISTIC BUSINESS RULE ENGINE
# ============================================================
#
# PURPOSE
#
# Calculate the EXPECTED System B values for fields whose
# mapping is governed by deterministic business rules.
#
#
# IMPORTANT:
#
#     Rules run BEFORE AI.
#
#     AI must not override a deterministic rule.
#
#
# OUTPUT VERDICTS
#
#     CONFORME
#         Destination matches the deterministic expectation.
#
#     ANOMALIE
#         The deterministic expected value is known and the
#         destination value does not match.
#
#     A_INVESTIGUER
#         CorroborIA cannot safely derive the expected value.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from datetime import timedelta
import unicodedata

import pandas as pd


from corroboria.comparator import (
    is_missing,
    values_equal,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def display_value(value) -> str:
    """
    Human-readable representation for explanations.
    """

    if is_missing(value):
        return "<VIDE>"

    return repr(value)


def clean_text(value):
    """
    Return stripped text or None.
    """

    if is_missing(value):
        return None

    return str(value).strip()


def remove_accents(value):
    """
    Remove accents from text.

    Example:

        Élodie -> Elodie
    """

    text = clean_text(value)

    if text is None:
        return None

    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def canonical_access_code(value):
    """
    Normalize access/status codes to two digits.

    Examples:

        0  -> "00"
        1  -> "01"
        2  -> "02"
        7  -> "07"

    This is necessary because Excel may remove leading zeros.
    """

    if is_missing(value):
        return None

    text = str(value).strip()

    if text.endswith(".0"):

        possible_number = text[:-2]

        if possible_number.isdigit():
            text = possible_number

    if text.isdigit():

        return text.zfill(2)

    return text


def normalize_rule_string(value):
    """
    Normalize a string used for deterministic comparisons.
    """

    if is_missing(value):
        return None

    return str(value).strip()


def rule_values_equal(
    destination_field,
    expected_value,
    actual_value,
):
    """
    Compare an expected rule result with System B.

    Email comparison is case-insensitive.
    """

    if destination_field == "contactEmail":

        expected_missing = is_missing(
            expected_value
        )

        actual_missing = is_missing(
            actual_value
        )

        if expected_missing and actual_missing:
            return True

        if expected_missing != actual_missing:
            return False

        return (
            str(expected_value).strip().casefold()
            ==
            str(actual_value).strip().casefold()
        )

    return values_equal(
        expected_value,
        actual_value,
    )


# ============================================================
# RULE 1
# EMAIL
# ============================================================

def build_expected_email(
    source_row: pd.Series
):
    """
    Mapping rule:

        first letter of first name
        +
        surname
        +
        last 3 digits of employee code
        +
        @loto-quebec.com

    Accents are removed from first and last names.
    """

    first_name = remove_accents(
        source_row.get(
            "PrénomUsuel"
        )
    )

    last_name = remove_accents(
        source_row.get(
            "NomFamille"
        )
    )

    employee_id = clean_text(
        source_row.get(
            "Matricule"
        )
    )


    if (
        not first_name
        or not last_name
        or not employee_id
    ):

        return {
            "resolved": False,
            "expected": None,
            "reason": (
                "PrénomUsuel, NomFamille ou Matricule "
                "manquant."
            ),
            "inputs": {
                "PrénomUsuel":
                    source_row.get("PrénomUsuel"),

                "NomFamille":
                    source_row.get("NomFamille"),

                "Matricule":
                    source_row.get("Matricule"),
            },
        }


    if len(employee_id) < 3:

        return {
            "resolved": False,
            "expected": None,
            "reason": (
                "Le Matricule contient moins de "
                "trois caractères."
            ),
            "inputs": {
                "PrénomUsuel": first_name,
                "NomFamille": last_name,
                "Matricule": employee_id,
            },
        }


    expected = (
        first_name[0]
        + last_name
        + employee_id[-3:]
        + "@loto-quebec.com"
    )


    return {
        "resolved": True,
        "expected": expected,
        "reason": None,
        "inputs": {
            "PrénomUsuel": first_name,
            "NomFamille": last_name,
            "Matricule": employee_id,
        },
    }


# ============================================================
# RULE 2
# DIVISION NAME
# ============================================================

def build_expected_division_name(
    source_row: pd.Series
):
    """
    Mapping rule:

        Unité adm.
        +
        "-"
        +
        Unité adm. desc

    Interpreted using:

        CodeDirection
        LibelléDirection
    """

    code = clean_text(
        source_row.get(
            "CodeDirection"
        )
    )

    description = clean_text(
        source_row.get(
            "LibelléDirection"
        )
    )


    if (
        code is None
        or description is None
    ):

        return {
            "resolved": False,
            "expected": None,
            "reason": (
                "CodeDirection ou LibelléDirection "
                "manquant."
            ),
            "inputs": {
                "CodeDirection": code,
                "LibelléDirection": description,
            },
        }


    return {
        "resolved": True,
        "expected": (
            f"{code}-{description}"
        ),
        "reason": None,
        "inputs": {
            "CodeDirection": code,
            "LibelléDirection": description,
        },
    }


# ============================================================
# RULE 3
# POSITION NAME
# ============================================================

def build_expected_position_name(
    source_row: pd.Series
):
    """
    Mapping rule:

        Emploi
        +
        "-"
        +
        Emploi desc
    """

    code = clean_text(
        source_row.get(
            "CodeEmploi"
        )
    )

    description = clean_text(
        source_row.get(
            "IntituléEmploi"
        )
    )


    if (
        code is None
        or description is None
    ):

        return {
            "resolved": False,
            "expected": None,
            "reason": (
                "CodeEmploi ou IntituléEmploi "
                "manquant."
            ),
            "inputs": {
                "CodeEmploi": code,
                "IntituléEmploi": description,
            },
        }


    return {
        "resolved": True,
        "expected": (
            f"{code}-{description}"
        ),
        "reason": None,
        "inputs": {
            "CodeEmploi": code,
            "IntituléEmploi": description,
        },
    }


# ============================================================
# RULE 4
# CONTRACT TYPE
# ============================================================

def derive_contract_type(
    source_row: pd.Series
):
    """
    Mapping rules:

        V + permanent + full-time -> JWN

        V + permanent + part-time -> XFLR

        T -> KELH
        O -> WHX
        M -> CEGQ
        R -> CNZC
        J -> RMQ
        Z -> JAW
        Q -> TRSY
    """

    category = clean_text(
        source_row.get(
            "CatégorieEmploi"
        )
    )

    permanent = source_row.get(
        "EstPermanent"
    )

    full_time = source_row.get(
        "EstTempsPlein"
    )


    if category is None:

        return {
            "resolved": False,
            "expected": None,
            "reason": (
                "CatégorieEmploi manquante."
            ),
            "inputs": {
                "CatégorieEmploi": category,
                "EstPermanent": permanent,
                "EstTempsPlein": full_time,
            },
        }


    category = category.upper()


    simple_mapping = {
        "T": "KELH",
        "O": "WHX",
        "M": "CEGQ",
        "R": "CNZC",
        "J": "RMQ",
        "Z": "JAW",
        "Q": "TRSY",
    }


    if category in simple_mapping:

        return {
            "resolved": True,
            "expected":
                simple_mapping[
                    category
                ],
            "reason": None,
            "inputs": {
                "CatégorieEmploi": category,
                "EstPermanent": permanent,
                "EstTempsPlein": full_time,
            },
        }


    if category == "V":

        if (
            is_missing(permanent)
            or is_missing(full_time)
        ):

            return {
                "resolved": False,
                "expected": None,
                "reason": (
                    "EstPermanent ou EstTempsPlein "
                    "manquant pour CatégorieEmploi V."
                ),
                "inputs": {
                    "CatégorieEmploi": category,
                    "EstPermanent": permanent,
                    "EstTempsPlein": full_time,
                },
            }


        permanent_bool = bool(
            permanent
        )

        full_time_bool = bool(
            full_time
        )


        if (
            permanent_bool
            and full_time_bool
        ):

            expected = "JWN"


        elif (
            permanent_bool
            and not full_time_bool
        ):

            expected = "XFLR"


        else:

            return {
                "resolved": False,
                "expected": None,
                "reason": (
                    "La combinaison CatégorieEmploi V / "
                    "EstPermanent / EstTempsPlein n'est pas "
                    "définie dans le mapping."
                ),
                "inputs": {
                    "CatégorieEmploi": category,
                    "EstPermanent": permanent_bool,
                    "EstTempsPlein": full_time_bool,
                },
            }


        return {
            "resolved": True,
            "expected": expected,
            "reason": None,
            "inputs": {
                "CatégorieEmploi": category,
                "EstPermanent": permanent_bool,
                "EstTempsPlein": full_time_bool,
            },
        }


    return {
        "resolved": False,
        "expected": None,
        "reason": (
            f"CatégorieEmploi '{category}' "
            "non définie dans le mapping."
        ),
        "inputs": {
            "CatégorieEmploi": category,
            "EstPermanent": permanent,
            "EstTempsPlein": full_time,
        },
    }


# ============================================================
# RULE 5
# ASSIGNMENT FLAGS
# ============================================================

def derive_assignment_flags(
    source_row: pd.Series
):
    """
    Mapping rules:

        P:
            primary = True
            temporary = False

        A:
            primary = False
            temporary = True

        S:
            primary = False
            temporary = False
    """

    assignment_type = clean_text(
        source_row.get(
            "TypeAffectation"
        )
    )


    if assignment_type is None:

        return {
            "resolved": False,
            "primary": None,
            "temporary": None,
            "reason": (
                "TypeAffectation manquant."
            ),
            "inputs": {
                "TypeAffectation": None,
            },
        }


    assignment_type = (
        assignment_type.upper()
    )


    mapping = {
        "P": (
            True,
            False,
        ),

        "A": (
            False,
            True,
        ),

        "S": (
            False,
            False,
        ),
    }


    if assignment_type not in mapping:

        return {
            "resolved": False,
            "primary": None,
            "temporary": None,
            "reason": (
                f"TypeAffectation "
                f"'{assignment_type}' inconnu."
            ),
            "inputs": {
                "TypeAffectation":
                    assignment_type,
            },
        }


    primary, temporary = (
        mapping[
            assignment_type
        ]
    )


    return {
        "resolved": True,
        "primary": primary,
        "temporary": temporary,
        "reason": None,
        "inputs": {
            "TypeAffectation":
                assignment_type,
        },
    }


# ============================================================
# EMPLOYMENT STATUS RULE TABLE
# ============================================================

def clean_specific_status(value):
    """
    Remove optional quotes around status text.
    """

    text = clean_text(value)

    if text is None:
        return None

    return text.strip(
        "\"'"
    )


def find_employment_status_rule(
    access_code,
    employment_rules_df: pd.DataFrame,
):
    """
    Find the rule row associated with a CodeSuspensionAccès.
    """

    canonical_code = canonical_access_code(
        access_code
    )


    if canonical_code is None:
        return None


    for _, rule in employment_rules_df.iterrows():

        rule_codes = clean_text(
            rule.get(
                "access_status_codes"
            )
        )


        if rule_codes is None:
            continue


        codes = [
            canonical_access_code(
                code.strip()
            )
            for code in rule_codes.split(",")
        ]


        if canonical_code in codes:

            return rule


    return None


def lookup_external_status_reason(
    source_row: pd.Series,
    employment_reasons_df: pd.DataFrame,
):
    """
    Join:

        Source CodeRaisonStatut
            ↔
        CodeCatégorieStatut

    and:

        Source CodeSuspensionAccès
            ↔
        CodeGestionAccès

    Then return:

        CodeStatutSystèmeExterne
    """

    reason_code = clean_text(
        source_row.get(
            "CodeRaisonStatut"
        )
    )

    access_code = canonical_access_code(
        source_row.get(
            "CodeSuspensionAccès"
        )
    )


    if reason_code is None:

        return {
            "resolved": False,
            "value": None,
            "reason": (
                "CodeRaisonStatut manquant."
            ),
        }


    candidates = employment_reasons_df[
        employment_reasons_df[
            "CodeCatégorieStatut"
        ].astype(str) == reason_code
    ].copy()


    if access_code is not None:

        candidates = candidates[
            candidates[
                "CodeGestionAccès"
            ].apply(
                canonical_access_code
            ) == access_code
        ]


    if candidates.empty:

        return {
            "resolved": False,
            "value": None,
            "reason": (
                "Aucune correspondance trouvée dans "
                "Motif de la situation d'emploi."
            ),
        }


    values = (
        candidates[
            "CodeStatutSystèmeExterne"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


    if len(values) != 1:

        return {
            "resolved": False,
            "value": None,
            "reason": (
                "La jointure du motif retourne "
                "plusieurs codes externes possibles."
            ),
        }


    return {
        "resolved": True,
        "value": values[0],
        "reason": None,
    }


def derive_employment_status(
    source_row: pd.Series,
    employment_rules_df: pd.DataFrame,
    employment_reasons_df: pd.DataFrame,
):
    """
    Derive:

        detailedStatus
        statusReasonCode
        expectedReturnDate
    """

    access_code = canonical_access_code(
        source_row.get(
            "CodeSuspensionAccès"
        )
    )


    rule = find_employment_status_rule(
        access_code=
            access_code,

        employment_rules_df=
            employment_rules_df,
    )


    if rule is None:

        return {
            "resolved": False,
            "reason": (
                f"Aucune règle de situation d'emploi "
                f"pour CodeSuspensionAccès "
                f"{display_value(access_code)}."
            ),
            "detailedStatus": None,
            "statusReasonCode": None,
            "expectedReturnDate": None,
            "inputs": {
                "CodeSuspensionAccès":
                    access_code,

                "CodeRaisonStatut":
                    source_row.get(
                        "CodeRaisonStatut"
                    ),

                "DateRetourAnticipée":
                    source_row.get(
                        "DateRetourAnticipée"
                    ),
            },
        }


    detailed_status = clean_specific_status(
        rule.get(
            "specific_status"
        )
    )


    # --------------------------------------------------------
    # STATUS REASON
    # --------------------------------------------------------

    cad_rule = rule.get(
        "cad_rule"
    )


    if is_missing(cad_rule):

        status_reason = None


    else:

        lookup = lookup_external_status_reason(

            source_row=
                source_row,

            employment_reasons_df=
                employment_reasons_df,
        )


        if not lookup[
            "resolved"
        ]:

            return {
                "resolved": False,
                "reason":
                    lookup[
                        "reason"
                    ],
                "detailedStatus":
                    detailed_status,

                "statusReasonCode":
                    None,

                "expectedReturnDate":
                    None,

                "inputs": {
                    "CodeSuspensionAccès":
                        access_code,

                    "CodeRaisonStatut":
                        source_row.get(
                            "CodeRaisonStatut"
                        ),

                    "DateRetourAnticipée":
                        source_row.get(
                            "DateRetourAnticipée"
                        ),
                },
            }


        status_reason = (
            lookup[
                "value"
            ]
        )


    # --------------------------------------------------------
    # EXPECTED RETURN DATE
    # --------------------------------------------------------

    cadp_rule = rule.get(
        "cadp_rule"
    )


    if is_missing(cadp_rule):

        expected_return = None

    else:

        expected_return = (
            source_row.get(
                "DateRetourAnticipée"
            )
        )


    return {
        "resolved": True,
        "reason": None,
        "detailedStatus":
            detailed_status,

        "statusReasonCode":
            status_reason,

        "expectedReturnDate":
            expected_return,

        "inputs": {
            "CodeSuspensionAccès":
                access_code,

            "CodeRaisonStatut":
                source_row.get(
                    "CodeRaisonStatut"
                ),

            "DateRetourAnticipée":
                source_row.get(
                    "DateRetourAnticipée"
                ),
        },
    }


# ============================================================
# JOB HISTORY DATE HELPERS
# ============================================================

def to_timestamp(value):
    """
    Convert normalized date values to pandas Timestamp.
    """

    if is_missing(value):
        return None

    converted = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(converted):
        return None

    return pd.Timestamp(
        converted
    ).normalize()


def timestamp_to_iso(value):
    """
    Convert Timestamp to YYYY-MM-DD.
    """

    if value is None:
        return None

    return value.strftime(
        "%Y-%m-%d"
    )


def minimum_date(
    *values,
):
    """
    Return earliest valid date as ISO text.
    """

    parsed = [
        to_timestamp(
            value
        )
        for value in values
    ]

    parsed = [
        value
        for value in parsed
        if value is not None
    ]


    if not parsed:
        return None


    return timestamp_to_iso(
        min(parsed)
    )


# ============================================================
# JOB HISTORY PERIOD
# ============================================================

def find_admin_unit_period(
    source_row: pd.Series,
    job_details_df: pd.DataFrame,
):
    """
    Find when the current administrative unit became effective
    and, when applicable, when it ended.

    Matching keys from the supplied join definition:

        CodePoste
            ↔ IdentifiantPoste

        CodeEmploi
            ↔ IdentifiantEmploi

        CodeDirection
            ↔ CodeDirectionAffectée
    """

    position = clean_text(
        source_row.get(
            "CodePoste"
        )
    )

    employment = clean_text(
        source_row.get(
            "CodeEmploi"
        )
    )

    direction = clean_text(
        source_row.get(
            "CodeDirection"
        )
    )


    if (
        position is None
        or employment is None
        or direction is None
    ):

        return {
            "resolved": False,
            "start": None,
            "end": None,
            "reason": (
                "CodePoste, CodeEmploi ou CodeDirection "
                "manquant."
            ),
            "history_rows": [],
        }


    history = job_details_df[
        (
            job_details_df[
                "IdentifiantPoste"
            ].astype(str) == position
        )
        &
        (
            job_details_df[
                "IdentifiantEmploi"
            ].astype(str) == employment
        )
    ].copy()


    if history.empty:

        return {
            "resolved": False,
            "start": None,
            "end": None,
            "reason": (
                "Aucun historique Détail du poste trouvé "
                "pour CodePoste + CodeEmploi."
            ),
            "history_rows": [],
        }


    history[
        "_date"
    ] = history[
        "DateEffetAffectation"
    ].apply(
        to_timestamp
    )


    history = history[
        history[
            "_date"
        ].notna()
    ].copy()


    history = (
        history
        .sort_values(
            by="_date"
        )
        .reset_index()
    )


    if history.empty:

        return {
            "resolved": False,
            "start": None,
            "end": None,
            "reason": (
                "L'historique Détail du poste ne contient "
                "aucune DateEffetAffectation exploitable."
            ),
            "history_rows": [],
        }


    matching_positions = []


    for position_index, row in history.iterrows():

        row_direction = clean_text(
            row.get(
                "CodeDirectionAffectée"
            )
        )


        if row_direction == direction:

            matching_positions.append(
                position_index
            )


    if not matching_positions:

        return {
            "resolved": False,
            "start": None,
            "end": None,
            "reason": (
                "Le CodeDirection courant n'est pas trouvé "
                "dans l'historique du poste."
            ),
            "history_rows":
                history[
                    "index"
                ].tolist(),
        }


    # --------------------------------------------------------
    # Use latest occurrence of the CURRENT direction.
    #
    # Then walk backward to find when this contiguous period
    # began.
    # --------------------------------------------------------

    current_position = max(
        matching_positions
    )


    start_position = (
        current_position
    )


    while start_position > 0:

        previous_direction = clean_text(

            history.iloc[
                start_position - 1
            ].get(
                "CodeDirectionAffectée"
            )

        )


        if previous_direction != direction:
            break


        start_position -= 1


    # --------------------------------------------------------
    # Walk forward through same administrative unit.
    # --------------------------------------------------------

    end_position = (
        current_position
    )


    while (
        end_position + 1
        <
        len(history)
    ):

        next_direction = clean_text(

            history.iloc[
                end_position + 1
            ].get(
                "CodeDirectionAffectée"
            )

        )


        if next_direction != direction:
            break


        end_position += 1


    admin_start = (
        history.iloc[
            start_position
        ][
            "_date"
        ]
    )


    # --------------------------------------------------------
    # ADMIN END
    #
    # Next detail date - 1 day ONLY if next detail changes
    # administrative unit.
    # --------------------------------------------------------

    admin_end = None


    next_position = (
        end_position + 1
    )


    if next_position < len(history):

        next_row = (
            history.iloc[
                next_position
            ]
        )

        next_direction = clean_text(
            next_row.get(
                "CodeDirectionAffectée"
            )
        )


        if next_direction != direction:

            next_date = (
                next_row[
                    "_date"
                ]
            )

            admin_end = (
                next_date
                - timedelta(
                    days=1
                )
            )


    return {
        "resolved": True,

        "start":
            timestamp_to_iso(
                admin_start
            ),

        "end":
            timestamp_to_iso(
                admin_end
            ),

        "reason": None,

        "history_rows":
            history[
                "index"
            ].tolist(),
    }


# ============================================================
# ASSIGNMENT DATES
# ============================================================

def derive_assignment_dates(
    source_row: pd.Series,
    job_details_df: pd.DataFrame,
):
    """
    Calculate:

        assignmentStartDate
        assignmentEndDate
        termEndDate
    """

    period = find_admin_unit_period(

        source_row=
            source_row,

        job_details_df=
            job_details_df,
    )


    if not period[
        "resolved"
    ]:

        return {
            "resolved": False,
            "assignmentStartDate": None,
            "assignmentEndDate": None,
            "termEndDate": None,
            "reason":
                period[
                    "reason"
                ],
            "inputs": {
                "DateEntréePoste":
                    source_row.get(
                        "DateEntréePoste"
                    ),

                "DateSortiePoste":
                    source_row.get(
                        "DateSortiePoste"
                    ),

                "CodePoste":
                    source_row.get(
                        "CodePoste"
                    ),

                "CodeEmploi":
                    source_row.get(
                        "CodeEmploi"
                    ),

                "CodeDirection":
                    source_row.get(
                        "CodeDirection"
                    ),
            },
        }


    assignment_start = minimum_date(

        source_row.get(
            "DateEntréePoste"
        ),

        period[
            "start"
        ],
    )


    assignment_end = minimum_date(

        source_row.get(
            "DateSortiePoste"
        ),

        period[
            "end"
        ],
    )


    # Mapping specifies same earliest-end logic for termEndDate.
    term_end = assignment_end


    return {
        "resolved": True,

        "assignmentStartDate":
            assignment_start,

        "assignmentEndDate":
            assignment_end,

        "termEndDate":
            term_end,

        "reason": None,

        "inputs": {
            "DateEntréePoste":
                source_row.get(
                    "DateEntréePoste"
                ),

            "DateSortiePoste":
                source_row.get(
                    "DateSortiePoste"
                ),

            "adminUnitStart":
                period[
                    "start"
                ],

            "adminUnitEnd":
                period[
                    "end"
                ],

            "jobDetailRows":
                period[
                    "history_rows"
                ],
        },
    }


# ============================================================
# STANDARD RULE RESULT
# ============================================================

def build_rule_result(
    employee_id,
    assignment_type,
    source_row_index,
    destination_row_index,
    mapping_row,
    rule_id,
    rule_name,
    destination_field,
    source_inputs,
    expected_value,
    destination_raw_value,
    destination_normalized_value,
    resolved,
    unresolved_reason=None,
):
    """
    Build one standardized deterministic rule result.
    """

    # --------------------------------------------------------
    # RULE COULD NOT BE RESOLVED
    # --------------------------------------------------------

    if not resolved:

        return {
            "employee_id":
                employee_id,

            "assignment_type":
                assignment_type,

            "source_row_index":
                source_row_index,

            "destination_row_index":
                destination_row_index,

            "mapping_row":
                mapping_row,

            "rule_id":
                rule_id,

            "rule_name":
                rule_name,

            "destination_field":
                destination_field,

            "source_inputs":
                source_inputs,

            "expected_value":
                expected_value,

            "destination_raw_value":
                destination_raw_value,

            "destination_normalized_value":
                destination_normalized_value,

            "rule_resolved":
                False,

            "comparison_status":
                "RULE_UNRESOLVED",

            "decision_source":
                "RULE",

            "verdict":
                "A_INVESTIGUER",

            "explanation":
                (
                    f"La règle {rule_id} ne peut pas être "
                    f"résolue de façon déterministe: "
                    f"{unresolved_reason}"
                ),
        }


    # --------------------------------------------------------
    # COMPARE EXPECTATION TO DESTINATION
    # --------------------------------------------------------

    equal = rule_values_equal(

        destination_field=
            destination_field,

        expected_value=
            expected_value,

        actual_value=
            destination_normalized_value,
    )


    if equal:

        comparison_status = (
            "RULE_MATCH"
        )

        verdict = (
            "CONFORME"
        )

        explanation = (
            f"{rule_id} conforme. "
            f"Valeur attendue pour "
            f"{destination_field}: "
            f"{display_value(expected_value)}."
        )


    else:

        comparison_status = (
            "RULE_DISCREPANCY"
        )

        verdict = (
            "ANOMALIE"
        )

        explanation = (
            f"{rule_id} non conforme. "
            f"Valeur attendue pour "
            f"{destination_field}: "
            f"{display_value(expected_value)}; "
            f"valeur reçue: "
            f"{display_value(destination_normalized_value)}."
        )


    return {
        "employee_id":
            employee_id,

        "assignment_type":
            assignment_type,

        "source_row_index":
            source_row_index,

        "destination_row_index":
            destination_row_index,

        "mapping_row":
            mapping_row,

        "rule_id":
            rule_id,

        "rule_name":
            rule_name,

        "destination_field":
            destination_field,

        "source_inputs":
            source_inputs,

        "expected_value":
            expected_value,

        "destination_raw_value":
            destination_raw_value,

        "destination_normalized_value":
            destination_normalized_value,

        "rule_resolved":
            True,

        "comparison_status":
            comparison_status,

        "decision_source":
            "RULE",

        "verdict":
            verdict,

        "explanation":
            explanation,
    }


# ============================================================
# MAIN RULE ENGINE
# ============================================================

def evaluate_rule_based_fields(
    raw_destination_df: pd.DataFrame,
    source_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    job_details_df: pd.DataFrame,
    employment_reasons_df: pd.DataFrame,
    employment_rules_df: pd.DataFrame,
    assignment_matches_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute deterministic mapping rules for every safely
    matched assignment.
    """

    results = []


    safe_matches = assignment_matches_df[

        assignment_matches_df[
            "assignment_match_status"
        ] == "MATCHED"

    ].copy()


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

        source_index = int(
            assignment[
                "source_row_index"
            ]
        )

        destination_index = int(
            assignment[
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

        raw_destination_row = (
            raw_destination_df.loc[
                destination_index
            ]
        )


        # ====================================================
        # EMAIL
        # ====================================================

        email = build_expected_email(
            source_row
        )


        results.append(

            build_rule_result(

                employee_id,
                assignment_type,
                source_index,
                destination_index,

                mapping_row=4,

                rule_id="RULE_EMAIL",

                rule_name=(
                    "Construction adresse courriel"
                ),

                destination_field=
                    "contactEmail",

                source_inputs=
                    email[
                        "inputs"
                    ],

                expected_value=
                    email[
                        "expected"
                    ],

                destination_raw_value=
                    raw_destination_row.get(
                        "contactEmail"
                    ),

                destination_normalized_value=
                    destination_row.get(
                        "contactEmail"
                    ),

                resolved=
                    email[
                        "resolved"
                    ],

                unresolved_reason=
                    email[
                        "reason"
                    ],
            )
        )


        # ====================================================
        # DIVISION NAME
        # ====================================================

        division = (
            build_expected_division_name(
                source_row
            )
        )


        results.append(

            build_rule_result(

                employee_id,
                assignment_type,
                source_index,
                destination_index,

                mapping_row=12,

                rule_id="RULE_DIVISION_NAME",

                rule_name=(
                    "Concaténation unité administrative"
                ),

                destination_field=
                    "divisionName",

                source_inputs=
                    division[
                        "inputs"
                    ],

                expected_value=
                    division[
                        "expected"
                    ],

                destination_raw_value=
                    raw_destination_row.get(
                        "divisionName"
                    ),

                destination_normalized_value=
                    destination_row.get(
                        "divisionName"
                    ),

                resolved=
                    division[
                        "resolved"
                    ],

                unresolved_reason=
                    division[
                        "reason"
                    ],
            )
        )


        # ====================================================
        # POSITION NAME
        # ====================================================

        position = (
            build_expected_position_name(
                source_row
            )
        )


        results.append(

            build_rule_result(

                employee_id,
                assignment_type,
                source_index,
                destination_index,

                mapping_row=15,

                rule_id="RULE_POSITION_NAME",

                rule_name=(
                    "Concaténation emploi"
                ),

                destination_field=
                    "positionName",

                source_inputs=
                    position[
                        "inputs"
                    ],

                expected_value=
                    position[
                        "expected"
                    ],

                destination_raw_value=
                    raw_destination_row.get(
                        "positionName"
                    ),

                destination_normalized_value=
                    destination_row.get(
                        "positionName"
                    ),

                resolved=
                    position[
                        "resolved"
                    ],

                unresolved_reason=
                    position[
                        "reason"
                    ],
            )
        )


        # ====================================================
        # EMPLOYMENT STATUS
        # ====================================================

        status = derive_employment_status(

            source_row=
                source_row,

            employment_rules_df=
                employment_rules_df,

            employment_reasons_df=
                employment_reasons_df,
        )


        for (
            mapping_row,
            rule_id,
            rule_name,
            destination_field,
            expected_value,
        ) in [

            (
                17,
                "RULE_STATUS_REASON",
                "Motif de situation d'emploi",
                "statusReasonCode",
                status[
                    "statusReasonCode"
                ],
            ),

            (
                22,
                "RULE_EXPECTED_RETURN",
                "Date de retour prévue",
                "expectedReturnDate",
                status[
                    "expectedReturnDate"
                ],
            ),

            (
                23,
                "RULE_DETAILED_STATUS",
                "Situation d'emploi",
                "detailedStatus",
                status[
                    "detailedStatus"
                ],
            ),
        ]:

            results.append(

                build_rule_result(

                    employee_id,
                    assignment_type,
                    source_index,
                    destination_index,

                    mapping_row=
                        mapping_row,

                    rule_id=
                        rule_id,

                    rule_name=
                        rule_name,

                    destination_field=
                        destination_field,

                    source_inputs=
                        status[
                            "inputs"
                        ],

                    expected_value=
                        expected_value,

                    destination_raw_value=
                        raw_destination_row.get(
                            destination_field
                        ),

                    destination_normalized_value=
                        destination_row.get(
                            destination_field
                        ),

                    resolved=
                        status[
                            "resolved"
                        ],

                    unresolved_reason=
                        status[
                            "reason"
                        ],
                )
            )


        # ====================================================
        # CONTRACT TYPE
        # ====================================================

        contract = derive_contract_type(
            source_row
        )


        results.append(

            build_rule_result(

                employee_id,
                assignment_type,
                source_index,
                destination_index,

                mapping_row=24,

                rule_id="RULE_CONTRACT_TYPE",

                rule_name=(
                    "Type d'employé"
                ),

                destination_field=
                    "contractTypeCode",

                source_inputs=
                    contract[
                        "inputs"
                    ],

                expected_value=
                    contract[
                        "expected"
                    ],

                destination_raw_value=
                    raw_destination_row.get(
                        "contractTypeCode"
                    ),

                destination_normalized_value=
                    destination_row.get(
                        "contractTypeCode"
                    ),

                resolved=
                    contract[
                        "resolved"
                    ],

                unresolved_reason=
                    contract[
                        "reason"
                    ],
            )
        )


        # ====================================================
        # ASSIGNMENT FLAGS
        # ====================================================

        flags = derive_assignment_flags(
            source_row
        )


        for (
            destination_field,
            expected_value,
            rule_id,
        ) in [

            (
                "isPrimaryAssignment",
                flags[
                    "primary"
                ],
                "RULE_PRIMARY_ASSIGNMENT",
            ),

            (
                "isTemporaryAssignment",
                flags[
                    "temporary"
                ],
                "RULE_TEMP_ASSIGNMENT",
            ),
        ]:

            results.append(

                build_rule_result(

                    employee_id,
                    assignment_type,
                    source_index,
                    destination_index,

                    mapping_row=41,

                    rule_id=
                        rule_id,

                    rule_name=(
                        "Type d'affectation P/A/S"
                    ),

                    destination_field=
                        destination_field,

                    source_inputs=
                        flags[
                            "inputs"
                        ],

                    expected_value=
                        expected_value,

                    destination_raw_value=
                        raw_destination_row.get(
                            destination_field
                        ),

                    destination_normalized_value=
                        destination_row.get(
                            destination_field
                        ),

                    resolved=
                        flags[
                            "resolved"
                        ],

                    unresolved_reason=
                        flags[
                            "reason"
                        ],
                )
            )


        # ====================================================
        # ASSIGNMENT / TERM DATES
        # ====================================================

        dates = derive_assignment_dates(

            source_row=
                source_row,

            job_details_df=
                job_details_df,
        )


        for (
            mapping_row,
            rule_id,
            rule_name,
            destination_field,
        ) in [

            (
                46,
                "RULE_ASSIGNMENT_START",
                "Date d'effet du poste",
                "assignmentStartDate",
            ),

            (
                53,
                "RULE_ASSIGNMENT_END",
                "Date d'expiration poste",
                "assignmentEndDate",
            ),

            (
                56,
                "RULE_TERM_END",
                "Date d'effet du détail du poste",
                "termEndDate",
            ),
        ]:

            expected_value = dates[
                destination_field
            ]


            results.append(

                build_rule_result(

                    employee_id,
                    assignment_type,
                    source_index,
                    destination_index,

                    mapping_row=
                        mapping_row,

                    rule_id=
                        rule_id,

                    rule_name=
                        rule_name,

                    destination_field=
                        destination_field,

                    source_inputs=
                        dates[
                            "inputs"
                        ],

                    expected_value=
                        expected_value,

                    destination_raw_value=
                        raw_destination_row.get(
                            destination_field
                        ),

                    destination_normalized_value=
                        destination_row.get(
                            destination_field
                        ),

                    resolved=
                        dates[
                            "resolved"
                        ],

                    unresolved_reason=
                        dates[
                            "reason"
                        ],
                )
            )


    return pd.DataFrame(
        results
    )


# ============================================================
# PREVIEW RULE ENGINE
# ============================================================

def preview_rule_based_results(
    rule_results_df: pd.DataFrame,
) -> None:
    """
    Print deterministic business-rule results.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "CORROBORIA - BUSINESS RULE ENGINE"
    )

    print(
        "=" * 70
    )


    if rule_results_df.empty:

        print(
            "\nNo rule-based comparisons were produced."
        )

        return


    print(
        f"\nTotal rule-based comparisons: "
        f"{len(rule_results_df)}"
    )


    print(
        "\nRULE COMPARISON STATUS"
    )

    print(
        "-" * 70
    )


    for (
        status,
        count,
    ) in (
        rule_results_df[
            "comparison_status"
        ]
        .value_counts()
        .items()
    ):

        print(
            f"{status}: {count}"
        )


    print(
        "\nRULE VERDICTS"
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
    # DETERMINISTIC ANOMALIES
    # ========================================================

    anomalies = rule_results_df[
        rule_results_df[
            "verdict"
        ] == "ANOMALIE"
    ]


    print(
        "\nDETERMINISTIC RULE ANOMALIES"
    )

    print(
        "-" * 70
    )


    if anomalies.empty:

        print(
            "None."
        )

    else:

        print(

            anomalies[
                [
                    "employee_id",
                    "assignment_type",
                    "rule_id",
                    "destination_field",
                    "expected_value",
                    "destination_normalized_value",
                ]
            ].to_string(
                index=False
            )

        )


    # ========================================================
    # UNRESOLVED RULES
    # ========================================================

    unresolved = rule_results_df[
        rule_results_df[
            "verdict"
        ] == "A_INVESTIGUER"
    ]


    print(
        "\nRULES REQUIRING INVESTIGATION"
    )

    print(
        "-" * 70
    )


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
                    "rule_id",
                    "destination_field",
                    "explanation",
                ]
            ].to_string(
                index=False
            )

        )

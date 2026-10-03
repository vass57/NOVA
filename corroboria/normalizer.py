# ============================================================
# CORROBORIA
# NORMALIZATION UTILITIES
# ============================================================
#
# This module contains reusable functions used to normalize
# values before System A and System B are compared.
#
# IMPORTANT:
#
# Normalization is NOT a business rule.
#
# Normalization only changes representation.
#
# Example:
#
#     48
#     48.0
#     "48"
#
# may all represent the same identifier.
#
# Likewise:
#
#     1995-02-09
#     1995-02-09T00:00:00.000Z
#
# may represent the same date.
#
# The original Excel files are NEVER modified.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from datetime import date, datetime
from numbers import Number
import re

import pandas as pd


# ============================================================
# EMPTY VALUE NORMALIZATION
# ============================================================

def normalize_empty(value):
    """
    Convert different representations of missing data to None.

    Examples:

        None
        NaN
        NaT
        ""
        "   "
        "NULL"
        "None"

    all become:

        None
    """

    # --------------------------------------------------------
    # Already None
    # --------------------------------------------------------

    if value is None:
        return None


    # --------------------------------------------------------
    # Pandas missing values
    # --------------------------------------------------------

    try:

        if pd.isna(value):
            return None

    except (
        TypeError,
        ValueError,
    ):

        pass


    # --------------------------------------------------------
    # String-based empty values
    # --------------------------------------------------------

    if isinstance(value, str):

        cleaned = value.strip()

        if cleaned.lower() in {
            "",
            "null",
            "none",
            "nan",
            "nat",
        }:

            return None


    return value


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize ordinary text.

    Example:

        "   Bonjour   "

    becomes:

        "Bonjour"

    Missing values become None.
    """

    value = normalize_empty(value)


    if value is None:
        return None


    return str(value).strip()


# ============================================================
# IDENTIFIER NORMALIZATION
# ============================================================

def normalize_identifier(value):
    """
    Normalize identifiers and codes.

    Examples:

        48
        48.0
        "48"

    become:

        "48"


    IMPORTANT:

    Identifiers are treated as text, not quantities.

    Strings containing leading zeroes are preserved.

    Example:

        "001234"

    remains:

        "001234"
    """

    value = normalize_empty(value)


    if value is None:
        return None


    # ========================================================
    # STRING IDENTIFIER
    # ========================================================

    if isinstance(value, str):

        text = value.strip()


        # Remove a meaningless decimal suffix.
        #
        # "48.0" -> "48"
        #
        # But:
        #
        # "001234" remains "001234"
        #
        if re.fullmatch(
            r"-?\d+\.0+",
            text,
        ):

            return text.split(".")[0]


        return text


    # ========================================================
    # NUMERIC IDENTIFIER
    # ========================================================

    if isinstance(value, Number):

        try:

            number = float(value)


            # 48.0 -> "48"
            if number.is_integer():

                return str(
                    int(number)
                )


            # Preserve meaningful decimals if they exist.
            return str(number)


        except (
            ValueError,
            TypeError,
            OverflowError,
        ):

            pass


    # ========================================================
    # FALLBACK
    # ========================================================

    return str(value).strip()


# ============================================================
# BOOLEAN NORMALIZATION
# ============================================================

def normalize_boolean(value):
    """
    Normalize boolean-like values.

    True examples:

        True
        1
        "1"
        "true"
        "yes"
        "oui"

    False examples:

        False
        0
        "0"
        "false"
        "no"
        "non"

    Unknown values return None.

    We never guess.
    """

    value = normalize_empty(value)


    if value is None:
        return None


    # ========================================================
    # NATIVE / NUMPY BOOLEAN-LIKE VALUES
    # ========================================================

    if value == True:
        return True


    if value == False:
        return False


    # ========================================================
    # TEXT VALUES
    # ========================================================

    text = str(value).strip().lower()


    true_values = {
        "true",
        "1",
        "yes",
        "oui",
        "y",
        "o",
        "vrai",
    }


    false_values = {
        "false",
        "0",
        "no",
        "non",
        "n",
        "faux",
    }


    if text in true_values:
        return True


    if text in false_values:
        return False


    return None


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date(value):
    """
    Normalize dates into:

        YYYY-MM-DD


    Supports:

        Python datetime objects
        Python date objects
        ordinary date strings
        ISO date strings
        Excel serial dates
        Excel serial dates stored as strings


    Examples:

        "2025-09-22T00:00:00.000Z"
            -> "2025-09-22"

        44285
            -> "2021-03-30"

        "44285"
            -> "2021-03-30"
    """

    value = normalize_empty(value)


    if value is None:
        return None


    # ========================================================
    # PYTHON DATETIME
    # ========================================================

    if isinstance(value, datetime):

        return value.date().isoformat()


    # ========================================================
    # PYTHON DATE
    # ========================================================

    if isinstance(value, date):

        return value.isoformat()


    # ========================================================
    # NUMERIC EXCEL SERIAL DATE
    # ========================================================
    #
    # Excel stores dates internally as a number of days.
    #
    # Excel-compatible pandas origin:
    #
    #     1899-12-30
    #
    if (
        isinstance(value, Number)
        and not isinstance(value, bool)
    ):

        try:

            number = float(value)


            # A broad realistic range for Excel dates.
            #
            # This prevents random values such as 2025 from
            # accidentally becoming dates.
            #
            if 20000 <= number <= 80000:

                parsed_date = pd.to_datetime(
                    number,
                    unit="D",
                    origin="1899-12-30",
                )


                return (
                    parsed_date
                    .date()
                    .isoformat()
                )


        except (
            ValueError,
            TypeError,
            OverflowError,
        ):

            pass


    # ========================================================
    # CONVERT TO TEXT
    # ========================================================

    text = str(value).strip()


    # ========================================================
    # EXCEL SERIAL DATE STORED AS TEXT
    # ========================================================

    if re.fullmatch(
        r"\d+(\.0+)?",
        text,
    ):

        try:

            number = float(text)


            if 20000 <= number <= 80000:

                parsed_date = pd.to_datetime(
                    number,
                    unit="D",
                    origin="1899-12-30",
                )


                return (
                    parsed_date
                    .date()
                    .isoformat()
                )


        except (
            ValueError,
            TypeError,
            OverflowError,
        ):

            pass


    # ========================================================
    # NORMAL DATE STRING
    # ========================================================

    try:

        parsed_date = pd.to_datetime(
            text,
            errors="raise",
        )


        return (
            parsed_date
            .date()
            .isoformat()
        )


    except (
        ValueError,
        TypeError,
        OverflowError,
    ):

        # Unknown date.
        #
        # Do not invent a result.
        return None


# ============================================================
# NUMBER NORMALIZATION
# ============================================================

def normalize_number(value):
    """
    Normalize actual quantities into floats.

    Examples:

        40
        40.0
        "40"

    become:

        40.0

    This should be used for quantities, not identifiers.
    """

    value = normalize_empty(value)


    if value is None:
        return None


    try:

        return float(value)


    except (
        ValueError,
        TypeError,
        OverflowError,
    ):

        return None
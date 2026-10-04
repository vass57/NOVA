# ============================================================
# CORROBORIA
# DATA NORMALIZATION
# ============================================================
#
# PURPOSE
#
# Normalize representation differences between System A,
# System B and supporting extracts.
#
# IMPORTANT:
#
# Normalization DOES NOT decide whether a value is correct.
#
# It only makes equivalent representations comparable.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from datetime import date, datetime
import re

import pandas as pd


# ============================================================
# EMPTY VALUE NORMALIZATION
# ============================================================

def normalize_empty(value):
    """
    Normalize blank / missing values to None.
    """

    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except (
        TypeError,
        ValueError,
    ):

        pass


    if isinstance(
        value,
        str,
    ):

        text = value.strip()


        if text.lower() in {
            "",
            "null",
            "none",
            "nan",
            "nat",
        }:

            return None


    return value


# ============================================================
# MOJIBAKE REPAIR
# ============================================================

def mojibake_score(
    text: str
) -> int:
    """
    Count common characters/sequences associated with broken
    UTF-8 decoding.

    Lower score is better.
    """

    suspicious_sequences = [
        "Ã",
        "Â",
        "â€",
        "â€™",
        "â€œ",
        "â€",
        "â€“",
        "â€”",
        "ï»¿",
        "�",
    ]


    return sum(
        text.count(
            sequence
        )
        for sequence in suspicious_sequences
    )


def repair_mojibake(
    text: str
) -> str:
    """
    Attempt conservative repair of common UTF-8 / Latin-1 /
    Windows-1252 mojibake.

    Example:

        Absence complÃ¨te
            ->
        Absence complète

    The repaired version is accepted ONLY when it reduces
    the number of suspicious encoding sequences.
    """

    if not isinstance(
        text,
        str,
    ):

        return text


    original_score = mojibake_score(
        text
    )


    if original_score == 0:

        return text


    candidates = [
        text
    ]


    # --------------------------------------------------------
    # LATIN-1 -> UTF-8
    # --------------------------------------------------------

    try:

        candidate = (
            text
            .encode(
                "latin1"
            )
            .decode(
                "utf-8"
            )
        )

        candidates.append(
            candidate
        )

    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
    ):

        pass


    # --------------------------------------------------------
    # WINDOWS-1252 -> UTF-8
    # --------------------------------------------------------

    try:

        candidate = (
            text
            .encode(
                "cp1252"
            )
            .decode(
                "utf-8"
            )
        )

        candidates.append(
            candidate
        )

    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
    ):

        pass


    best = min(
        candidates,
        key=mojibake_score,
    )


    if (
        mojibake_score(
            best
        )
        <
        original_score
    ):

        return best


    return text


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize ordinary text.

    Operations:

        - missing -> None
        - convert to string
        - trim surrounding whitespace
        - repair obvious mojibake

    Accents are NOT removed here.

    Accent removal is a business rule for specific fields,
    not a general normalization rule.
    """

    value = normalize_empty(
        value
    )


    if value is None:

        return None


    text = str(
        value
    ).strip()


    text = repair_mojibake(
        text
    )


    return text


# ============================================================
# IDENTIFIER NORMALIZATION
# ============================================================

def normalize_identifier(value):
    """
    Normalize identifiers and codes.

    Examples:

        1545850
            -> "1545850"

        1545850.0
            -> "1545850"

        "1545850.0"
            -> "1545850"

        "00397"
            -> "00397"

    Leading zeroes in existing strings are preserved.
    """

    value = normalize_empty(
        value
    )


    if value is None:

        return None


    # --------------------------------------------------------
    # BOOL SHOULD NOT BECOME 1 / 0 IDENTIFIERS
    # --------------------------------------------------------

    if isinstance(
        value,
        bool,
    ):

        return str(
            value
        )


    # --------------------------------------------------------
    # INTEGER
    # --------------------------------------------------------

    if isinstance(
        value,
        int,
    ):

        return str(
            value
        )


    # --------------------------------------------------------
    # FLOAT
    # --------------------------------------------------------

    if isinstance(
        value,
        float,
    ):

        if value.is_integer():

            return str(
                int(
                    value
                )
            )


        return str(
            value
        )


    # --------------------------------------------------------
    # STRING / OTHER
    # --------------------------------------------------------

    text = str(
        value
    ).strip()


    # Remove trailing .0 ONLY when the entire value is numeric.
    if re.fullmatch(
        r"-?\d+\.0",
        text,
    ):

        return text[:-2]


    return text


# ============================================================
# BOOLEAN NORMALIZATION
# ============================================================

def normalize_boolean(value):
    """
    Normalize common boolean representations.
    """

    value = normalize_empty(
        value
    )


    if value is None:

        return None


    if isinstance(
        value,
        bool,
    ):

        return value


    # NumPy boolean values are safely handled here too.
    if str(
        type(
            value
        )
    ).endswith(
        "bool_'>"
    ):

        return bool(
            value
        )


    if isinstance(
        value,
        (int, float),
    ):

        if value == 1:

            return True


        if value == 0:

            return False


    text = str(
        value
    ).strip().lower()


    true_values = {
        "true",
        "t",
        "yes",
        "y",
        "oui",
        "o",
        "1",
        "vrai",
    }


    false_values = {
        "false",
        "f",
        "no",
        "n",
        "non",
        "0",
        "faux",
    }


    if text in true_values:

        return True


    if text in false_values:

        return False


    return None


# ============================================================
# EXCEL SERIAL DATE
# ============================================================

def excel_serial_to_date(
    value
):
    """
    Convert an Excel serial date using Excel's standard
    1900-date-system origin.

    Pandas uses:

        1899-12-30

    which correctly accommodates Excel's historic leap-year
    quirk.

    IMPORTANT:

    The previous implementation required the serial to be
    >= 20000.

    That incorrectly rejected valid older dates such as:

        18484
        19110

    We now accept the normal positive Excel serial range.
    """

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


    # --------------------------------------------------------
    # MUST REPRESENT A WHOLE-DAY SERIAL
    # --------------------------------------------------------

    if not number.is_integer():

        return None


    serial = int(
        number
    )


    # --------------------------------------------------------
    # REASONABLE EXCEL DATE RANGE
    #
    # 1      = 1900 era
    # 80000  = well beyond challenge dates
    # --------------------------------------------------------

    if not (
        1
        <=
        serial
        <=
        80000
    ):

        return None


    converted = pd.to_datetime(
        serial,
        unit="D",
        origin="1899-12-30",
        errors="coerce",
    )


    if pd.isna(
        converted
    ):

        return None


    return (
        converted
        .date()
        .isoformat()
    )


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date(value):
    """
    Normalize dates to:

        YYYY-MM-DD

    Supports:

        datetime
        date
        pandas Timestamp
        ISO date strings
        ISO datetime strings
        Excel serial numbers
        Excel serial number strings
    """

    value = normalize_empty(
        value
    )


    if value is None:

        return None


    # --------------------------------------------------------
    # DATETIME / DATE / TIMESTAMP
    # --------------------------------------------------------

    if isinstance(
        value,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):

        timestamp = pd.Timestamp(
            value
        )


        if pd.isna(
            timestamp
        ):

            return None


        return (
            timestamp
            .date()
            .isoformat()
        )


    # --------------------------------------------------------
    # NUMERIC EXCEL SERIAL
    # --------------------------------------------------------

    if (
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
    ):

        excel_date = (
            excel_serial_to_date(
                value
            )
        )


        if excel_date is not None:

            return excel_date


    # --------------------------------------------------------
    # STRING
    # --------------------------------------------------------

    text = str(
        value
    ).strip()


    # --------------------------------------------------------
    # NUMERIC STRING MAY BE EXCEL SERIAL
    # --------------------------------------------------------

    if re.fullmatch(
        r"\d+(?:\.0+)?",
        text,
    ):

        excel_date = (
            excel_serial_to_date(
                text
            )
        )


        if excel_date is not None:

            return excel_date


    # --------------------------------------------------------
    # NORMAL DATE PARSING
    # --------------------------------------------------------

    converted = pd.to_datetime(
        text,
        errors="coerce",
    )


    if pd.isna(
        converted
    ):

        return None


    return (
        converted
        .date()
        .isoformat()
    )


# ============================================================
# NUMBER NORMALIZATION
# ============================================================

def normalize_number(value):
    """
    Normalize numeric values to float.

    Missing / invalid values become None.
    """

    value = normalize_empty(
        value
    )


    if value is None:

        return None


    if isinstance(
        value,
        bool,
    ):

        return None


    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None
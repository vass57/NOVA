"""Leave-one-confirmed-match-out validation for CorroborIA."""

from __future__ import annotations

from pathlib import Path
import random

import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier,
)

from corroboria.assignment_matcher import (
    match_assignments,
)
from corroboria.matcher import (
    match_employees,
)
from corroboria.pipeline import (
    InputPaths,
    _normalise_destination,
    _normalise_source,
    _read_table,
)


BASE_DIR = Path(__file__).resolve().parent

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


RANDOM_STATE = 42
NEGATIVE_RATIO = 5


FEATURE_COLUMNS = [
    "position_id_match",
    "position_code_match",
    "site_code_match",
    "division_id_match",
    "division_code_match",
    "pay_grade_match",
    "assignment_type_match",
    "weekly_hours_gap",
    "daily_hours_gap",
    "weekly_missing_mismatch",
    "daily_missing_mismatch",
]


def is_missing(
    value: object,
) -> bool:

    if value is None:
        return True

    try:

        return bool(
            pd.isna(
                value
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return False


def same_value(
    first: object,
    second: object,
) -> int:

    if (
        is_missing(
            first
        )
        or
        is_missing(
            second
        )
    ):

        return 0

    return int(
        str(
            first
        )
        ==
        str(
            second
        )
    )


def numeric_gap(
    first: object,
    second: object,
) -> float:

    first_missing = (
        is_missing(
            first
        )
    )

    second_missing = (
        is_missing(
            second
        )
    )

    if (
        first_missing
        and
        second_missing
    ):

        return 0.0

    if (
        first_missing
        or
        second_missing
    ):

        return 1000.0

    try:

        return abs(
            float(
                first
            )
            -
            float(
                second
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return 1000.0


def missing_mismatch(
    first: object,
    second: object,
) -> int:

    return int(
        is_missing(
            first
        )
        !=
        is_missing(
            second
        )
    )


def destination_assignment_type(
    row: pd.Series,
) -> str:

    if (
        row.get(
            "isPrimaryAssignment"
        )
        is True
    ):

        return "P"

    if (
        row.get(
            "isTemporaryAssignment"
        )
        is True
    ):

        return "A"

    return "S"


def pair_features(
    source_row: pd.Series,
    destination_row: pd.Series,
) -> dict[str, float]:

    source_type = str(
        source_row.get(
            "TypeAffectation"
        )
    )

    destination_type = (
        destination_assignment_type(
            destination_row
        )
    )

    return {

        "position_id_match":
            same_value(
                source_row.get(
                    "CodeEmploi"
                ),
                destination_row.get(
                    "positionId"
                ),
            ),

        "position_code_match":
            same_value(
                source_row.get(
                    "CodeEmploi"
                ),
                destination_row.get(
                    "positionCode"
                ),
            ),

        "site_code_match":
            same_value(
                source_row.get(
                    "CodeSite"
                ),
                destination_row.get(
                    "siteCode"
                ),
            ),

        "division_id_match":
            same_value(
                source_row.get(
                    "CodeDirection"
                ),
                destination_row.get(
                    "divisionId"
                ),
            ),

        "division_code_match":
            same_value(
                source_row.get(
                    "CodeImputation"
                ),
                destination_row.get(
                    "divisionCode"
                ),
            ),

        "pay_grade_match":
            same_value(
                source_row.get(
                    "ÉchelleSalariale"
                ),
                destination_row.get(
                    "payGradeId"
                ),
            ),

        "assignment_type_match":
            int(
                source_type
                ==
                destination_type
            ),

        "weekly_hours_gap":
            numeric_gap(
                source_row.get(
                    "HeuresNormeHebdo"
                ),
                destination_row.get(
                    "weeklyHoursOverride"
                ),
            ),

        "daily_hours_gap":
            numeric_gap(
                source_row.get(
                    "HeuresNormeQuotidienne"
                ),
                destination_row.get(
                    "dailyHoursOverride"
                ),
            ),

        "weekly_missing_mismatch":
            missing_mismatch(
                source_row.get(
                    "HeuresNormeHebdo"
                ),
                destination_row.get(
                    "weeklyHoursOverride"
                ),
            ),

        "daily_missing_mismatch":
            missing_mismatch(
                source_row.get(
                    "HeuresNormeQuotidienne"
                ),
                destination_row.get(
                    "dailyHoursOverride"
                ),
            ),
    }


def confirmed_pairs(
    assignment_matches: pd.DataFrame,
) -> pd.DataFrame:

    return (
        assignment_matches.loc[
            assignment_matches[
                "assignment_match_status"
            ]
            .eq(
                "MATCHED"
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


def build_training_data(
    source: pd.DataFrame,
    destination: pd.DataFrame,
    pairs: pd.DataFrame,
    holdout_index: int,
) -> tuple[
    pd.DataFrame,
    pd.Series,
]:

    train_pairs = pairs.drop(
        index=
            holdout_index
    )

    feature_rows = []

    labels = []

    # ========================================================
    # POSITIVE EXAMPLES
    # ========================================================

    for row in (
        train_pairs.itertuples()
    ):

        source_row = source.loc[
            int(
                row.source_row_index
            )
        ]

        destination_row = destination.loc[
            int(
                row.destination_row_index
            )
        ]

        feature_rows.append(
            pair_features(
                source_row,
                destination_row,
            )
        )

        labels.append(
            1
        )

    # ========================================================
    # NEGATIVE CROSS-EMPLOYEE EXAMPLES
    # ========================================================

    rng = random.Random(
        RANDOM_STATE
        +
        int(
            holdout_index
        )
    )

    destination_pool = [
        (
            str(
                row.employee_id
            ),
            int(
                row.destination_row_index
            ),
        )
        for row
        in train_pairs.itertuples()
    ]

    for source_pair in (
        train_pairs.itertuples()
    ):

        source_employee = str(
            source_pair.employee_id
        )

        source_index = int(
            source_pair.source_row_index
        )

        source_row = source.loc[
            source_index
        ]

        candidates = [
            (
                employee,
                destination_index,
            )
            for (
                employee,
                destination_index,
            )
            in destination_pool
            if (
                employee
                !=
                source_employee
            )
        ]

        sample_size = min(
            NEGATIVE_RATIO,
            len(
                candidates
            ),
        )

        chosen = rng.sample(
            candidates,
            sample_size,
        )

        for (
            _,
            destination_index,
        ) in chosen:

            destination_row = (
                destination.loc[
                    destination_index
                ]
            )

            feature_rows.append(
                pair_features(
                    source_row,
                    destination_row,
                )
            )

            labels.append(
                0
            )

    X = pd.DataFrame(
        feature_rows,
        columns=
            FEATURE_COLUMNS,
    )

    y = pd.Series(
        labels,
        dtype=int,
    )

    return (
        X,
        y,
    )


def validate() -> pd.DataFrame:

    paths = (
        InputPaths
        .from_data_directory(
            DATA_DIR
        )
    )

    source_raw = _read_table(
        paths.source
    )

    destination_raw = _read_table(
        paths.destination
    )

    source = _normalise_source(
        source_raw
    )

    destination = (
        _normalise_destination(
            destination_raw
        )
    )

    employee_matches = (
        match_employees(
            source_df=
                source,

            destination_df=
                destination,
        )
    )

    assignment_matches = (
        match_assignments(
            source_df=
                source,

            destination_df=
                destination,

            employee_matches_df=
                employee_matches,
        )
    )

    pairs = confirmed_pairs(
        assignment_matches
    )

    if (
        len(
            pairs
        )
        <
        3
    ):

        raise RuntimeError(
            "Not enough confirmed deterministic "
            "pairs for validation."
        )

    destination_indices = [
        int(
            row.destination_row_index
        )
        for row
        in pairs.itertuples()
    ]

    results = []

    # ========================================================
    # LEAVE ONE CONFIRMED PAIR OUT
    # ========================================================

    for (
        holdout_index,
        holdout,
    ) in pairs.iterrows():

        X_train, y_train = (
            build_training_data(
                source=
                    source,

                destination=
                    destination,

                pairs=
                    pairs,

                holdout_index=
                    holdout_index,
            )
        )

        model = (
            RandomForestClassifier(
                n_estimators=
                    500,

                class_weight=
                    "balanced",

                random_state=
                    RANDOM_STATE,

                n_jobs=
                    -1,
            )
        )

        model.fit(
            X_train,
            y_train,
        )

        source_index = int(
            holdout[
                "source_row_index"
            ]
        )

        true_destination = int(
            holdout[
                "destination_row_index"
            ]
        )

        source_row = source.loc[
            source_index
        ]

        candidates = []

        for destination_index in (
            destination_indices
        ):

            destination_row = (
                destination.loc[
                    destination_index
                ]
            )

            features = pair_features(
                source_row,
                destination_row,
            )

            candidates.append(
                {
                    "destination_row_index":
                        destination_index,

                    **features,
                }
            )

        candidate_frame = (
            pd.DataFrame(
                candidates
            )
        )

        probabilities = (
            model
            .predict_proba(
                candidate_frame[
                    FEATURE_COLUMNS
                ]
            )[
                :,
                1
            ]
        )

        candidate_frame[
            "score"
        ] = probabilities

        true_score = float(
            candidate_frame.loc[
                candidate_frame[
                    "destination_row_index"
                ]
                .eq(
                    true_destination
                ),
                "score",
            ]
            .iloc[
                0
            ]
        )

        rank = (
            1
            +
            int(
                (
                    candidate_frame[
                        "score"
                    ]
                    >
                    true_score
                    +
                    1e-12
                )
                .sum()
            )
        )

        top_index = (
            candidate_frame[
                "score"
            ]
            .idxmax()
        )

        top_row = (
            candidate_frame.loc[
                top_index
            ]
        )

        results.append(
            {
                "employee_id":
                    holdout[
                        "employee_id"
                    ],

                "source_row_index":
                    source_index,

                "true_destination_row_index":
                    true_destination,

                "top_destination_row_index":
                    int(
                        top_row[
                            "destination_row_index"
                        ]
                    ),

                "true_score":
                    true_score,

                "top_score":
                    float(
                        top_row[
                            "score"
                        ]
                    ),

                "rank":
                    rank,

                "top_1_correct":
                    (
                        rank
                        ==
                        1
                    ),

                "reciprocal_rank":
                    (
                        1.0
                        /
                        rank
                    ),

                "candidate_count":
                    len(
                        candidate_frame
                    ),
            }
        )

    return pd.DataFrame(
        results
    )


def main() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = validate()

    output_file = (
        OUTPUT_DIR
        /
        "ai_validation.csv"
    )

    results.to_csv(
        output_file,
        index=False,
    )

    top_1_correct = int(
        results[
            "top_1_correct"
        ]
        .sum()
    )

    top_1_accuracy = float(
        results[
            "top_1_correct"
        ]
        .mean()
    )

    mean_reciprocal_rank = float(
        results[
            "reciprocal_rank"
        ]
        .mean()
    )

    print(
        "=" * 72
    )

    print(
        "CORROBORIA - AI MATCHING VALIDATION"
    )

    print(
        "=" * 72
    )

    print(
        "\nConfirmed pairs evaluated: "
        f"{len(results)}"
    )

    print(
        "Top-1 ranking accuracy: "
        f"{top_1_correct}"
        "/"
        f"{len(results)} "
        f"({top_1_accuracy:.1%})"
    )

    print(
        "Mean reciprocal rank: "
        f"{mean_reciprocal_rank:.3f}"
    )

    print(
        "\nImportant limitations:"
    )

    print(
        "- The supplied dataset is small."
    )

    print(
        "- Confirmed positive examples are mostly "
        "deterministically matched assignments."
    )

    print(
        "- The ambiguous secondary-assignment case "
        "is NOT treated as validation ground truth."
    )

    print(
        "- Match scores are relative model scores, "
        "not calibrated probabilities."
    )

    print(
        "\nDetailed results saved to:"
    )

    print(
        output_file
    )


if __name__ == "__main__":
    main()
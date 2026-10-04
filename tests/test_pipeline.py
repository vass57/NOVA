"""Integration and safety checks for the approved challenge inputs."""

from __future__ import annotations

from pathlib import Path
import unittest

from corroboria.ai import validate_suggestion
from corroboria.export import cases_to_csv, run_to_excel
from corroboria.pipeline import InputPaths, VERDICTS, run_reconciliation


ROOT = Path(__file__).resolve().parents[1]


class ReconciliationPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reconciliation = run_reconciliation(InputPaths.from_data_directory(ROOT / "data"))

    def test_all_results_use_the_published_verdicts(self) -> None:
        self.assertTrue(set(self.reconciliation.cases["verdict"]).issubset(VERDICTS))

    def test_challenge_data_covers_match_justified_anomaly_and_review(self) -> None:
        counts = self.reconciliation.cases["verdict"].value_counts()
        for verdict in VERDICTS:
            self.assertGreater(counts.get(verdict, 0), 0, verdict)

    def test_direct_discrepancies_are_deterministic_anomalies(self) -> None:
        hourly_difference = self.reconciliation.cases.loc[
            self.reconciliation.cases["field"].eq("weeklyHoursOverride")
        ]
        self.assertIn("Actual anomaly", set(hourly_difference["verdict"]))
        self.assertTrue(
            hourly_difference.loc[
                hourly_difference["verdict"].eq("Actual anomaly"), "rule_ids"
            ].eq("").all()
        )

    def test_ambiguous_and_unmatched_records_are_not_silently_dropped(self) -> None:
        review = self.reconciliation.cases.loc[self.reconciliation.cases["verdict"].eq("Needs review")]
        self.assertFalse(review.empty)
        self.assertTrue(review["field"].eq("record matching").all())
        self.assertTrue(review["ai_status"].eq("not configured").all())

    def test_exports_include_report_and_audit_evidence(self) -> None:
        self.assertTrue(cases_to_csv(self.reconciliation.cases).startswith(b"\xef\xbb\xbf"))
        self.assertGreater(len(run_to_excel(self.reconciliation)), 1_000)
        self.assertIn("input_sha256", self.reconciliation.audit)


class AiBoundaryTests(unittest.TestCase):
    def test_rejects_a_suggestion_that_attempts_to_justify_without_a_rule(self) -> None:
        with self.assertRaises(ValueError):
            validate_suggestion(
                {
                    "proposed_verdict": "Justified difference",
                    "evidence_references": ["row 1"],
                    "rule_ids": [],
                    "missing_information": [],
                    "next_step": "Accept it",
                },
                {"RULE_EMAIL"},
            )

    def test_accepts_only_known_rule_references(self) -> None:
        with self.assertRaises(ValueError):
            validate_suggestion(
                {
                    "proposed_verdict": "Needs review",
                    "evidence_references": ["row 1"],
                    "rule_ids": ["RULE_NOT_IN_CATALOGUE"],
                    "missing_information": ["confirmation"],
                    "next_step": "Ask an expert",
                },
                {"RULE_EMAIL"},
            )

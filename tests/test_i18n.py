"""Checks that English and French reviewer copy stays complete."""

from __future__ import annotations

import unittest

from corroboria.i18n import DECISION_METHODS, PRIORITIES, TRANSLATIONS, VERDICTS, translate, translate_value


class TranslationTests(unittest.TestCase):
    def test_every_english_key_has_a_french_translation(self) -> None:
        self.assertEqual(set(TRANSLATIONS["en"]), set(TRANSLATIONS["fr"]))

    def test_result_labels_have_both_languages(self) -> None:
        self.assertEqual(set(VERDICTS["en"]), set(VERDICTS["fr"]))
        self.assertEqual(set(PRIORITIES["en"]), set(PRIORITIES["fr"]))
        self.assertEqual(set(DECISION_METHODS["en"]), set(DECISION_METHODS["fr"]))

    def test_french_case_copy_and_labels_are_available(self) -> None:
        self.assertEqual(
            translate_value("fr", "verdict", "Needs review"),
            "À examiner",
        )
        self.assertIn("Système B", translate("fr", "case_explanation_rule_anomaly", rule_id="RULE_EMAIL"))

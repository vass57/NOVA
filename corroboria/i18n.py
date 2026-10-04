"""Bilingual UI translations for CorroborIA."""

from __future__ import annotations

from typing import Final


LANGUAGES: Final = {
    "en": "English",
    "fr": "Français",
}


TRANSLATIONS: Final = {

    # ========================================================
    # ENGLISH
    # ========================================================

    "en": {

        "studio":
            "RECONCILIATION STUDIO",

        "appearance":
            "Appearance",

        "language":
            "Language",

        "light":
            "Light",

        "dark":
            "Dark",

        # ----------------------------------------------------
        # INPUTS
        # ----------------------------------------------------

        "input_step":
            "01 / Choose the trusted input set",

        "input_source":
            "Input source",

        "bundled":
            "Bundled challenge files",

        "custom":
            "My approved files",

        "bundled_ready":
            "Five bundled challenge files are ready.",

        "upload_help":
            (
                "Upload all five files. "
                "Data stays inside this local Streamlit process."
            ),

        "source_file":
            "System A - HR",

        "destination_file":
            "System B - Time",

        "mapping_file":
            "Mapping and rules",

        "job_file":
            "Job-detail history",

        "reasons_file":
            "Employment-reason lookup",

        "files_required":
            (
                "Five files are required before "
                "a custom run can start."
            ),

        # ----------------------------------------------------
        # HERO
        # ----------------------------------------------------

        "hero_ready":
            "Ready for a trusted reconciliation",

        "hero_results":
            "Results are ready to review",

        "hero_title":
            "Make every data difference make sense.",

        "hero_copy":
            (
                "CorroborIA combines deterministic business rules "
                "with local AI analysis to transform HR and "
                "time-management discrepancies into a traceable "
                "investigation workflow."
            ),

        "pill_deterministic":
            "Deterministic first",

        "pill_ai":
            "AI for ambiguity & prioritization",

        "pill_evidence":
            "Evidence on every case",

        "pill_private":
            "Local processing",

        # ----------------------------------------------------
        # WORKFLOW
        # ----------------------------------------------------

        "flow_input_title":
            "Choose inputs",

        "flow_input_copy":
            "Use challenge files or approved uploads.",

        "flow_run_title":
            "Run the engine",

        "flow_run_copy":
            (
                "Validate, normalize, match and apply "
                "the business-rule catalogue."
            ),

        "flow_triage_title":
            "Investigate",

        "flow_triage_copy":
            (
                "Separate real anomalies, justified "
                "differences and ambiguous cases."
            ),

        "flow_export_title":
            "Export evidence",

        "flow_export_copy":
            (
                "Share the report while preserving "
                "the complete audit trail."
            ),

        # ----------------------------------------------------
        # RUN
        # ----------------------------------------------------

        "run":
            "Run reconciliation",

        "local_first":
            (
                "Local-first workflow: raw files remain unchanged "
                "and AI analysis runs locally with no external "
                "data transfer."
            ),

        "running":
            (
                "Reading trusted inputs, normalizing values, "
                "matching assignments, applying business rules "
                "and running local AI analysis..."
            ),

        "validation_stopped":
            "Input validation stopped the run.",

        "ready_title":
            "Your investigation space is ready",

        "ready_copy":
            (
                "Choose the bundled files or upload an approved "
                "set, then run CorroborIA."
            ),

        # ----------------------------------------------------
        # TABS
        # ----------------------------------------------------

        "tab_overview":
            "Overview",

        "tab_queue":
            "Review queue",

        "tab_ai":
            "AI analysis",

        "tab_governance":
            "Governance & audit",

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        "pulse_kicker":
            "02 / Reconciliation pulse",

        "pulse_title":
            "What needs your attention?",

        "actual_note":
            "Deterministic mismatches",

        "review_note":
            "Ambiguous or limited evidence",

        "justified_note":
            (
                "Raw values differ but normalize "
                "to the same information"
            ),

        "match_note":
            "Approved values agree",

        "start_title":
            "A clear place to start",

        "start_copy":
            (
                "{count} high-priority case(s) require attention "
                "because of confirmed anomalies or unresolved "
                "matching evidence."
            ),

        "count_caption":
            (
                "Counts represent field comparisons and structural "
                "matching cases, not unique employees."
            ),

        # ----------------------------------------------------
        # REVIEW QUEUE
        # ----------------------------------------------------

        "triage_kicker":
            "03 / Triage",

        "triage_title":
            "Investigation queue",

        "tune_queue":
            "Tune the queue",

        "verdict":
            "Verdict",

        "field":
            "Field",

        "priority":
            "Priority",

        "rule":
            "Rule",

        "empty_queue":
            (
                "Nothing matches these filters. "
                "Adjust the controls to widen the view."
            ),

        "queue_count":
            (
                "{count:,} case(s) in this view. "
                "Select a case below to inspect its evidence."
            ),

        "case":
            "Case",

        "employee":
            "Employee",

        "why":
            "Why",

        # ----------------------------------------------------
        # CASE DETAILS
        # ----------------------------------------------------

        "evidence_kicker":
            "04 / Evidence",

        "evidence_title":
            "Case detail",

        "empty_evidence":
            "Choose a broader queue view to inspect a case.",

        "select_case":
            "Select a case to investigate",

        "decision_method":
            "Decision method",

        "source_evidence":
            "SYSTEM A / SOURCE EVIDENCE",

        "destination_evidence":
            "SYSTEM B / EXPECTED OUTCOME",

        "supporting":
            (
                "Supporting records, rule evidence, "
                "priority and AI status"
            ),

        "raw":
            "raw",

        "normalized":
            "normalized",

        "row":
            "row",

        "expected":
            "expected",

        "rule_ids":
            "rule IDs",

        "supporting_records":
            "supporting records",

        "priority_reason":
            "priority rationale",

        "confidence":
            "confidence",

        "limitation":
            "dataset limitation",

        "pattern":
            "pattern type",

        "ai_contributed":
            "AI contributed",

        "ai_status":
            "AI status",

        "ai_score":
            "AI score",

        "missing_id":
            "missing ID",

        # ----------------------------------------------------
        # EXPLANATIONS
        # ----------------------------------------------------

        "case_explanation_direct_match":
            (
                "The mapped source and destination values agree "
                "under the approved comparison logic."
            ),

        "case_explanation_direct_anomaly":
            (
                "The mapped source value differs from System B "
                "and no approved rule explains the discrepancy."
            ),

        "case_explanation_normalized":
            (
                "The raw representations differ, but approved "
                "normalization converts both values to the same "
                "meaning."
            ),

        "case_explanation_rule_match":
            (
                "Rule {rule_id} derives the expected System B "
                "value and confirms the destination data."
            ),

        "case_explanation_rule_anomaly":
            (
                "Rule {rule_id} derives an expected value that "
                "differs from System B."
            ),

        "case_explanation_rule_review":
            (
                "Rule {rule_id} cannot establish a reliable verdict "
                "from the available evidence."
            ),

        "case_explanation_matching":
            (
                "The available assignment records cannot be matched "
                "uniquely by deterministic rules."
            ),

        # ----------------------------------------------------
        # PRIORITY TEXT
        # ----------------------------------------------------

        "priority_anomaly":
            (
                "A deterministic expected value differs "
                "from System B."
            ),

        "priority_review":
            (
                "Matching or supporting evidence remains "
                "ambiguous or incomplete."
            ),

        "priority_justified":
            (
                "Approved normalization explains the apparent "
                "difference."
            ),

        "priority_match":
            (
                "The mapped values agree under the approved "
                "comparison logic."
            ),

        # ----------------------------------------------------
        # AI TAB
        # ----------------------------------------------------

        "ai_kicker":
            "Hybrid intelligence",

        "ai_title":
            "AI-assisted analysis",

        "ai_intro_title":
            "AI assists where deterministic logic stops",

        "ai_intro_copy":
            (
                "Business rules establish deterministic verdicts. "
                "Local machine-learning models are used only to "
                "assist ambiguous assignment matching, prioritize "
                "anomaly profiles and identify recurring patterns. "
                "AI never silently overrides a deterministic verdict."
            ),

        "ai_matching_kicker":
            "Ambiguous assignment resolution",

        "ai_matching_title":
            "Suggested one-to-one assignment matching",

        "ai_best_score":
            "Best matching score",

        "ai_second_score":
            "Alternative score",

        "ai_confidence":
            "Matching confidence",

        "ai_proposal":
            "AI-preferred matching: {pairs}",

        "ai_advisory":
            (
                "This is an advisory AI recommendation. "
                "The deterministic verdict remains Needs review "
                "until validated by a reviewer."
            ),

        "ai_matching_evidence":
            "Candidate-pair evidence",

        "ai_no_ambiguous":
            "No ambiguous assignment groups were detected.",

        "ai_priority_kicker":
            "Risk prioritization",

        "ai_priority_title":
            "Which employee profiles deserve attention first?",

        "ai_priority_chart":
            "Relative AI anomaly score by employee",

        "ai_no_priorities":
            "No AI prioritization output is available.",

        "ai_pattern_kicker":
            "Population patterns",

        "ai_pattern_title":
            "Systematic, recurrent and isolated discrepancies",

        "ai_pattern_chart":
            "Employee prevalence by affected field",

        "ai_no_patterns":
            "No recurring discrepancy patterns were detected.",

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        "handoff_kicker":
            "05 / Handoff",

        "handoff_title":
            "Export the evidence",

        "download_csv":
            "Filtered case CSV",

        "download_excel":
            "Full Excel report",

        "download_audit":
            "Run audit JSON",

        # ----------------------------------------------------
        # GOVERNANCE
        # ----------------------------------------------------

        "governance_kicker":
            "Review governance",

        "governance_title":
            "Expert feedback",

        "feedback_caption":
            (
                "Reviewer feedback is preserved separately. "
                "It never overwrites the deterministic result."
            ),

        "reviewer_verdict":
            "Reviewer verdict",

        "feedback_reason":
            "Why is this verdict appropriate?",

        "feedback_placeholder":
            (
                "Record the evidence or business context "
                "used in your decision."
            ),

        "save_feedback":
            "Save feedback",

        "reason_required":
            (
                "Add a reviewer reason so the feedback "
                "remains auditable."
            ),

        "feedback_saved":
            "Feedback added to this session's audit trail.",

        "download_feedback":
            "Download feedback audit",

        "mapping_evidence":
            "Mapping evidence",

        "run_audit":
            "Run audit",
    },

    # ========================================================
    # FRENCH
    # ========================================================

    "fr": {

        "studio":
            "ATELIER DE CORROBORATION",

        "appearance":
            "Apparence",

        "language":
            "Langue",

        "light":
            "Clair",

        "dark":
            "Sombre",

        # ----------------------------------------------------
        # INPUTS
        # ----------------------------------------------------

        "input_step":
            "01 / Choisir les données de confiance",

        "input_source":
            "Source des données",

        "bundled":
            "Fichiers du défi inclus",

        "custom":
            "Mes fichiers approuvés",

        "bundled_ready":
            "Les cinq fichiers du défi sont prêts.",

        "upload_help":
            (
                "Téléversez les cinq fichiers. "
                "Les données restent dans ce processus Streamlit local."
            ),

        "source_file":
            "Système A - RH",

        "destination_file":
            "Système B - Temps",

        "mapping_file":
            "Mapping et règles",

        "job_file":
            "Historique du détail du poste",

        "reasons_file":
            "Référentiel des motifs d'emploi",

        "files_required":
            (
                "Les cinq fichiers sont requis avant de lancer "
                "une corroboration personnalisée."
            ),

        # ----------------------------------------------------
        # HERO
        # ----------------------------------------------------

        "hero_ready":
            "Prêt pour une corroboration fiable",

        "hero_results":
            "Les résultats sont prêts à examiner",

        "hero_title":
            "Donnez un sens à chaque écart de données.",

        "hero_copy":
            (
                "CorroborIA combine des règles métier déterministes "
                "et une analyse IA locale afin de transformer les "
                "écarts entre les systèmes RH et Temps en une "
                "démarche d'investigation traçable."
            ),

        "pill_deterministic":
            "Déterministe d'abord",

        "pill_ai":
            "IA pour ambiguïté et priorité",

        "pill_evidence":
            "Preuves pour chaque dossier",

        "pill_private":
            "Traitement local",

        # ----------------------------------------------------
        # WORKFLOW
        # ----------------------------------------------------

        "flow_input_title":
            "Choisir les données",

        "flow_input_copy":
            "Utilisez les fichiers du défi ou des fichiers approuvés.",

        "flow_run_title":
            "Lancer le moteur",

        "flow_run_copy":
            (
                "Valider, normaliser, apparier et appliquer "
                "le catalogue de règles."
            ),

        "flow_triage_title":
            "Investiguer",

        "flow_triage_copy":
            (
                "Séparer les anomalies réelles, les écarts "
                "justifiés et les cas ambigus."
            ),

        "flow_export_title":
            "Exporter les preuves",

        "flow_export_copy":
            (
                "Partager le rapport tout en conservant "
                "la piste d'audit complète."
            ),

        # ----------------------------------------------------
        # RUN
        # ----------------------------------------------------

        "run":
            "Lancer la corroboration",

        "local_first":
            (
                "Traitement local : les fichiers sources restent "
                "inchangés et l'analyse IA s'exécute localement "
                "sans transfert externe de données."
            ),

        "running":
            (
                "Lecture des données, normalisation, appariement "
                "des affectations, application des règles et "
                "analyse IA locale..."
            ),

        "validation_stopped":
            "La validation des données a interrompu le traitement.",

        "ready_title":
            "Votre espace d'analyse est prêt",

        "ready_copy":
            (
                "Choisissez les fichiers inclus ou téléversez un "
                "ensemble approuvé, puis lancez CorroborIA."
            ),

        # ----------------------------------------------------
        # TABS
        # ----------------------------------------------------

        "tab_overview":
            "Vue d'ensemble",

        "tab_queue":
            "File de revue",

        "tab_ai":
            "Analyse IA",

        "tab_governance":
            "Gouvernance et audit",

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        "pulse_kicker":
            "02 / Pouls de la corroboration",

        "pulse_title":
            "Qu'est-ce qui demande votre attention?",

        "actual_note":
            "Écarts déterministes",

        "review_note":
            "Preuves ambiguës ou limitées",

        "justified_note":
            (
                "Les valeurs brutes diffèrent, mais deviennent "
                "équivalentes après normalisation"
            ),

        "match_note":
            "Les valeurs concordent",

        "start_title":
            "Un point de départ clair",

        "start_copy":
            (
                "{count} dossier(s) de priorité élevée nécessitent "
                "une attention en raison d'anomalies confirmées ou "
                "de preuves d'appariement non résolues."
            ),

        "count_caption":
            (
                "Les comptes représentent des comparaisons de champs "
                "et des dossiers structurels, pas des employés uniques."
            ),

        # ----------------------------------------------------
        # REVIEW QUEUE
        # ----------------------------------------------------

        "triage_kicker":
            "03 / Triage",

        "triage_title":
            "File d'investigation",

        "tune_queue":
            "Affiner la file",

        "verdict":
            "Verdict",

        "field":
            "Champ",

        "priority":
            "Priorité",

        "rule":
            "Règle",

        "empty_queue":
            (
                "Aucun dossier ne correspond à ces filtres. "
                "Ajustez les contrôles."
            ),

        "queue_count":
            (
                "{count:,} dossier(s) dans cette vue. "
                "Sélectionnez un dossier pour examiner les preuves."
            ),

        "case":
            "Dossier",

        "employee":
            "Employé",

        "why":
            "Motif",

        # ----------------------------------------------------
        # DETAILS
        # ----------------------------------------------------

        "evidence_kicker":
            "04 / Preuves",

        "evidence_title":
            "Détail du dossier",

        "empty_evidence":
            "Élargissez la file pour examiner un dossier.",

        "select_case":
            "Sélectionner un dossier à analyser",

        "decision_method":
            "Méthode de décision",

        "source_evidence":
            "SYSTÈME A / PREUVES SOURCE",

        "destination_evidence":
            "SYSTÈME B / RÉSULTAT ATTENDU",

        "supporting":
            (
                "Preuves justificatives, règles, priorité "
                "et statut IA"
            ),

        "raw":
            "brute",

        "normalized":
            "normalisée",

        "row":
            "ligne",

        "expected":
            "attendue",

        "rule_ids":
            "identifiants de règle",

        "supporting_records":
            "preuves justificatives",

        "priority_reason":
            "justification de la priorité",

        "confidence":
            "confiance",

        "limitation":
            "limitation du jeu de données",

        "pattern":
            "type de tendance",

        "ai_contributed":
            "contribution de l'IA",

        "ai_status":
            "statut IA",

        "ai_score":
            "score IA",

        "missing_id":
            "identifiant manquant",

        # ----------------------------------------------------
        # EXPLANATIONS
        # ----------------------------------------------------

        "case_explanation_direct_match":
            (
                "Les valeurs mappées des systèmes A et B "
                "concordent selon la logique approuvée."
            ),

        "case_explanation_direct_anomaly":
            (
                "La valeur source mappée diffère de la valeur "
                "du système B et aucune règle ne justifie l'écart."
            ),

        "case_explanation_normalized":
            (
                "Les représentations brutes diffèrent, mais la "
                "normalisation approuvée produit une information "
                "équivalente."
            ),

        "case_explanation_rule_match":
            (
                "La règle {rule_id} calcule la valeur attendue "
                "et confirme les données du système B."
            ),

        "case_explanation_rule_anomaly":
            (
                "La règle {rule_id} calcule une valeur attendue "
                "qui diffère du système B."
            ),

        "case_explanation_rule_review":
            (
                "La règle {rule_id} ne permet pas d'établir un "
                "verdict fiable avec les preuves disponibles."
            ),

        "case_explanation_matching":
            (
                "Les affectations disponibles ne peuvent pas être "
                "appariées de façon unique par les règles "
                "déterministes."
            ),

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        "priority_anomaly":
            (
                "Une valeur attendue déterministe diffère "
                "du système B."
            ),

        "priority_review":
            (
                "L'appariement ou les preuves demeurent "
                "ambigus ou incomplets."
            ),

        "priority_justified":
            (
                "La normalisation approuvée explique "
                "l'écart apparent."
            ),

        "priority_match":
            (
                "Les valeurs mappées concordent selon "
                "la logique approuvée."
            ),

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        "ai_kicker":
            "Intelligence hybride",

        "ai_title":
            "Analyse assistée par l'IA",

        "ai_intro_title":
            "L'IA intervient lorsque les règles déterministes s'arrêtent",

        "ai_intro_copy":
            (
                "Les règles métier établissent les verdicts "
                "déterministes. Les modèles locaux servent uniquement "
                "à assister l'appariement ambigu, prioriser les profils "
                "d'anomalies et identifier les tendances récurrentes. "
                "L'IA ne remplace jamais silencieusement un verdict "
                "déterministe."
            ),

        "ai_matching_kicker":
            "Résolution d'appariement ambigu",

        "ai_matching_title":
            "Suggestion d'appariement biunivoque",

        "ai_best_score":
            "Score du meilleur appariement",

        "ai_second_score":
            "Score de l'alternative",

        "ai_confidence":
            "Confiance d'appariement",

        "ai_proposal":
            "Appariement privilégié par l'IA : {pairs}",

        "ai_advisory":
            (
                "Cette proposition IA est consultative. "
                "Le verdict déterministe demeure À examiner "
                "jusqu'à validation humaine."
            ),

        "ai_matching_evidence":
            "Preuves des paires candidates",

        "ai_no_ambiguous":
            "Aucun groupe d'affectations ambiguës n'a été détecté.",

        "ai_priority_kicker":
            "Priorisation des risques",

        "ai_priority_title":
            "Quels profils devraient être examinés en premier?",

        "ai_priority_chart":
            "Score relatif d'anomalie IA par employé",

        "ai_no_priorities":
            "Aucune priorisation IA n'est disponible.",

        "ai_pattern_kicker":
            "Tendances populationnelles",

        "ai_pattern_title":
            "Écarts systématiques, récurrents et isolés",

        "ai_pattern_chart":
            "Prévalence par champ touché",

        "ai_no_patterns":
            "Aucune tendance récurrente n'a été détectée.",

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        "handoff_kicker":
            "05 / Transmission",

        "handoff_title":
            "Exporter les preuves",

        "download_csv":
            "CSV des dossiers filtrés",

        "download_excel":
            "Rapport Excel complet",

        "download_audit":
            "Audit JSON",

        # ----------------------------------------------------
        # GOVERNANCE
        # ----------------------------------------------------

        "governance_kicker":
            "Gouvernance de la revue",

        "governance_title":
            "Rétroaction experte",

        "feedback_caption":
            (
                "La rétroaction est conservée séparément et ne "
                "remplace jamais le résultat déterministe."
            ),

        "reviewer_verdict":
            "Verdict de l'expert",

        "feedback_reason":
            "Pourquoi ce verdict est-il approprié?",

        "feedback_placeholder":
            (
                "Consignez les preuves ou le contexte métier "
                "utilisés pour la décision."
            ),

        "save_feedback":
            "Enregistrer la rétroaction",

        "reason_required":
            (
                "Ajoutez un motif afin que la rétroaction "
                "demeure auditable."
            ),

        "feedback_saved":
            "La rétroaction a été ajoutée à la piste d'audit.",

        "download_feedback":
            "Télécharger l'audit de rétroaction",

        "mapping_evidence":
            "Preuves du mapping",

        "run_audit":
            "Audit d'exécution",
    },
}


# ============================================================
# VERDICTS
# ============================================================

VERDICTS: Final = {

    "en": {
        "Actual anomaly":
            "Actual anomaly",

        "Needs review":
            "Needs review",

        "Justified difference":
            "Justified difference",

        "Match":
            "Match",
    },

    "fr": {
        "Actual anomaly":
            "Anomalie réelle",

        "Needs review":
            "À examiner",

        "Justified difference":
            "Écart justifié",

        "Match":
            "Concordance",
    },
}


# ============================================================
# PRIORITIES
# ============================================================

PRIORITIES: Final = {

    "en": {
        "High":
            "High",

        "Medium":
            "Medium",

        "Low":
            "Low",
    },

    "fr": {
        "High":
            "Élevée",

        "Medium":
            "Moyenne",

        "Low":
            "Faible",
    },
}


# ============================================================
# METHODS
# ============================================================

DECISION_METHODS: Final = {

    "en": {
        "direct comparison":
            "Direct comparison",

        "deterministic business rule":
            "Deterministic business rule",

        "employee matching":
            "Employee matching",

        "assignment matching":
            "Assignment matching",

        "input validation":
            "Input validation",
    },

    "fr": {
        "direct comparison":
            "Comparaison directe",

        "deterministic business rule":
            "Règle métier déterministe",

        "employee matching":
            "Appariement des employés",

        "assignment matching":
            "Appariement des affectations",

        "input validation":
            "Validation des données",
    },
}


# ============================================================
# TRANSLATION FUNCTIONS
# ============================================================

def translate(
    locale: str,
    key: str,
    **values: object,
) -> str:
    """Return translated UI copy."""

    return (
        TRANSLATIONS[
            locale
        ][
            key
        ].format(
            **values
        )
    )


def translate_value(
    locale: str,
    group: str,
    value: str,
) -> str:
    """Translate known pipeline labels."""

    catalogues = {
        "verdict":
            VERDICTS,

        "priority":
            PRIORITIES,

        "method":
            DECISION_METHODS,
    }

    return (
        catalogues[
            group
        ][
            locale
        ].get(
            value,
            value,
        )
    )
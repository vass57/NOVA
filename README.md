# CorroborIA

CorroborIA is a local, explainable reconciliation prototype for the supplied HR (System A) and time-management (System B) extracts. It keeps source files read-only, preserves raw and normalized values, applies deterministic rules before any optional AI review, and exports the evidence behind every result.

## Run it

Use Python 3.11 or later.

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m streamlit run app.py
```

The interface opens with the supplied five files selected. It also accepts a complete replacement set of approved challenge files. Use the **Run reconciliation** button, review the default anomaly and review queue, inspect a case, and download CSV, Excel, or the run audit.

For a non-interactive report:

```powershell
py -3.14 main.py --output-dir reports
```

## Confirmed inputs and relationships

The repository contains no separate challenge brief or glossary, so `data/Mapping.xlsx` is the authority used by the implementation.

- Employee identity: `Matricule` (System A) maps to `personId` (System B).
- Employees can have multiple records. Assignment matching uses the mapping’s `P`/`A`/`S` semantics: System A `TypeAffectation` and System B `isPrimaryAssignment` plus `isTemporaryAssignment`. Multiple candidates of the same type remain unresolved instead of being forced together.
- The job-detail input is a comma-separated payload stored in one Excel column. It is parsed in memory and joined using the supplied position, employment, and administrative-unit fields.
- Employment status uses the supplied status table and employment-reason lookup. The lookup combines the source employment-reason and access-status codes.
- Only the 13 direct mappings in the Mapping sheet are compared directly. The deterministic catalogue covers the workbook rules for email, division and position names, employment status, contract type, assignment flags, and effective-dated assignment/term dates.

## Decision model

| Result | Meaning |
| --- | --- |
| Match | Values agree under direct approved comparison logic. |
| Justified difference | A deterministic mapping rule derives the destination value. |
| Actual anomaly | A mapped or derived expected value is known and differs from the destination value. |
| Needs review | Matching or required evidence is missing or ambiguous. |

Every case includes raw and normalized values, an expected value where determinable, rule identifiers, mapping row references, explanation, matching evidence, decision method, and explainable priority. The priority only reflects deterministic impact and recurrence; it does not claim a confidence percentage.

## Architecture

`corroboria/pipeline.py` orchestrates loading, validation, normalization, matching, rule evaluation, final verdicts, and run hashes. The existing focused modules provide normalization, mapping parsing, matching, direct comparison, and deterministic rule calculations. `app.py` is the Streamlit review interface, while `corroboria/export.py` creates reports in memory so input data is never modified.

The source files are loaded with `dtype=object`; identifier columns are treated as text after loading so meaningful leading zeroes are not discarded during normalization. Normalization is limited to whitespace, missing values, date representation, approved boolean labels, and numeric quantities.

## AI boundary and privacy

AI is disabled by default and no input data leaves the local application. `corroboria/ai.py` provides a validator for a future challenge-approved provider. It accepts structured suggestions only, checks referenced rule identifiers, and rejects an AI attempt to label a case a justified difference. A valid suggestion is still advice: deterministic verdicts remain unchanged and unresolved cases remain **Needs review** until an expert records feedback.

## Assumptions and limitations

- The current workbook layout is validated by required columns and the Mapping workbook must retain its four authority worksheets.
- The source mapping refers to HR labels such as `PERM_IND`, `FT_IND`, and `EMPTP_CD`; these are implemented through their mapped extract fields `EstPermanent`, `EstTempsPlein`, and `CatégorieEmploi`.
- No automated correction is made. Review feedback is stored only for the active Streamlit session and exported as a separate audit CSV.
- The prototype does not activate feedback-suggested rules or connect to an external AI provider. An approved provider and persistent, access-controlled audit store are required before production use.

## Validation

```powershell
py -3.14 -m unittest discover -s tests -v
```

The integration tests exercise the supplied data’s matching cases, deterministic rule-driven differences, direct anomalies, ambiguous or unmatched records, report exports, and rejected unsupported AI output.

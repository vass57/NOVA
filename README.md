CorroborIA is a reconciliation application created for the Loto-Québec Détection intelligente des écarts challenge.
It compares employee information from System A - HR and System B - Time and helps determine whether a difference is normal, justified, a real anomaly, or something that should be reviewed.


After running the reconciliation, CorroborIA groups results into four categories:
- Match
  The information in both systems agrees.

- Justified difference
  The values look different, but after normalization they represent the same information.

- Actual anomaly
  The expected value is known, but System B contains a different value.

- Needs review
  The case cannot be resolved safely using deterministic rules alone.


How to use the site
1. Choose the files
In the sidebar, you can either:
- use the bundled challenge files;
- upload your own approved files.
The application uses the source file, destination file, mapping file, job-detail file and employment-reason file.
2. Run the reconciliation
Click Run reconciliation.
CorroborIA will process the files and display the results in the main dashboard.
The original source files are not modified.
Overview tab
The Overview tab gives a quick summary of the reconciliation.
It shows how many cases are:
- matches;
- justified differences;
- actual anomalies;
- still in need of review.
This gives the user an immediate idea of how much of the data is correct and how much needs attention.
Review Queue tab
The Review Queue is where individual cases can be investigated.
Cases can be filtered by:
- verdict;
- field;
- priority;
- rule.
When a case is selected, CorroborIA shows:
- the employee;
- the field being compared;
- the final verdict;
- the decision method;
- the priority;
- the System A value;
- the System B value;
- the normalized values;
- the expected value when applicable;
- the explanation for the result;
- supporting information used to make the decision.

The goal is to make every result understandable without having to manually search through the original spreadsheets.
Structural assignment cases
CorroborIA can also detect when an entire assignment is missing.
This makes it easy to see that the issue is not simply one incorrect field, but a missing assignment record.
AI Analysis tab

The AI Analysis tab is used for cases where extra analysis is useful.
It includes:
Assignment matching
If multiple assignments could match each other, the AI suggests the most likely one-to-one pairing.
The recommendation is shown to the user, but the case remains Needs review until it is confirmed.
Prioritization

CorroborIA also ranks employee anomaly profiles so that the most unusual cases can be investigated first.
Pattern detection

The site identifies whether a discrepancy appears to be:
- Systematic
- Recurrent
- Isolated

This helps show whether a problem affects one employee or appears across many records.
Governance & Audit tab
The Governance & Audit tab provides additional transparency.
It allows the user to:
- review the mapping used by the system;
- see run-level audit information;
- confirm that source files were treated as read-only;
- view file fingerprints;
- record reviewer feedback.
Reviewer feedback is stored separately so that the original CorroborIA result is preserved.

Language and theme
The site can be displayed in:
- English;
- French.
It also supports:
- Light mode;
- Dark mode.

These settings only affect the interface and do not change the reconciliation results.

Exports
CorroborIA allows users to download the results in several formats:
- Filtered CSV for the current review list;
- Excel report containing the full reconciliation results;
- JSON audit file containing run information;
- Reviewer feedback CSV.
This makes it possible to continue the investigation outside the application.

Running the application
Install the required packages:
py -m pip install -r requirements.txt
Launch CorroborIA:
py -m streamlit run app.py

Quality check
The project includes an automated QA check:
py qa_check.py
Current result:
ALL QA CHECKS PASSED

The validated result is:
406 Match
20 Justified difference
55 Actual anomaly
21 Needs review
502 total

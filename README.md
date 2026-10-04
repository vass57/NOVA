CorroborIA
CorroborIA is an intelligent reconciliation application built for the Loto-Québec Détection intelligente des écarts challenge.
It compares employee data from:
- System A - HR
- System B - Time
and determines whether each difference is:
- Match
- Justified difference
- Actual anomaly
- Needs review
The goal is not simply to detect differences. CorroborIA explains whether a difference actually matters, why it exists, and what should be investigated.
What the site does
CorroborIA guides the user through the full reconciliation process.
It can:
- load the five approved challenge files;
- normalize dates, numbers, booleans, identifiers and text;
- match employees and assignments;
- apply the supplied business rules;
- detect direct mismatches;
- recognize harmless representation differences;
- detect missing assignments;
- flag unresolved cases;
- use local AI to assist ambiguous assignment matching;
- prioritize unusual anomaly profiles;
- identify systematic, recurrent and isolated discrepancy patterns;
- show supporting evidence for every case;
- collect reviewer feedback;
- export the results and audit trail.
The original source files remain unchanged.
Using the application
Launch the site with:
py -m streamlit run app.py
The sidebar allows the user to:
- select the bundled challenge files or upload an approved file set;
- switch between English and French;
- switch between Light and Dark mode;
- run the reconciliation.
Overview
After the reconciliation runs, the Overview tab shows the final result.
For the supplied challenge dataset:
Verdict	Count
Match	406
Justified difference	20
Actual anomaly	55
Needs review	21
Total	502


These counts represent field comparisons and structural assignment cases, not unique employees.
The four verdicts
Match
The approved source and destination values agree.
Justified difference
The raw values look different, but normalization shows they represent the same information.
Example:
System A: 1995-02-09 00:00:00
System B: 1995-02-09T00:00:00.000Z
Normalized: 1995-02-09
This avoids false anomalies caused by formatting differences.
Actual anomaly
CorroborIA can determine the expected value, but System B contains something different.
Example:
Expected weekly hours: 35
System B weekly hours: 40
Needs review
The available evidence is not strong enough for a safe deterministic decision.
This includes ambiguous assignment matches and known anonymization limitations.
Review queue
The Review queue is the main investigation workspace.
Cases can be filtered by:
- verdict;
- field;
- priority;
- rule.
Selecting a case shows:
- verdict;
- decision method;
- priority;
- System A evidence;
- System B evidence;
- raw values;
- normalized values;
- expected values;
- source and destination rows;
- rule evidence;
- AI information when applicable.
Structural cases are also shown clearly. For example:
SYSTEM A
Present
Assignment type: A

SYSTEM B
Missing
Assignment type: A
This makes missing whole assignments easy to understand.
AI-assisted analysis
AI is used as an assistance layer, not as a replacement for deterministic rules.
The AI analysis tab contains three functions:
1. Ambiguous assignment matching
When deterministic rules cannot uniquely match multiple assignments, CorroborIA evaluates the possible one-to-one pairings.
For the supplied challenge case, AI prefers:
Source 21 → Destination 21
Source 22 → Destination 19
The deterministic verdict still remains Needs review until a reviewer confirms the proposal.
2. Anomaly prioritization
CorroborIA ranks employee anomaly profiles so investigators can focus on the most unusual cases first.
Priority affects investigation order only. It does not change the deterministic verdict.
3. Pattern analysis
Discrepancies are categorized as:
- Systematic
- Recurrent
- Isolated
This helps distinguish a single employee problem from a system-wide transformation issue.
AI validation
The assignment-matching model was tested using leave-one-confirmed-match-out validation.
Result:
Confirmed pairs evaluated: 20
Top-1 ranking accuracy: 20/20 (100.0%)
Mean Reciprocal Rank: 1.000
The sample is small, so this result applies to the supplied challenge dataset and should not be interpreted as universal production accuracy.
The ambiguous secondary-assignment case is not used as validation ground truth.
Governance and audit
The Governance & audit tab provides:
- reviewer feedback;
- mapping evidence;
- run-level audit information;
- input-file fingerprints;
- read-only confirmation;
- AI configuration details.
Reviewer feedback is stored separately and never overwrites the original deterministic result.
CorroborIA also calculates SHA-256 fingerprints for the input files, making each run traceable to the exact files used.
Exports
The application provides:
- filtered CSV export;
- full Excel report;
- JSON run audit;
- reviewer feedback CSV.
The Excel report includes summary, investigation, mapping, matching, AI, and audit information.
Quality assurance
Run:
py qa_check.py
Current result:
Bundled data.................. PASS
Structural anomaly............ PASS
AI outputs.................... PASS
Export files.................. PASS
Simulated file uploads........ PASS
Bundled vs uploaded results... PASS

ALL QA CHECKS PASSED
Privacy
All machine-learning analysis runs locally with scikit-learn.
No challenge employee data are sent to an external AI provider.
Core principle
CorroborIA does not ask:
Are these two raw values identical?

It asks:
Do they represent the same information, can the difference be explained by an approved business rule, or does it require investigation?

That is what turns a raw comparison into an explainable and actionable reconciliation workflow.
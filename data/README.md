# Data dictionary

`processed/trials.csv`: one row per trial, from ClinicalTrials.gov API v2. `bci_trials.csv` has the same columns, for BCI-related trials only.

| Column | Meaning |
|---|---|
| nct_id | Unique trial ID on ClinicalTrials.gov |
| title | Short trial title |
| lead_sponsor | Organization running the trial |
| sponsor_class | INDUSTRY, OTHER (universities, hospitals), FED, NIH, etc. |
| study_type | Always INTERVENTIONAL after filtering |
| overall_status | Completed, recruiting, terminated, unknown, etc. |
| start_date | Trial start (actual or planned) |
| primary_completion_date | Date main results were or will be collected |
| conditions | Conditions as listed by the sponsor |
| searched_conditions | Which of our 10 searches found the trial |
| device_names | Names of the device interventions |
| phases | Trial phase; usually NA for device trials |
| enrollment | Number of participants |
| allocation | RANDOMIZED, NON_RANDOMIZED, or NA (single arm) |
| num_sites | Number of trial locations |
| fda_regulated_device | Sponsor declared the device is FDA-regulated |
| has_results | Whether results were posted |
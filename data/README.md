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

## `processed/fda_decisions.csv`
One row per FDA decision on a Neurology-panel device, from openFDA.

| Column | Meaning |
|---|---|
| submission_number | FDA ID: P… (PMA), K… (510(k)), DEN… (De Novo) |
| pathway | PMA, De Novo or 510(k) |
| applicant | Company that submitted |
| device_name | Device trade name |
| generic_name | Generic device type (PMA only) |
| product_code | FDA 3-letter device type code |
| date_received / decision_date | Submission and decision dates |
| decision_code | FDA outcome code (e.g., SESE = cleared, DENG = De Novo granted) |
| expedited_review | Whether review was expedited |
| device_class | FDA risk class (1–3) |
| n_supplements | Number of follow-up approvals (PMA only) |
| review_days | Days from submission to decision |
| decision_year | Year of decision |

## `processed/novel_devices_labels.csv`
Hand labels for the 95 De Novo and PMA devices.

| Column | Meaning |
|---|---|
| category | Device type: implanted_neurostim, external_neurostim, brain_signal, neurovascular, diagnostic_other, digital_therapeutic, other_neuro, not_neuro |
| include | yes if a genuine neuro device; no if misfiled |
| bci_narrow | bci / partial under the narrow BCI definition (see main README) |
| bci_broad | bci / partial under the broad BCI definition |
| notes | One-line description of the device |

`processed/bci_trials.csv`: same columns as `trials.csv`, for the 66 BCI-related trials.
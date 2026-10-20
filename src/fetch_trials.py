"""
fetch_trials.py

Downloads neurological device trials from ClinicalTrials.gov (API v2)
and saves them as one clean table, one row per trial.

Run from the project folder, with the bci environment active:
    python src/fetch_trials.py

Outputs:
    data/raw/<condition>.json     raw API responses (ignored by Git)
    data/processed/trials.csv     one row per unique trial
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests


# ------------------------------------------------------------------
# 1. Settings
# ------------------------------------------------------------------
API_URL = "https://clinicaltrials.gov/api/v2/studies"

# The conditions defined in the README scope
CONDITIONS = [
    "epilepsy",
    "Parkinson disease",
    "essential tremor",
    "chronic pain",
    "depression",
    "migraine",
    "obstructive sleep apnea",
    "stroke",
    "spinal cord injury",
    "amyotrophic lateral sclerosis",
]

PAGE_SIZE = 1000      # the most trials the API returns per request
PAUSE_SECONDS = 0.5   # short wait between requests, to be polite to the server
MAX_RETRIES = 3       # how many times to retry a failed request

# Folder paths, worked out from where this script lives (src/),
# so the script works no matter which folder you run it from
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ------------------------------------------------------------------
# 2. Downloading
# ------------------------------------------------------------------
def get_page(params):
    """Request one page of results, retrying a few times if it fails."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()   # turns HTTP errors (e.g. 500) into exceptions
            return response.json()
        except requests.RequestException as error:
            print(f"   Attempt {attempt} failed: {error}")
            time.sleep(2 * attempt)       # wait a little longer each time
    raise RuntimeError("API request failed after several attempts.")


def fetch_condition(condition):
    """Download every device trial for one condition, page by page."""
    params = {
        "query.cond": condition,
        "filter.advanced": "AREA[InterventionType]DEVICE",
        "pageSize": PAGE_SIZE,
        "format": "json",
    }
    studies = []
    while True:
        data = get_page(params)
        studies.extend(data.get("studies", []))

        # The API includes nextPageToken while more pages remain
        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
        time.sleep(PAUSE_SECONDS)
    return studies


# ------------------------------------------------------------------
# 3. Flattening: nested JSON -> one flat row per trial
# ------------------------------------------------------------------
def flatten(study, searched_condition):
    """Pull the fields we need out of one trial's nested JSON."""
    s = study.get("protocolSection", {})
    ident = s.get("identificationModule", {})
    status = s.get("statusModule", {})
    sponsor = s.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    oversight = s.get("oversightModule", {})
    conds = s.get("conditionsModule", {})
    design = s.get("designModule", {})
    arms = s.get("armsInterventionsModule", {})
    locations = s.get("contactsLocationsModule", {}).get("locations", [])

    device_names = [
        i.get("name", "")
        for i in arms.get("interventions", [])
        if i.get("type") == "DEVICE"
    ]

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "lead_sponsor": sponsor.get("name"),
        "sponsor_class": sponsor.get("class"),          # INDUSTRY, OTHER (e.g. university), NIH...
        "study_type": design.get("studyType"),
        "overall_status": status.get("overallStatus"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "primary_completion_date": status.get("primaryCompletionDateStruct", {}).get("date"),
        "conditions": "; ".join(conds.get("conditions", [])),
        "searched_condition": searched_condition,
        "device_names": "; ".join(device_names),
        "phases": "; ".join(design.get("phases", [])),
        "enrollment": design.get("enrollmentInfo", {}).get("count"),
        "allocation": design.get("designInfo", {}).get("allocation"),
        "num_sites": len(locations),
        "fda_regulated_device": oversight.get("isFdaRegulatedDevice"),
        "has_results": study.get("hasResults"),
    }


# ------------------------------------------------------------------
# 4. Main: run everything
# ------------------------------------------------------------------
def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for condition in CONDITIONS:
        print(f"Fetching: {condition}")
        studies = fetch_condition(condition)
        print(f"   {len(studies)} trials found")

        # Save the raw download, so we never need to re-download to re-process
        raw_file = RAW_DIR / f"{condition.lower().replace(' ', '_')}.json"
        raw_file.write_text(json.dumps(studies), encoding="utf-8")

        rows.extend(flatten(study, condition) for study in studies)

    trials = pd.DataFrame(rows)

    # Keep interventional studies only (drops observational and expanded access)
    trials = trials[trials["study_type"] == "INTERVENTIONAL"]

    # One trial can match several conditions (e.g. stroke AND depression).
    # Keep one row per trial, and record every condition search that found it.
    matched = (
        trials.groupby("nct_id")["searched_condition"]
        .apply(lambda x: "; ".join(sorted(set(x))))
    )
    trials = trials.drop_duplicates("nct_id").drop(columns="searched_condition")
    trials["searched_conditions"] = trials["nct_id"].map(matched)

    out_file = PROCESSED_DIR / "trials.csv"
    trials.to_csv(out_file, index=False)
    print(f"\nSaved {len(trials)} unique trials to {out_file}")


if __name__ == "__main__":
    main()

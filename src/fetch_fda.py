"""
fetch_fda.py

Downloads FDA decisions on neurological devices from openFDA and saves
them as one clean table, one row per FDA decision.

Covers three pathways, all reviewed by the FDA's Neurology panel ("NE"):
    PMA      high-risk devices (original approvals only, not supplements)
    De Novo  novel moderate-risk devices (found inside the 510(k) data)
    510(k)   moderate-risk devices similar to an existing device

Run from the project folder, with the bci environment active:
    python src/fetch_fda.py

Outputs:
    data/raw/fda_pma.json, data/raw/fda_510k.json   raw downloads (ignored by Git)
    data/processed/fda_decisions.csv                one row per FDA decision
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests


# ------------------------------------------------------------------
# 1. Settings
# ------------------------------------------------------------------
PMA_URL = "https://api.fda.gov/device/pma.json"
K510_URL = "https://api.fda.gov/device/510k.json"
SEARCH = "advisory_committee:NE"   # the FDA Neurology review panel

PAGE_SIZE = 1000      # the most records openFDA returns per request
PAUSE_SECONDS = 0.5
MAX_RETRIES = 3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ------------------------------------------------------------------
# 2. Downloading
# ------------------------------------------------------------------
def get_page(url, params):
    """Request one page, retrying if the connection fails.

    openFDA answers with an error (and no "results") once we ask for
    records past the end, so that case returns an empty list.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            if response.status_code == 404:     # "no more matches"
                return []
            response.raise_for_status()
            return data.get("results", [])
        except (requests.RequestException, ValueError) as error:
            print(f"   Attempt {attempt} failed: {error}")
            time.sleep(2 * attempt)
    raise RuntimeError("openFDA request failed after several attempts.")


def fetch_all(url):
    """Download every neuro record from one openFDA endpoint, page by page."""
    records = []
    skip = 0
    while True:
        page = get_page(url, {"search": SEARCH, "limit": PAGE_SIZE, "skip": skip})
        if not page:
            break
        records.extend(page)
        skip += PAGE_SIZE
        time.sleep(PAUSE_SECONDS)
    return records


# ------------------------------------------------------------------
# 3. Shaping each pathway into the same columns
# ------------------------------------------------------------------
def shape_pma(records):
    """Keep original PMA approvals, and count each one's supplements."""
    pma = pd.DataFrame(records)
    pma["supplement_number"] = pma["supplement_number"].fillna("")

    # How many follow-up supplements each device has had (a rough
    # signal of how long and actively it has been on the market)
    supplements = (
        pma[pma["supplement_number"] != ""]
        .groupby("pma_number")
        .size()
    )

    originals = pma[pma["supplement_number"] == ""].copy()
    return pd.DataFrame({
        "submission_number": originals["pma_number"],
        "pathway": "PMA",
        "applicant": originals["applicant"],
        "device_name": originals["trade_name"],
        "generic_name": originals["generic_name"],
        "product_code": originals["product_code"],
        "date_received": originals["date_received"],
        "decision_date": originals["decision_date"],
        "decision_code": originals["decision_code"],
        "expedited_review": originals["expedited_review_flag"],
        "device_class": originals["openfda"].apply(
            lambda o: o.get("device_class") if isinstance(o, dict) else None
        ),
        "n_supplements": originals["pma_number"].map(supplements).fillna(0).astype(int),
    })


def shape_510k(records):
    """Shape 510(k) records; De Novo grants are the rows coded DENG."""
    k = pd.DataFrame(records)
    return pd.DataFrame({
        "submission_number": k["k_number"],
        "pathway": k["decision_code"].map(lambda c: "De Novo" if c == "DENG" else "510(k)"),
        "applicant": k["applicant"],
        "device_name": k["device_name"],
        "generic_name": None,
        "product_code": k["product_code"],
        "date_received": k["date_received"],
        "decision_date": k["decision_date"],
        "decision_code": k["decision_code"],
        "expedited_review": k.get("expedited_review_flag"),
        "device_class": k["openfda"].apply(
            lambda o: o.get("device_class") if isinstance(o, dict) else None
        ),
        "n_supplements": None,
    })


# ------------------------------------------------------------------
# 4. Main: run everything
# ------------------------------------------------------------------
def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching PMA records...")
    pma_records = fetch_all(PMA_URL)
    print(f"   {len(pma_records)} records (originals + supplements)")
    (RAW_DIR / "fda_pma.json").write_text(json.dumps(pma_records), encoding="utf-8")

    print("Fetching 510(k) records (includes De Novo)...")
    k_records = fetch_all(K510_URL)
    print(f"   {len(k_records)} records")
    (RAW_DIR / "fda_510k.json").write_text(json.dumps(k_records), encoding="utf-8")

    decisions = pd.concat([shape_pma(pma_records), shape_510k(k_records)], ignore_index=True)

    # Review time: days from FDA receiving the submission to its decision
    received = pd.to_datetime(decisions["date_received"], errors="coerce")
    decided = pd.to_datetime(decisions["decision_date"], errors="coerce")
    decisions["review_days"] = (decided - received).dt.days
    decisions["decision_year"] = decided.dt.year

    decisions = decisions.sort_values("decision_date")
    out_file = PROCESSED_DIR / "fda_decisions.csv"
    decisions.to_csv(out_file, index=False)

    print(f"\nSaved {len(decisions)} FDA decisions to {out_file}")
    print(decisions["pathway"].value_counts().to_string())


if __name__ == "__main__":
    main()

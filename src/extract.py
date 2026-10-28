"""
Extract: pull street-level crime data from the data.police.uk API.

For each of a small set of fixed locations, fetch all street-level crimes
for the latest 3 months the API has data for, and save the raw JSON
responses untouched into data/raw/ so the rest of the pipeline (and anyone
reviewing this project) can work from exactly what the API returned.

API docs: https://data.police.uk/docs/  (keyless, free)
"""
import json
import time
from pathlib import Path

import requests

BASE_URL = "https://data.police.uk/api"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
N_MONTHS = 3

# Fixed points of interest: (slug, display name, lat, lng)
# The street-crime endpoint returns crimes within roughly one mile.
LOCATIONS = [
    ("bristol_city_centre", "Bristol City Centre", 51.4545, -2.5879),
    ("bristol_fishponds", "Bristol Fishponds", 51.4780, -2.5350),
    ("london_bank", "London Bank (Watling Street area)", 51.5138, -0.0886),
    ("london_shoreditch", "London Shoreditch", 51.5265, -0.0825),
]


def get_json(url, params=None, retries=3, backoff=2.0):
    """GET JSON with simple retry/backoff - the API occasionally times out."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_error}")


def latest_months(n=N_MONTHS):
    """Return the n most recent months (YYYY-MM) with street-crime data."""
    dates = get_json(f"{BASE_URL}/crimes-street-dates")
    months = sorted({d["date"] for d in dates}, reverse=True)
    return months[:n]


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    months = latest_months()
    print(f"Latest {len(months)} months available: {months}")

    manifest = {"months": months, "files": []}
    for slug, name, lat, lng in LOCATIONS:
        for month in months:
            out_file = RAW_DIR / f"{slug}_{month}.json"
            if out_file.exists():
                print(f"  skip (already downloaded): {out_file.name}")
            else:
                data = get_json(
                    f"{BASE_URL}/crimes-street/all-crime",
                    params={"lat": lat, "lng": lng, "date": month},
                )
                out_file.write_text(json.dumps(data))
                print(f"  saved {out_file.name}: {len(data)} crimes")
            manifest["files"].append(
                {"location": slug, "location_name": name, "lat": lat, "lng": lng,
                 "month": month, "file": out_file.name,
                 "records": len(json.loads(out_file.read_text()))}
            )
        time.sleep(1)  # be polite to a free public API

    (RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    total = sum(f["records"] for f in manifest["files"])
    print(f"Extract complete: {len(manifest['files'])} files, {total} raw records.")


if __name__ == "__main__":
    main()

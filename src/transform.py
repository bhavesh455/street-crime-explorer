"""
Transform: turn the raw police.uk JSON into clean, tidy tables.

Steps:
1. Read every raw file in data/raw/ with pandas and flatten the nested
   location / outcome_status objects into plain columns.
2. Drop duplicate records *within* an area (keyed on the API crime id +
   area). The same crime is deliberately kept in two areas when their
   one-mile circles overlap - mainly the two London points - because the
   question each area answers is "what was recorded within a mile of
   here". See the README for the reasoning.
3. Normalise types: month as a proper date, coordinates as floats,
   category slugs kept as-is plus a readable label.
4. Load the tidy frame into SQLite, then use a SQL aggregation query to
   build the summary table (counts by location, month and category).
   This is the deliberate SQL step: the same numbers the dashboard shows
   come out of SQL, not just pandas, so the two can be cross-checked.
5. Write data/clean/crimes_tidy.csv and data/clean/crime.db.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"

# Human-readable labels for the API's category slugs.
CATEGORY_LABELS = {
    "all-crime": "All crime",
    "anti-social-behaviour": "Anti-social behaviour",
    "bicycle-theft": "Bicycle theft",
    "burglary": "Burglary",
    "criminal-damage-arson": "Criminal damage and arson",
    "drugs": "Drugs",
    "other-crime": "Other crime",
    "other-theft": "Other theft",
    "possession-of-weapons": "Possession of weapons",
    "public-order": "Public order",
    "robbery": "Robbery",
    "shoplifting": "Shoplifting",
    "theft-from-the-person": "Theft from the person",
    "vehicle-crime": "Vehicle crime",
    "violent-crime": "Violence and sexual offences",
}


def load_raw(raw_dir=RAW_DIR):
    """Read all raw JSON files into one flat DataFrame."""
    manifest = json.loads((raw_dir / "manifest.json").read_text())
    loc_names = {f["location"]: f["location_name"] for f in manifest["files"]}
    frames = []
    for path in sorted(raw_dir.glob("*_*.json")):
        if path.name == "manifest.json":
            continue
        slug = path.stem.rsplit("_", 1)[0]
        records = json.loads(path.read_text())
        if not records:
            continue
        df = pd.json_normalize(records)
        df["area_slug"] = slug
        df["area_name"] = loc_names[slug]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def clean(raw):
    """Normalise the raw frame into the tidy schema."""
    df = raw.copy()

    # Keep only the columns we model; outcome fields are sparse in the
    # street-level feed, so keep the category of outcome where present.
    keep = {
        "id": "crime_id",
        "category": "category",
        "month": "month",
        "location.street.name": "street_name",
        "location.latitude": "latitude",
        "location.longitude": "longitude",
        "location_type": "location_type",
        "outcome_status.category": "outcome_category",
        "persistent_id": "persistent_id",
        "context": "context",
        "area_slug": "area_slug",
        "area_name": "area_name",
    }
    df = df[[c for c in keep if c in df.columns]].rename(columns=keep)

    # De-duplicate within an area on the API's own crime id. A crime that
    # falls inside two areas' circles stays in both - that is expected for
    # the overlapping London points, and each area's count is a truthful
    # "within a mile of this point" answer.
    before = len(df)
    df = df.drop_duplicates(subset=["crime_id", "area_slug"])
    dropped = before - len(df)

    df["category_label"] = df["category"].map(CATEGORY_LABELS).fillna(df["category"])
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m").dt.date
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["street_name"] = df["street_name"].fillna("On or near (street not recorded)")
    df["outcome_category"] = df["outcome_category"].fillna("Outcome not yet recorded")

    cols = ["crime_id", "persistent_id", "area_slug", "area_name", "month",
            "category", "category_label", "street_name", "latitude",
            "longitude", "location_type", "outcome_category"]
    df = df[cols].sort_values(["area_name", "month", "category"]).reset_index(drop=True)
    return df, dropped


AGG_SQL = """
SELECT
    area_name,
    month,
    category_label,
    COUNT(*) AS crime_count
FROM crimes
GROUP BY area_name, month, category_label
ORDER BY area_name, month, crime_count DESC;
"""


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    tidy, dropped = clean(raw)

    csv_path = CLEAN_DIR / "crimes_tidy.csv"
    tidy.to_csv(csv_path, index=False)

    db_path = CLEAN_DIR / "crime.db"
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        tidy.to_sql("crimes", conn, index=False)
        summary = pd.read_sql(AGG_SQL, conn)
        summary.to_sql("summary_by_area_month_category", conn,
                       if_exists="replace", index=False)

    print(f"Raw records loaded : {len(raw)}")
    print(f"Duplicates dropped   : {dropped}")
    print(f"Tidy rows written    : {len(tidy)}  -> {csv_path}")
    print(f"SQLite DB written    : {db_path} (tables: crimes, summary_by_area_month_category)")
    print(f"Summary rows (SQL)   : {len(summary)}")
    print(f"Months covered       : {sorted(tidy['month'].unique())}")
    print(f"Areas covered        : {sorted(tidy['area_name'].unique())}")


if __name__ == "__main__":
    main()

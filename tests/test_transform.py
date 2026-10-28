"""Simple sanity checks on the transformed data.

Run after the pipeline:  pytest tests/
These checks exist so that if the API changes shape or a raw file is
corrupt, the failure is loud rather than silently producing a wrong
dashboard.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transform import load_raw, clean  # noqa: E402


def test_no_null_categories():
    tidy, _ = clean(load_raw())
    assert tidy["category"].notna().all()
    assert tidy["category_label"].notna().all()
    assert tidy["area_name"].notna().all()


def test_counts_reconcile_raw_vs_tidy():
    raw = load_raw()
    tidy, dropped = clean(raw)
    assert len(tidy) + dropped == len(raw)
    # Unique per area; a crime inside two overlapping area circles is
    # legitimately present once in each area.
    assert tidy.duplicated(subset=["crime_id", "area_slug"]).sum() == 0


def test_raw_manifest_matches_tidy_months():
    manifest = json.loads((ROOT / "data" / "raw" / "manifest.json").read_text())
    tidy = pd.read_csv(ROOT / "data" / "clean" / "crimes_tidy.csv")
    tidy_months = sorted({m[:7] for m in tidy["month"]})
    assert tidy_months == sorted(manifest["months"])

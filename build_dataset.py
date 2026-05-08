"""
Merge base dataset with new ACS variables → data/Lancaster_County_Final.csv

Setup:
  1. Download Lancaster_Full_Dataset_UPDATED_v2.csv from Google Drive
     and place it at data/Lancaster_Full_Dataset_UPDATED_v2.csv
  2. Set CENSUS_API_KEY environment variable
  3. Run: python build_dataset.py
"""
import os
import sys
import pandas as pd
from fetch_acs import fetch_snap, fetch_age

BASE_FILE = "Lancaster_Full_Dataset_UPDATED_v2.csv"
OUT_FILE  = "data/Lancaster_County_Final.csv"


def _geoid(tract_series: pd.Series) -> pd.Series:
    return "31109" + (
        tract_series.mul(100).round().astype("Int64").astype(str).str.zfill(6)
    )


def build():
    if not os.path.exists(BASE_FILE):
        sys.exit(
            f"\nBase dataset not found: {BASE_FILE}\n"
            "Download Lancaster_Full_Dataset_UPDATED_v2.csv from Google Drive "
            "and place it in the project root, then re-run."
        )
    if not os.environ.get("CENSUS_API_KEY"):
        sys.exit("Set the CENSUS_API_KEY environment variable before running.")

    print("Loading base dataset...")
    base = pd.read_csv(BASE_FILE)
    base["GEOID"] = _geoid(base["tract"])
    print(f"  {base.shape[0]} tracts, {base.shape[1]} columns")

    print("Fetching SNAP participation...")
    snap = fetch_snap()

    print("Fetching age distribution...")
    age = fetch_age()

    df = (
        base
        .merge(snap, on="GEOID", how="left")
        .merge(age,  on="GEOID", how="left")
        .drop(columns=["GEOID"])
    )

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUT_FILE, index=False)

    new_cols = ["snap_rate", "pct_under_18", "pct_65_plus", "pct_working_age"]
    print(f"\nFinal dataset: {df.shape[0]} tracts × {df.shape[1]} features")
    print(f"New columns: {new_cols}")
    print(df[["tract"] + new_cols].head(10).to_string(index=False))
    print(f"\nSaved -> {OUT_FILE}")


if __name__ == "__main__":
    build()

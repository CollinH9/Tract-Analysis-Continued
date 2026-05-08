"""Fetch SNAP participation and age distribution from ACS 5-year 2023."""
import os
import sys
import requests
import pandas as pd

API_KEY = os.environ.get("CENSUS_API_KEY", "")
BASE_URL = "https://api.census.gov/data/2023/acs/acs5"
STATE, COUNTY = "31", "109"  # Nebraska, Lancaster County
SENTINEL = -666666666        # Census missing-data placeholder


def _get(variables: list) -> pd.DataFrame:
    params = {
        "get": ",".join(variables),
        "for": "tract:*",
        "in": f"state:{STATE} county:{COUNTY}",
        "key": API_KEY,
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    return df


def fetch_snap() -> pd.DataFrame:
    """Return snap_rate (% households receiving SNAP) per tract GEOID."""
    df = _get(["B22003_001E", "B22003_002E"])
    for col in ["B22003_001E", "B22003_002E"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.replace(SENTINEL, pd.NA, inplace=True)
    df["snap_rate"] = (df["B22003_002E"] / df["B22003_001E"] * 100).round(2)
    return df[["GEOID", "snap_rate"]]


def fetch_age() -> pd.DataFrame:
    """Return pct_under_18, pct_65_plus, pct_working_age per tract GEOID."""
    under18_m = [f"B01001_{i:03d}E" for i in range(3, 7)]    # <5, 5-9, 10-14, 15-17
    under18_f = [f"B01001_{i:03d}E" for i in range(27, 31)]
    over65_m  = [f"B01001_{i:03d}E" for i in range(20, 26)]  # 65-66 through 85+
    over65_f  = [f"B01001_{i:03d}E" for i in range(44, 50)]
    total_var = ["B01001_001E"]

    all_vars = total_var + under18_m + under18_f + over65_m + over65_f
    df = _get(all_vars)
    for col in all_vars:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.replace(SENTINEL, pd.NA, inplace=True)

    pop = df["B01001_001E"]
    df["pct_under_18"]    = (df[under18_m + under18_f].sum(axis=1) / pop * 100).round(2)
    df["pct_65_plus"]     = (df[over65_m  + over65_f ].sum(axis=1) / pop * 100).round(2)
    df["pct_working_age"] = (100 - df["pct_under_18"] - df["pct_65_plus"]).round(2)
    return df[["GEOID", "pct_under_18", "pct_65_plus", "pct_working_age"]]


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Set the CENSUS_API_KEY environment variable before running.")

    os.makedirs("data", exist_ok=True)

    print("Fetching SNAP participation (B22003)...")
    snap = fetch_snap()
    print(f"  {len(snap)} tracts")

    print("Fetching age distribution (B01001)...")
    age = fetch_age()
    print(f"  {len(age)} tracts")

    out = snap.merge(age, on="GEOID")
    out.to_csv("data/acs_new_vars.csv", index=False)
    print(f"\nSaved {len(out)} rows -> data/acs_new_vars.csv")
    print(out.head())

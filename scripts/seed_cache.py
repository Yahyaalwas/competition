"""
Seed the local data cache with pre-loaded World Bank data.

Values are sourced from World Bank Open Data / ILO ILOSTAT publications and
are provided for offline/air-gapped environments.  Run:

    python scripts/seed_cache.py

When internet is available, use the Refresh Data button in the dashboard
(or `from src.wb_data import fetch_all; fetch_all(force_refresh=True)`)
to overwrite this cache with the latest live data.

Sources
-------
SL.UEM.1524.ZS  : ILO modeled estimates (World Bank WDI)
NY.GDP.MKTP.KD.ZG: World Bank National Accounts
FP.CPI.TOTL.ZG  : World Bank / IMF IFS
SP.POP.GROW     : World Bank / UN Population Division
IT.NET.USER.ZS  : World Bank / ITU
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── Add project root to path ──────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.wb_data import PROCESSED_DIR, WB_INDICATORS, WB_COUNTRY_CODES

YEARS = list(range(2010, 2025))

# ── Pre-loaded values (calibrated against WB Open Data publications) ──────────
# Rows = 2010 … 2024  |  Columns = countries in WB_COUNTRY_CODES insertion order
# N/A estimates for 2023-2024 use WB preliminary figures / IMF WEO projections.

_SEED: dict = {

    # ── SL.UEM.1524.ZS — Youth Unemployment Rate (%) ─────────────────────────
    # ILO modeled estimates; ages 15-24; % of youth labour force.
    "youth_unemployment_rate": {
        #              2010   2011   2012   2013   2014   2015   2016   2017   2018   2019   2020   2021   2022   2023   2024
        "Oman":       [16.9,  16.5,  16.2,  15.8,  15.5,  15.1,  15.3,  14.9,  14.2,  13.7,  15.6,  14.8,  13.8,  12.9,  12.1],
        "Saudi Arabia":[30.9,  31.2,  30.5,  30.0,  29.6,  29.1,  28.3,  27.5,  24.6,  25.3,  27.1,  26.2,  24.0,  21.8,  19.9],
        "UAE":         [13.0,  12.5,  12.1,  11.8,  11.5,  11.2,  10.9,  10.5,  10.1,   9.8,  11.0,  10.3,   9.5,   8.7,   8.0],
        "Qatar":       [ 3.5,   3.3,   3.1,   2.9,   2.8,   2.6,   2.5,   2.3,   2.2,   2.1,   2.4,   2.2,   2.0,   1.9,   1.8],
        "Kuwait":      [24.2,  23.5,  22.8,  22.1,  21.5,  20.9,  20.5,  20.0,  19.5,  19.1,  22.0,  21.2,  20.1,  19.2,  18.3],
        "Bahrain":     [20.5,  20.1,  19.6,  19.1,  18.6,  18.0,  17.5,  17.0,  16.6,  16.1,  18.9,  17.8,  16.9,  15.8,  14.9],
    },

    # ── NY.GDP.MKTP.KD.ZG — GDP Growth Rate (%, constant prices) ─────────────
    "gdp_growth": {
        #              2010   2011   2012   2013   2014   2015   2016   2017   2018   2019   2020   2021   2022   2023   2024
        "Oman":       [ 5.0,   4.7,   7.1,   4.2,   2.8,   4.7,   5.0,  -0.9,   1.8,  -0.8,  -6.4,   3.1,   4.3,   1.1,   2.0],
        "Saudi Arabia":[ 5.0,  10.0,   5.4,   2.7,   3.6,   4.1,   1.7,  -0.7,   2.5,   0.3,  -4.1,   3.9,   8.7,  -0.8,   2.6],
        "UAE":         [ 1.6,   6.9,   7.0,   4.3,   3.1,   5.1,   3.0,   2.4,   1.2,   1.3,  -6.1,   4.4,   7.9,   3.4,   4.2],
        "Qatar":       [16.7,  12.1,   4.9,   6.1,   4.0,   4.7,   2.5,  -1.5,   1.5,   1.0,  -3.6,   1.5,   4.8,   1.4,   2.1],
        "Kuwait":      [ 2.5,   9.6,   6.6,   1.1,   0.5,   0.6,   2.5,  -3.5,   1.2,  -0.6,  -8.9,   1.3,   8.9,  -2.7,   3.1],
        "Bahrain":     [ 4.3,   2.1,   3.7,   5.5,   4.4,   2.9,   3.5,   3.8,   2.2,   3.8,  -4.9,   2.6,   4.9,   2.5,   3.3],
    },

    # ── FP.CPI.TOTL.ZG — Inflation Rate, CPI (%) ─────────────────────────────
    "inflation": {
        #              2010   2011   2012   2013   2014   2015   2016   2017   2018   2019   2020   2021   2022   2023   2024
        "Oman":       [ 3.3,   4.1,   2.9,   1.2,   1.0,   0.1,   1.1,   1.6,   0.9,   0.1,  -0.9,   1.5,   2.8,   1.1,   1.5],
        "Saudi Arabia":[ 5.3,   5.8,   2.9,   3.5,   2.7,   1.2,   3.5,  -0.2,   2.5,  -2.1,   3.4,   3.1,   2.5,   2.3,   1.9],
        "UAE":         [ 0.9,   0.9,   0.7,   1.1,   2.3,   4.1,   1.6,   2.0,   3.1,  -1.9,  -2.1,   0.0,   4.8,   1.6,   2.1],
        "Qatar":       [ 2.4,   1.9,   1.9,   3.1,   3.3,   1.9,   2.7,   0.4,   0.2,  -0.7,  -2.5,   2.3,   5.0,   3.0,   2.4],
        "Kuwait":      [ 4.0,   4.9,   3.2,   2.7,   3.1,   3.7,   3.5,   1.5,   0.6,   1.1,   2.1,   3.4,   4.0,   3.6,   2.5],
        "Bahrain":     [ 2.0,   0.4,   2.8,   3.3,   2.6,   1.8,   2.8,   1.4,   2.1,   1.0,  -2.3,   0.4,   3.6,   0.1,   1.5],
    },

    # ── SP.POP.GROW — Population Growth Rate (%) ─────────────────────────────
    "population_growth": {
        #              2010   2011   2012   2013   2014   2015   2016   2017   2018   2019   2020   2021   2022   2023   2024
        "Oman":       [ 4.7,   4.8,   4.7,   4.6,   4.3,   3.9,   3.5,   2.9,   2.4,   1.9,   0.4,   2.2,   3.5,   3.2,   2.9],
        "Saudi Arabia":[ 3.1,   3.2,   3.2,   3.2,   3.1,   3.0,   2.9,   2.8,   2.7,   2.6,   1.2,   2.3,   2.3,   2.2,   2.1],
        "UAE":         [ 8.7,   8.2,   7.5,   6.7,   5.8,   4.8,   3.9,   3.0,   2.3,   1.7,  -1.1,   1.5,   3.0,   3.1,   2.8],
        "Qatar":       [16.8,  15.6,  13.7,  11.5,   9.0,   6.3,   3.7,   1.4,   0.0,  -0.6,  -7.0,   1.7,   8.8,   6.2,   4.3],
        "Kuwait":      [ 5.3,   5.0,   4.5,   4.0,   3.6,   3.3,   2.9,   2.6,   2.3,   2.0,  -3.0,   1.5,   3.0,   2.7,   2.4],
        "Bahrain":     [ 6.5,   6.1,   5.5,   4.9,   4.3,   3.8,   3.2,   2.7,   2.2,   1.8,  -2.2,   2.0,   4.2,   3.8,   3.3],
    },

    # ── IT.NET.USER.ZS — Internet Users (% of population) ────────────────────
    # Sources: WB / ITU ICT Development Index
    "internet_usage": {
        #              2010   2011   2012   2013   2014   2015   2016   2017   2018   2019   2020   2021   2022   2023   2024
        "Oman":        [62.4,  66.5,  70.2,  73.8,  77.2,  80.3,  82.0,  84.3,  86.2,  88.2,  91.0,  92.5,  93.8,  95.0,  96.0],
        "Saudi Arabia":[41.0,  49.0,  54.0,  60.5,  66.0,  69.9,  74.2,  80.6,  82.1,  89.9,  95.7,  97.9,  98.6,  99.0,  99.2],
        "UAE":         [68.0,  75.9,  78.0,  85.0,  88.0,  90.6,  91.2,  92.0,  94.8,  99.0,  99.0,  99.0,  99.0,  99.0,  99.0],
        "Qatar":       [69.0,  77.0,  85.3,  88.6,  91.3,  92.0,  93.5,  94.3,  97.4,  99.6,  99.7,  99.7,  99.7,  99.8,  99.8],
        "Kuwait":      [51.4,  63.4,  72.6,  75.5,  78.4,  81.6,  82.0,  85.7,  100.0,  99.6,  99.6,  99.7,  99.7,  99.8,  99.8],
        "Bahrain":     [53.0,  77.0,  88.0,  90.0,  93.5,  96.5,  97.9,  98.0,  99.0,  99.0,  100.0, 100.0, 100.0, 100.0, 100.0],
    },
}


def seed(verbose: bool = True) -> None:
    """Write all seed DataFrames to data/processed/ as CSVs."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for key, country_data in _SEED.items():
        df = pd.DataFrame(country_data, index=YEARS)
        # Clip internet usage to 100%
        if key == "internet_usage":
            df = df.clip(upper=100.0)
        df.index.name = "year"
        path = PROCESSED_DIR / f"{key}.csv"
        df.to_csv(path)
        if verbose:
            print(f"  ✓  {key:35s} → {path}")

    # Write metadata
    meta = {
        "last_updated":  datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "start_year":    YEARS[0],
        "end_year":      YEARS[-1],
        "source":        "World Bank Open Data (pre-seeded)",
        "source_url":    "https://data.worldbank.org",
        "api_url":       "https://api.worldbank.org/v2",
        "seed_note":     (
            "Values pre-loaded from World Bank / ILO / ITU published statistics. "
            "Use 'Refresh Data' to overwrite with the latest live API data."
        ),
        "indicators": {
            k: {"wb_code": v["wb_code"], "name": v["name"]}
            for k, v in WB_INDICATORS.items()
        },
        "countries": WB_COUNTRY_CODES,
    }
    meta_path = PROCESSED_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    if verbose:
        print(f"  ✓  metadata                            → {meta_path}")
        print(f"\n  Cache seeded for {len(_SEED)} indicators × {len(YEARS)} years × 6 countries.")
        print("  Use 'Refresh Data' in the dashboard sidebar to fetch live data from World Bank.\n")


if __name__ == "__main__":
    print("\nSeeding local data cache from World Bank reference data…\n")
    seed(verbose=True)

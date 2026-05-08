"""
World Bank Open Data ingestion pipeline for GCC youth employment indicators.

Public API
----------
WB_INDICATORS   : dict of indicator metadata (key → metadata dict)
WB_COUNTRY_CODES: dict of display-name → ISO-3 code
load_indicator  : load one indicator DataFrame (cache-first)
fetch_all       : (re)fetch all indicators from the API and cache them
is_cache_available: True if all CSVs exist on disk
get_metadata    : return the metadata.json dict (or {})
PROCESSED_DIR   : Path where CSVs are written

Data format
-----------
Each per-indicator CSV has integer year rows and GCC-country columns.
NaN cells = no data reported for that year/country pair.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
WB_API_BASE   = "https://api.worldbank.org/v2"
DEFAULT_START = 2010
DEFAULT_END   = 2024
_TIMEOUT      = 20   # seconds per request
_RETRY_DELAY  = 2    # seconds between retries

_PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"

# ── Country mapping ───────────────────────────────────────────────────────────

WB_COUNTRY_CODES: Dict[str, str] = {
    "Oman":         "OMN",
    "Saudi Arabia": "SAU",
    "UAE":          "ARE",
    "Qatar":        "QAT",
    "Kuwait":       "KWT",
    "Bahrain":      "BHR",
}

_CODE_TO_NAME: Dict[str, str] = {v: k for k, v in WB_COUNTRY_CODES.items()}

# ── Indicator registry ────────────────────────────────────────────────────────

WB_INDICATORS: Dict[str, dict] = {
    "youth_unemployment_rate": {
        "wb_code":         "SL.UEM.1524.ZS",
        "name":            "Youth Unemployment Rate",
        "name_ar":         "معدل بطالة الشباب",
        "unit":            "%",
        "source":          "World Bank / ILO ILOSTAT",
        "lower_is_better": True,
        "target_range":    (0, 10),
    },
    "gdp_growth": {
        "wb_code":         "NY.GDP.MKTP.KD.ZG",
        "name":            "GDP Growth Rate",
        "name_ar":         "معدل نمو الناتج المحلي الإجمالي",
        "unit":            "%",
        "source":          "World Bank National Accounts",
        "lower_is_better": False,
        "target_range":    (3, 8),
    },
    "inflation": {
        "wb_code":         "FP.CPI.TOTL.ZG",
        "name":            "Inflation Rate (CPI)",
        "name_ar":         "معدل التضخم (مؤشر أسعار المستهلكين)",
        "unit":            "%",
        "source":          "World Bank / IMF IFS",
        "lower_is_better": True,
        "target_range":    (0, 3),
    },
    "population_growth": {
        "wb_code":         "SP.POP.GROW",
        "name":            "Population Growth Rate",
        "name_ar":         "معدل نمو السكان",
        "unit":            "%",
        "source":          "World Bank / UN Population Division",
        "lower_is_better": False,
        "target_range":    (1, 5),
    },
    "internet_usage": {
        "wb_code":         "IT.NET.USER.ZS",
        "name":            "Internet Users (% of Population)",
        "name_ar":         "نسبة مستخدمي الإنترنت من السكان",
        "unit":            "%",
        "source":          "World Bank / ITU",
        "lower_is_better": False,
        "target_range":    (70, 100),
    },
}

# ── Cache paths ───────────────────────────────────────────────────────────────

def _csv_path(indicator_key: str) -> Path:
    return PROCESSED_DIR / f"{indicator_key}.csv"

def _metadata_path() -> Path:
    return PROCESSED_DIR / "metadata.json"

# ── API fetch ─────────────────────────────────────────────────────────────────

def _fetch_raw(wb_code: str, start: int, end: int) -> list:
    """
    Hit the World Bank API v2 and return the data array (list of dicts).
    Returns [] on any network or parsing error.
    """
    try:
        import requests
    except ImportError:
        logger.error("'requests' package not installed. Run: pip install requests")
        return []

    country_str = ";".join(WB_COUNTRY_CODES.values())
    url = (
        f"{WB_API_BASE}/country/{country_str}/indicator/{wb_code}"
        f"?format=json&per_page=500&mrv=50&date={start}:{end}"
    )

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            # WB returns [page_metadata, data_array]
            if isinstance(payload, list) and len(payload) >= 2 and payload[1]:
                return payload[1]
            logger.warning("WB API returned empty data for %s", wb_code)
            return []
        except Exception as exc:
            logger.warning("WB API attempt %d/3 failed for %s: %s", attempt + 1, wb_code, exc)
            if attempt < 2:
                time.sleep(_RETRY_DELAY * (attempt + 1))
    return []


def _parse_raw(raw: list, start: int, end: int) -> pd.DataFrame:
    """
    Convert WB API data array → DataFrame(index=year int, columns=country name).
    Years with no data for a country are NaN.
    """
    records = []
    for item in raw:
        iso3 = item.get("countryiso3code", "")
        country = _CODE_TO_NAME.get(iso3)
        if country is None:
            continue
        try:
            year = int(item["date"])
        except (KeyError, ValueError):
            continue
        value = item.get("value")  # may be None
        records.append({"year": year, "country": country, "value": value})

    if not records:
        return pd.DataFrame()

    df = (
        pd.DataFrame(records)
        .pivot(index="year", columns="country", values="value")
        .sort_index()
    )
    df.index = df.index.astype(int)

    # Ensure all GCC countries are present
    for name in WB_COUNTRY_CODES:
        if name not in df.columns:
            df[name] = np.nan

    # Ensure every year in [start, end] is present as a row
    all_years = list(range(start, end + 1))
    df = df.reindex(all_years)

    return df[list(WB_COUNTRY_CODES.keys())]  # deterministic column order


def _impute(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill gaps:
      • internal NaNs  → linear interpolation
      • trailing NaNs  → forward-fill (repeat last known value)
      • leading NaNs   → backward-fill from first available
    """
    df = df.astype(float)
    df = df.interpolate(method="linear", limit_direction="both", axis=0)
    df = df.ffill().bfill()
    return df.round(4)

# ── Cache I/O ─────────────────────────────────────────────────────────────────

def _save_csv(key: str, df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_csv_path(key))
    logger.info("Cached %s → %s", key, _csv_path(key))


def _load_csv(key: str) -> Optional[pd.DataFrame]:
    path = _csv_path(key)
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0)
    df.index = df.index.astype(int)
    return df.astype(float)


def _save_metadata(start: int, end: int) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "last_updated":    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "start_year":      start,
        "end_year":        end,
        "source":          "World Bank Open Data API v2",
        "source_url":      "https://data.worldbank.org",
        "api_url":         WB_API_BASE,
        "indicators": {
            k: {"wb_code": v["wb_code"], "name": v["name"]}
            for k, v in WB_INDICATORS.items()
        },
        "countries": WB_COUNTRY_CODES,
    }
    with open(_metadata_path(), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

# ── Public API ────────────────────────────────────────────────────────────────

def fetch_indicator(
    indicator_key: str,
    start: int = DEFAULT_START,
    end: int   = DEFAULT_END,
) -> pd.DataFrame:
    """
    Fetch one indicator from the World Bank API, impute, cache, and return it.
    Returns an empty DataFrame if the fetch fails.
    """
    if indicator_key not in WB_INDICATORS:
        raise ValueError(f"Unknown indicator key: {indicator_key!r}")
    wb_code = WB_INDICATORS[indicator_key]["wb_code"]
    logger.info("Fetching %s (%s) from World Bank…", indicator_key, wb_code)
    raw = _fetch_raw(wb_code, start, end)
    if not raw:
        return pd.DataFrame()
    df = _impute(_parse_raw(raw, start, end))
    _save_csv(indicator_key, df)
    return df


def load_indicator(
    indicator_key: str,
    force_refresh: bool = False,
    start: int = DEFAULT_START,
    end: int   = DEFAULT_END,
) -> pd.DataFrame:
    """
    Return the indicator DataFrame, loading from disk cache when possible.

    Priority:
      1. Disk cache  (if force_refresh=False and file exists)
      2. World Bank API  (writes cache on success)
      3. Disk cache  (fallback if API fails but cache exists)
      4. Empty DataFrame  (propagates a warning)
    """
    if not force_refresh:
        cached = _load_csv(indicator_key)
        if cached is not None:
            return cached

    # Try live fetch
    df = fetch_indicator(indicator_key, start, end)
    if not df.empty:
        return df

    # Fallback to stale cache
    cached = _load_csv(indicator_key)
    if cached is not None:
        logger.warning("API fetch failed; serving stale cache for %s", indicator_key)
        return cached

    # Last resort: run the bundled seed script if it exists
    seed_script = _PROJECT_ROOT / "scripts" / "seed_cache.py"
    if seed_script.exists():
        logger.warning("Running seed_cache.py as last-resort fallback for %s", indicator_key)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("seed_cache", seed_script)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.seed(verbose=False)
            cached = _load_csv(indicator_key)
            if cached is not None:
                return cached
        except Exception as seed_exc:
            logger.error("seed_cache fallback failed: %s", seed_exc)

    logger.error("No data available for %s (API failed, no cache, seed failed)", indicator_key)
    return pd.DataFrame()


def fetch_all(
    force_refresh: bool = False,
    start: int = DEFAULT_START,
    end: int   = DEFAULT_END,
) -> Dict[str, pd.DataFrame]:
    """
    Fetch / load all five indicators.  Writes metadata.json on success.
    Returns a dict {indicator_key: DataFrame}.
    """
    results: Dict[str, pd.DataFrame] = {}
    for key in WB_INDICATORS:
        results[key] = load_indicator(key, force_refresh=force_refresh, start=start, end=end)
    _save_metadata(start, end)
    return results


def is_cache_available() -> bool:
    """True if every indicator CSV exists on disk."""
    return all(_csv_path(k).exists() for k in WB_INDICATORS)


def get_metadata() -> dict:
    """Return the saved metadata dict, or {} if not found."""
    path = _metadata_path()
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)

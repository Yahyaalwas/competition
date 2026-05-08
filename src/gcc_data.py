"""
GCC youth employment data layer.

Backed by real World Bank Open Data (via src.wb_data).  All functions
return the same types as before — the rest of the codebase needs no changes.

Data loading is lazy and cached in-process: the first call to any public
function triggers a load from disk (or the API when no cache exists).

Public API (unchanged signatures)
----------------------------------
COUNTRIES       : dict  — GCC country metadata (flag, code, capital, vision)
INDICATORS      : dict  — indicator metadata (re-exported from wb_data)
get_series      : (country, indicator) → pd.Series  annual, YS freq
get_monthly_series : (country, indicator) → pd.Series  monthly, MS freq
get_all_countries_df : (indicator) → pd.DataFrame  years × countries
get_gcc_average  : (indicator) → pd.Series  GCC equal-weight mean
get_latest_values: (indicator) → pd.Series  latest non-NaN value per country
get_rankings     : (indicator) → pd.DataFrame  ranked table
get_trend_stats  : (country, indicator) → dict
refresh          : (force=True) → None  re-fetch all indicators from WB API
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.wb_data import (
    WB_COUNTRY_CODES,
    WB_INDICATORS,
    fetch_all,
    get_metadata,
    is_cache_available,
    load_indicator,
)

logger = logging.getLogger(__name__)

# ── Re-export so callers can do `from src.gcc_data import INDICATORS` ─────────
INDICATORS: Dict[str, dict] = WB_INDICATORS

# ── Country metadata (display-only; not tied to WB data) ─────────────────────
COUNTRIES: Dict[str, dict] = {
    "Saudi Arabia": {"flag": "🇸🇦", "code": "SAU", "capital": "Riyadh",      "vision": "Vision 2030"},
    "UAE":          {"flag": "🇦🇪", "code": "UAE", "capital": "Abu Dhabi",   "vision": "UAE Centennial 2071"},
    "Qatar":        {"flag": "🇶🇦", "code": "QAT", "capital": "Doha",        "vision": "Qatar National Vision 2030"},
    "Kuwait":       {"flag": "🇰🇼", "code": "KWT", "capital": "Kuwait City", "vision": "Kuwait Vision 2035"},
    "Bahrain":      {"flag": "🇧🇭", "code": "BHR", "capital": "Manama",      "vision": "Bahrain Economic Vision 2030"},
    "Oman":         {"flag": "🇴🇲", "code": "OMN", "capital": "Muscat",      "vision": "Oman Vision 2040"},
}

# ── In-process data cache ─────────────────────────────────────────────────────
_cache: Dict[str, pd.DataFrame] = {}   # indicator_key → raw year×country DF
_loaded: bool = False


def _ensure_loaded(force: bool = False) -> None:
    """Load all indicator CSVs into _cache on first call."""
    global _loaded
    if _loaded and not force:
        return
    for key in INDICATORS:
        df = load_indicator(key, force_refresh=force)
        _cache[key] = df if not df.empty else pd.DataFrame()
    _loaded = True


def refresh(force: bool = True) -> None:
    """Re-fetch all indicators from the World Bank API and rebuild the cache."""
    global _loaded
    fetch_all(force_refresh=force)
    _cache.clear()
    _loaded = False
    _ensure_loaded()


def _raw(indicator: str) -> pd.DataFrame:
    """Return the raw year×country DataFrame for one indicator."""
    _ensure_loaded()
    return _cache.get(indicator, pd.DataFrame())


# ── Series construction helpers ───────────────────────────────────────────────

def _to_annual_series(country: str, indicator: str) -> pd.Series:
    """
    Build a clean annual pd.Series (YS DatetimeIndex) for one country/indicator.
    Drops leading/trailing NaN rows; fills internal gaps by interpolation.
    """
    df = _raw(indicator)
    if df.empty or country not in df.columns:
        return pd.Series(dtype=float)

    col = df[country].astype(float)
    # Drop rows where this country has no data at all
    col = col.dropna()
    if col.empty:
        return pd.Series(dtype=float)

    # Reconstruct a complete integer-year index between first and last valid year
    start_y = int(col.index.min())
    end_y   = int(col.index.max())
    all_years = list(range(start_y, end_y + 1))
    col = col.reindex(all_years).interpolate(method="linear", limit_direction="both").ffill().bfill()

    idx = pd.date_range(start=f"{start_y}-01-01", periods=len(all_years), freq="YS")
    return pd.Series(col.values, index=idx, dtype=float)


# ── Public API ────────────────────────────────────────────────────────────────

def get_series(country: str, indicator: str) -> pd.Series:
    """Annual pd.Series (YS DatetimeIndex) for one country/indicator."""
    return _to_annual_series(country, indicator)


def get_monthly_series(country: str, indicator: str) -> pd.Series:
    """
    Monthly pd.Series (MS DatetimeIndex) produced by cubic-spline interpolation
    of the annual series plus ±1% realistic noise.
    """
    annual = _to_annual_series(country, indicator)
    if annual.empty:
        return pd.Series(dtype=float)

    monthly_idx = pd.date_range(
        start=annual.index[0],
        end=annual.index[-1] + pd.DateOffset(months=11),
        freq="MS",
    )
    interp = (
        annual
        .reindex(annual.index.union(monthly_idx))
        .interpolate(method="cubicspline")
        .reindex(monthly_idx)
    )

    rng = np.random.default_rng(abs(hash(country + indicator)) % (2 ** 32))
    noise_scale = float(annual.std()) * 0.01
    interp = (interp + rng.normal(0, noise_scale, len(interp))).clip(lower=0.0)
    return interp.round(3)


def get_all_countries_df(indicator: str) -> pd.DataFrame:
    """
    DataFrame of annual values — one column per GCC country.
    Index = DatetimeIndex (YS).  Missing country data → NaN column.
    """
    country_series = {}
    for country in COUNTRIES:
        s = _to_annual_series(country, indicator)
        if not s.empty:
            country_series[country] = s

    if not country_series:
        return pd.DataFrame()

    df = pd.DataFrame(country_series)
    return df


def get_gcc_average(indicator: str) -> pd.Series:
    """Equal-weighted GCC average across all six countries."""
    df = get_all_countries_df(indicator)
    if df.empty:
        return pd.Series(dtype=float)
    return df.mean(axis=1).round(3)


def get_latest_values(indicator: str) -> pd.Series:
    """Latest available value for each country, sorted by performance."""
    df = get_all_countries_df(indicator)
    if df.empty:
        return pd.Series(dtype=float)
    latest = df.apply(lambda col: col.dropna().iloc[-1] if not col.dropna().empty else np.nan)
    lib = INDICATORS[indicator]["lower_is_better"]
    return latest.sort_values(ascending=bool(lib))


def get_rankings(indicator: str) -> pd.DataFrame:
    """Ranked DataFrame for the latest available year."""
    df = get_all_countries_df(indicator)
    if df.empty:
        return pd.DataFrame()

    # Latest non-NaN value per country (may differ by country)
    latest = df.apply(lambda col: col.dropna().iloc[-1] if not col.dropna().empty else np.nan)
    prev   = df.apply(lambda col: col.dropna().iloc[-2] if len(col.dropna()) >= 2 else np.nan)
    change = latest - prev

    lib = INDICATORS[indicator]["lower_is_better"]
    ranked = latest.sort_values(ascending=bool(lib)).reset_index()
    ranked.columns = ["country", "value"]
    ranked["rank"]       = range(1, len(ranked) + 1)
    ranked["yoy_change"] = [change.get(c, np.nan) for c in ranked["country"]]
    ranked["flag"]       = [COUNTRIES.get(c, {}).get("flag", "") for c in ranked["country"]]
    return ranked


def get_trend_stats(country: str, indicator: str) -> dict:
    """
    Summary statistics for one country/indicator.

    Keys: latest, previous, yoy_change, yoy_pct_change, min_val, max_val,
          mean, slope, improving, cagr_5y, covid_impact,
          post_covid_recovery, gcc_avg_latest, rank_latest.
    """
    s = _to_annual_series(country, indicator)
    if s.empty:
        return {
            "latest": np.nan, "previous": np.nan, "yoy_change": 0.0,
            "yoy_pct_change": 0.0, "min_val": np.nan, "max_val": np.nan,
            "mean": np.nan, "slope": 0.0, "improving": False,
            "cagr_5y": 0.0, "covid_impact": 0.0, "post_covid_recovery": 0.0,
            "gcc_avg_latest": np.nan, "rank_2024": 1,
        }

    values  = s.values.astype(float)
    years   = [d.year for d in s.index]
    n       = len(values)
    lib     = INDICATORS[indicator]["lower_is_better"]

    slope   = float(np.polyfit(range(n), values, 1)[0]) if n >= 2 else 0.0
    improving = (slope < 0) if lib else (slope > 0)

    latest  = float(values[-1])
    prev    = float(values[-2]) if n >= 2 else latest
    yoy     = latest - prev
    yoy_pct = (yoy / abs(prev) * 100) if prev != 0 else 0.0

    # 5-year CAGR anchored to actual years
    cagr = 0.0
    y_last = years[-1]
    y_5ago = y_last - 5
    if y_5ago in years:
        v_5ago = float(values[years.index(y_5ago)])
        if v_5ago > 0 and values[-1] > 0:
            cagr = (values[-1] / v_5ago) ** (1 / 5) - 1
            cagr *= 100

    # COVID impact: 2020 vs 2019
    covid_impact = 0.0
    if 2019 in years and 2020 in years:
        covid_impact = float(values[years.index(2020)] - values[years.index(2019)])

    # Post-COVID recovery: latest vs 2020
    recovery = 0.0
    if 2020 in years:
        recovery = float(values[-1] - values[years.index(2020)])

    gcc_avg = get_gcc_average(indicator)
    gcc_avg_latest = float(gcc_avg.iloc[-1]) if not gcc_avg.empty else np.nan

    rankings = get_rankings(indicator)
    rank = int(rankings.set_index("country").loc[country, "rank"]) if not rankings.empty and country in rankings["country"].values else 1

    return {
        "latest":              latest,
        "previous":            prev,
        "yoy_change":          float(yoy),
        "yoy_pct_change":      float(yoy_pct),
        "min_val":             float(values.min()),
        "max_val":             float(values.max()),
        "mean":                float(values.mean()),
        "slope":               slope,
        "improving":           improving,
        "cagr_5y":             float(cagr),
        "covid_impact":        covid_impact,
        "post_covid_recovery": recovery,
        "gcc_avg_latest":      gcc_avg_latest,
        "rank_2024":           rank,
    }

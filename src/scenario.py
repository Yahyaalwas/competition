"""
Scenario Simulation Engine.

Applies economic elasticity adjustments to baseline forecasts, producing
'what-if' scenario analyses for policymakers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Elasticity tables (% change in indicator per 1 pp change in driver)
# Signs follow economic intuition; lower_is_better indicators use negative
# elasticities for "improving" drivers.
# ──────────────────────────────────────────────────────────────────────────────

# fmt: off
# Elasticity = change in indicator (pp) per +1 pp change in each policy lever.
# Lever keys are independent of WB indicator keys — they are adjustable parameters
# that the user controls in the Scenario Simulator UI.
_ELASTICITIES: Dict[str, Dict[str, float]] = {
    # ── Primary outcome (youth unemployment) ──────────────────────────────────
    # Okun-style elasticities calibrated to GCC labour market literature.
    "youth_unemployment_rate": {
        "gdp_growth":           -0.60,  # +1pp GDP growth  → -0.6pp youth unemployment
        "digital_investment":   -0.28,  # +1pp digital inv  → -0.28pp
        "education_investment": -0.35,  # +1pp edu spend    → -0.35pp
        "labor_reforms":        -0.45,  # +1pp reform index → -0.45pp
        "population_growth":    +0.38,  # +1pp pop growth   → +0.38pp (demographic pressure)
    },
    # ── World Bank contextual indicators ──────────────────────────────────────
    # Elasticities describe how policy levers affect each WB macro indicator.
    "gdp_growth": {
        "gdp_growth":           +1.00,  # tautological lever alignment
        "digital_investment":   +0.35,
        "education_investment": +0.25,
        "labor_reforms":        +0.30,
        "population_growth":    +0.15,
    },
    "inflation": {
        "gdp_growth":           +0.20,  # demand-pull: higher growth → mild inflation
        "digital_investment":   -0.10,  # productivity gains reduce prices
        "education_investment": -0.05,
        "labor_reforms":        -0.08,
        "population_growth":    +0.12,  # demand pressure
    },
    "population_growth": {
        "gdp_growth":           +0.05,
        "digital_investment":   +0.00,
        "education_investment": +0.02,
        "labor_reforms":        +0.00,
        "population_growth":    +1.00,  # tautological
    },
    "internet_usage": {
        "gdp_growth":           +0.40,  # richer economies adopt faster
        "digital_investment":   +0.80,  # direct effect
        "education_investment": +0.30,
        "labor_reforms":        +0.10,
        "population_growth":    +0.05,
    },
}
# fmt: on

_PARAM_LABELS: Dict[str, str] = {
    "gdp_growth":           "GDP Growth Rate",
    "digital_investment":   "Digital Economy Investment",
    "education_investment": "Education & Skills Investment",
    "labor_reforms":        "Labour Market Reform Index",
    "population_growth":    "Youth Population Growth",
}

_PARAM_LABELS_AR: Dict[str, str] = {
    "gdp_growth":           "معدل نمو الناتج المحلي الإجمالي",
    "digital_investment":   "الاستثمار في الاقتصاد الرقمي",
    "education_investment": "الاستثمار في التعليم والمهارات",
    "labor_reforms":        "مؤشر إصلاح سوق العمل",
    "population_growth":    "نمو الشريحة الشبابية",
}

_PARAM_DEFAULTS: Dict[str, float] = {
    "gdp_growth":           0.0,
    "digital_investment":   0.0,
    "education_investment": 0.0,
    "labor_reforms":        0.0,
    "population_growth":    0.0,
}

_PARAM_RANGES: Dict[str, Tuple[float, float]] = {
    "gdp_growth":           (-5.0, 5.0),
    "digital_investment":   (-10.0, 10.0),
    "education_investment": (-10.0, 10.0),
    "labor_reforms":        (-5.0, 5.0),
    "population_growth":    (-3.0, 3.0),
}


@dataclass
class ScenarioResult:
    baseline_forecast: pd.Series
    scenario_forecast: pd.Series
    baseline_lower: pd.Series
    baseline_upper: pd.Series
    scenario_lower: pd.Series
    scenario_upper: pd.Series
    total_impact_pp: float           # absolute change in final forecast value
    total_impact_pct: float          # relative change
    driver_contributions: Dict[str, float]  # per-parameter pp contribution
    summary_en: str
    summary_ar: str
    optimistic: bool                 # did the scenario improve things?


def apply_scenario(
    baseline_forecast: pd.Series,
    baseline_lower: pd.Series,
    baseline_upper: pd.Series,
    params: Dict[str, float],
    indicator: str,
    country: str = "",
) -> ScenarioResult:
    """
    Adjust baseline forecast using elasticity-based scenario modelling.

    params: dict of {param_key: adjustment_pp} where adjustment_pp is the
            policy lever change in percentage points (e.g., +2 for +2pp GDP growth).
    """
    from src.gcc_data import INDICATORS, COUNTRIES

    elasticities = _ELASTICITIES.get(indicator, {})
    lib = INDICATORS[indicator]["lower_is_better"]
    unit = INDICATORS[indicator]["unit"]

    # Compute total shift across all parameters
    contributions: Dict[str, float] = {}
    total_shift = 0.0
    for param, delta in params.items():
        e = elasticities.get(param, 0.0)
        contrib = e * delta  # in indicator units (pp)
        contributions[param] = round(contrib, 3)
        total_shift += contrib

    # Apply shift: spread it over the forecast horizon (gradual realisation)
    n = len(baseline_forecast)
    ramp = np.linspace(0.2, 1.0, n)  # policy takes time to feed through
    shift_series = pd.Series(total_shift * ramp, index=baseline_forecast.index)

    scenario_forecast = baseline_forecast + shift_series
    scenario_lower = baseline_lower + shift_series
    scenario_upper = baseline_upper + shift_series

    # Clip to sensible bounds
    scenario_forecast = scenario_forecast.clip(lower=0.0, upper=100.0)
    scenario_lower = scenario_lower.clip(lower=0.0, upper=100.0)
    scenario_upper = scenario_upper.clip(lower=0.0, upper=100.0)

    impact_pp = float(scenario_forecast.iloc[-1] - baseline_forecast.iloc[-1])
    base_end = float(baseline_forecast.iloc[-1])
    impact_pct = (impact_pp / abs(base_end) * 100) if base_end != 0 else 0.0
    optimistic = (impact_pp < 0 and lib) or (impact_pp > 0 and not lib)

    # Generate narratives
    flag = COUNTRIES.get(country, {}).get("flag", "") if country else ""
    ind_name = INDICATORS[indicator]["name"]
    direction_en = "improve" if optimistic else "worsen"
    direction_ar = "يتحسّن" if optimistic else "يتراجع"

    active_params = {k: v for k, v in params.items() if abs(v) > 0.01}

    if active_params:
        param_list_en = ", ".join(
            f"{_PARAM_LABELS.get(k, k)} ({'+' if v > 0 else ''}{v:.1f}pp)"
            for k, v in active_params.items()
        )
        param_list_ar = "، ".join(
            f"{_PARAM_LABELS_AR.get(k, k)} ({'+' if v > 0 else ''}{v:.1f} نقطة)"
            for k, v in active_params.items()
        )
        summary_en = (
            f"Under the simulated scenario ({param_list_en}), the {ind_name} is projected to "
            f"{direction_en} by {abs(impact_pp):.2f} percentage points relative to the baseline, "
            f"reaching {scenario_forecast.iloc[-1]:.1f}{unit} by end of the forecast horizon. "
            f"{'This represents a meaningful policy gain achievable through sustained reform investment.' if optimistic else 'This highlights vulnerability to adverse macro conditions — mitigating policy measures are advisable.'}"
        )
        summary_ar = (
            f"في ظل السيناريو المُحاكى ({param_list_ar})، يُتوقع أن {direction_ar} {INDICATORS[indicator].get('name_ar', ind_name)} "
            f"بمقدار {abs(impact_pp):.2f} نقطة مئوية مقارنةً بالسيناريو الأساسي، "
            f"ليبلغ {scenario_forecast.iloc[-1]:.1f}{unit} بنهاية أفق التنبؤ. "
            f"{'يُمثّل ذلك مكسبًا سياسيًا ملموسًا يمكن تحقيقه من خلال الاستثمار المستدام في الإصلاح.' if optimistic else 'يكشف ذلك عن هشاشة حيال الظروف الاقتصادية السلبية — ويُنصح باتخاذ تدابير تخفيف وقائية.'}"
        )
    else:
        summary_en = "No scenario adjustments applied. Displaying baseline forecast."
        summary_ar = "لم يتم تطبيق أي تعديلات. يعرض النظام التوقعات الأساسية."

    return ScenarioResult(
        baseline_forecast=baseline_forecast,
        scenario_forecast=scenario_forecast,
        baseline_lower=baseline_lower,
        baseline_upper=baseline_upper,
        scenario_lower=scenario_lower,
        scenario_upper=scenario_upper,
        total_impact_pp=round(impact_pp, 3),
        total_impact_pct=round(impact_pct, 2),
        driver_contributions=contributions,
        summary_en=summary_en,
        summary_ar=summary_ar,
        optimistic=optimistic,
    )


def get_param_config() -> List[dict]:
    """Return parameter configuration for UI slider construction."""
    return [
        {
            "key": k,
            "label": _PARAM_LABELS[k],
            "label_ar": _PARAM_LABELS_AR[k],
            "min": _PARAM_RANGES[k][0],
            "max": _PARAM_RANGES[k][1],
            "default": _PARAM_DEFAULTS[k],
            "step": 0.5,
        }
        for k in _PARAM_LABELS
    ]

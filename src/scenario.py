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


# ──────────────────────────────────────────────────────────────────────────────
# Strategic scenario presets
# ──────────────────────────────────────────────────────────────────────────────

SCENARIO_PRESETS: Dict[str, dict] = {
    "baseline": {
        "name":         "Baseline Outlook",
        "name_ar":      "التوقعات الأساسية",
        "icon":         "📊",
        "color":        "#1B4F72",
        "severity":     "neutral",
        "description":  "No policy changes. AI-generated baseline forecast only.",
        "description_ar": "بدون تغييرات في السياسات. التوقع الأساسي فحسب.",
        "params": {"gdp_growth": 0.0, "digital_investment": 0.0, "education_investment": 0.0,
                   "labor_reforms": 0.0, "population_growth": 0.0},
    },
    "digital_acceleration": {
        "name":         "Digital Acceleration",
        "name_ar":      "التسارع الرقمي",
        "icon":         "⚡",
        "color":        "#1A7A4A",
        "severity":     "opportunity",
        "description":  "Strong digital investment + GDP uplift. Models Vision 2030 digital transformation.",
        "description_ar": "استثمار رقمي قوي ونمو اقتصادي. يُجسّد التحول الرقمي لرؤية 2030.",
        "params": {"gdp_growth": 2.0, "digital_investment": 5.0, "education_investment": 3.0,
                   "labor_reforms": 2.0, "population_growth": 0.0},
    },
    "economic_slowdown": {
        "name":         "Economic Slowdown",
        "name_ar":      "التباطؤ الاقتصادي",
        "icon":         "📉",
        "color":        "#A93226",
        "severity":     "risk",
        "description":  "Reduced GDP growth with negative knock-on effects on employment.",
        "description_ar": "تراجع في النمو مع تداعيات سلبية على التوظيف.",
        "params": {"gdp_growth": -3.0, "digital_investment": -2.0, "education_investment": -1.0,
                   "labor_reforms": -1.0, "population_growth": 0.0},
    },
    "inflation_stress": {
        "name":         "Inflation Stress Test",
        "name_ar":      "اختبار ضغط التضخم",
        "icon":         "🔥",
        "color":        "#C07820",
        "severity":     "warning",
        "description":  "Elevated inflation eroding real investment capacity and labour stability.",
        "description_ar": "ارتفاع التضخم يُقلّص القدرة الاستثمارية واستقرار سوق العمل.",
        "params": {"gdp_growth": -1.5, "digital_investment": -1.0, "education_investment": -0.5,
                   "labor_reforms": 0.0, "population_growth": 0.5},
    },
    "reform_expansion": {
        "name":         "Reform Expansion",
        "name_ar":      "توسّع الإصلاح",
        "icon":         "🏗",
        "color":        "#1A7A4A",
        "severity":     "opportunity",
        "description":  "Comprehensive labour reforms and education investment aligned with national vision.",
        "description_ar": "إصلاحات شاملة وتعليم متوافق مع الرؤية الوطنية.",
        "params": {"gdp_growth": 1.0, "digital_investment": 2.0, "education_investment": 5.0,
                   "labor_reforms": 4.0, "population_growth": 0.0},
    },
    "youth_recovery": {
        "name":         "Youth Employment Recovery",
        "name_ar":      "تعافي توظيف الشباب",
        "icon":         "🌱",
        "color":        "#148F77",
        "severity":     "opportunity",
        "description":  "Targeted youth labour interventions with SME absorption and reskilling.",
        "description_ar": "تدخلات شبابية موجّهة مع استيعاب المنشآت وإعادة التأهيل.",
        "params": {"gdp_growth": 1.0, "digital_investment": 1.0, "education_investment": 3.0,
                   "labor_reforms": 3.0, "population_growth": 0.0},
    },
    "population_surge": {
        "name":         "Population Surge",
        "name_ar":      "الارتفاع السكاني",
        "icon":         "👥",
        "color":        "#6C3483",
        "severity":     "pressure",
        "description":  "Accelerated demographic growth straining labour market absorption capacity.",
        "description_ar": "نمو ديموغرافي متسارع يُثقل طاقة استيعاب سوق العمل.",
        "params": {"gdp_growth": 0.0, "digital_investment": 0.0, "education_investment": 0.0,
                   "labor_reforms": 0.0, "population_growth": 2.5},
    },
    "high_growth_gcc": {
        "name":         "High Growth GCC",
        "name_ar":      "السيناريو الخليجي عالي النمو",
        "icon":         "🚀",
        "color":        "#1A7A4A",
        "severity":     "opportunity",
        "description":  "Optimistic scenario: synchronized GDP, digital investment, and reform momentum.",
        "description_ar": "سيناريو متفائل بتزامن نمو الناتج والاستثمار الرقمي والإصلاح الخليجي.",
        "params": {"gdp_growth": 4.0, "digital_investment": 5.0, "education_investment": 4.0,
                   "labor_reforms": 4.0, "population_growth": 0.5},
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Scenario intelligence engine
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ScenarioIntelligence:
    scenario_label: str
    scenario_label_ar: str
    severity: str           # "opportunity" | "risk" | "warning" | "pressure" | "neutral"
    badge_color: str        # hex color

    strategic_outlook_en: str
    strategic_outlook_ar: str
    key_impact_en: str
    key_impact_ar: str
    labor_implications_en: str
    labor_implications_ar: str
    risk_assessment_en: str
    risk_assessment_ar: str
    gcc_comparative_en: str
    gcc_comparative_ar: str
    recommended_actions_en: List[str]
    recommended_actions_ar: List[str]
    gcc_ranking_shift: int      # positive = improved rank, negative = worsened
    scenario_end_value: float
    baseline_end_value: float


_SCENARIO_LABEL_MAP: Dict[str, Tuple[str, str, str]] = {
    # key -> (EN label, AR label, hex color)
    "recovery":          ("Recovery Opportunity",        "فرصة تعافٍ",                  "#1A7A4A"),
    "digital-growth":    ("Digital Growth Opportunity",  "فرصة نمو رقمي",               "#148F77"),
    "reform-driven":     ("Reform-Driven Improvement",   "تحسّن مدفوع بالإصلاح",       "#1A7A4A"),
    "growth-accel":      ("Growth Acceleration",         "تسارع النمو",                  "#1A7A4A"),
    "strategic-stab":    ("Strategic Stabilization",     "استقرار استراتيجي",           "#1B4F72"),
    "elevated-vol":      ("Elevated Volatility",         "تذبذب مرتفع",                 "#C07820"),
    "structural-pres":   ("Structural Labor Pressure",   "ضغط هيكلي على العمالة",      "#A93226"),
    "inflation-risk":    ("Inflationary Risk",           "مخاطر تضخمية",                "#C07820"),
    "pop-pressure":      ("Demographic Pressure",        "ضغط ديموغرافي",               "#6C3483"),
    "neutral":           ("Baseline Maintained",         "الأساس محافظ عليه",           "#1B4F72"),
}

_SCENARIO_SEVERITY_MAP: Dict[str, str] = {
    "recovery":       "opportunity",
    "digital-growth": "opportunity",
    "reform-driven":  "opportunity",
    "growth-accel":   "opportunity",
    "strategic-stab": "opportunity",
    "elevated-vol":   "warning",
    "structural-pres":"risk",
    "inflation-risk": "warning",
    "pop-pressure":   "pressure",
    "neutral":        "neutral",
}


def _classify_scenario_type(
    indicator: str,
    result: "ScenarioResult",
    params: Dict[str, float],
) -> str:
    """Classify a scenario into a strategic label key."""
    has_active = any(abs(v) > 0.01 for v in params.values())
    if not has_active:
        return "neutral"

    lib = True  # default; will be overridden
    try:
        from src.gcc_data import INDICATORS
        lib = INDICATORS[indicator]["lower_is_better"]
    except Exception:
        pass

    contribs = result.driver_contributions
    dominant = (
        max(contribs, key=lambda k: abs(contribs[k]))
        if contribs else None
    )
    impact_abs = abs(result.total_impact_pp)
    optimistic = result.optimistic

    if optimistic:
        if impact_abs < 0.3:
            return "strategic-stab"
        if dominant == "digital_investment":
            return "digital-growth"
        if dominant in ("labor_reforms", "education_investment"):
            return "reform-driven"
        if indicator == "youth_unemployment_rate" and impact_abs > 1.5:
            return "recovery"
        return "growth-accel"
    else:
        if params.get("population_growth", 0) > 1.0:
            dominant_pop = not any(
                abs(params.get(k, 0)) > abs(params.get("population_growth", 0)) * 0.5
                for k in ("gdp_growth", "digital_investment", "education_investment", "labor_reforms")
            )
            if dominant_pop:
                return "pop-pressure"
        if params.get("gdp_growth", 0) < -1.0 and impact_abs > 0.5:
            return "inflation-risk"
        if impact_abs > 1.5:
            return "structural-pres"
        return "elevated-vol"


def generate_scenario_intelligence(
    country: str,
    indicator: str,
    result: "ScenarioResult",
    params: Dict[str, float],
    preset_name: str = "",
) -> ScenarioIntelligence:
    """
    Generate ministry-grade structured bilingual scenario intelligence:
    strategic outlook, impact analysis, GCC comparison, and policy actions.
    """
    from src.gcc_data import INDICATORS, COUNTRIES
    from src.intelligence import _COUNTRY_CONTEXT, _INDICATOR_POLICY

    ind_meta = INDICATORS[indicator]
    ind_name = ind_meta["name"]
    ind_name_ar = ind_meta.get("name_ar", ind_name)
    unit = ind_meta["unit"]
    lib = ind_meta["lower_is_better"]
    flag = COUNTRIES[country]["flag"]
    ctx = _COUNTRY_CONTEXT.get(country, {})
    vision = ctx.get("vision", "the national vision")
    strength = ctx.get("strength", "structural economic reforms")
    challenge = ctx.get("challenge", "structural challenges")
    strength_ar = ctx.get("strength_ar", "الإصلاحات الهيكلية")
    challenge_ar = ctx.get("challenge_ar", "التحديات الهيكلية")

    # Core impact numbers
    scenario_end = float(result.scenario_forecast.iloc[-1])
    baseline_end = float(result.baseline_forecast.iloc[-1])
    impact_pp = result.total_impact_pp
    impact_pct = result.total_impact_pct
    impact_abs = abs(impact_pp)
    horizon = len(result.scenario_forecast)
    optimistic = result.optimistic

    # Dominant driver
    contribs = result.driver_contributions
    dominant_key = (
        max(contribs, key=lambda k: abs(contribs[k]))
        if contribs else "gdp_growth"
    )
    dominant_label = _PARAM_LABELS.get(dominant_key, dominant_key)
    dominant_contrib = contribs.get(dominant_key, 0.0)

    # Direction words
    dir_en = "improve" if optimistic else "deteriorate"
    dir_en2 = "improvement" if optimistic else "deterioration"
    dir_ar = "يتحسّن" if optimistic else "يتراجع"
    dir_ar2 = "تحسّنًا" if optimistic else "تراجعًا"

    # Scenario classification
    sc_type = _classify_scenario_type(indicator, result, params)
    label_en, label_ar, badge_color = _SCENARIO_LABEL_MAP.get(
        sc_type, ("Scenario Analysis", "تحليل السيناريو", "#1B4F72")
    )
    severity = _SCENARIO_SEVERITY_MAP.get(sc_type, "neutral")

    # ── GCC Comparative Impact ────────────────────────────────────────────────
    # Estimate the same scenario elasticity applied to all GCC countries
    try:
        from src.gcc_data import get_trend_stats
        elasticities = _ELASTICITIES.get(indicator, {})
        total_shift_scenario = sum(
            elasticities.get(k, 0.0) * v for k, v in params.items()
        )
        country_impacts: Dict[str, float] = {}
        for c in COUNTRIES:
            latest_c = get_trend_stats(c, indicator).get("latest", 0.0)
            # Apply scenario shift (same params) — scenario end estimate
            scenario_est = latest_c + total_shift_scenario
            country_impacts[c] = scenario_est

        # Rank by scenario-adjusted value (best first = lower for lib)
        sorted_countries = sorted(
            country_impacts.keys(),
            key=lambda c: country_impacts[c] * (1 if lib else -1),
        )
        scenario_rank = sorted_countries.index(country) + 1
        # Baseline rank
        baseline_vals = {c: get_trend_stats(c, indicator).get("latest", 0.0) for c in COUNTRIES}
        sorted_baseline = sorted(
            baseline_vals.keys(),
            key=lambda c: baseline_vals[c] * (1 if lib else -1),
        )
        baseline_rank = sorted_baseline.index(country) + 1
        rank_shift = baseline_rank - scenario_rank  # positive = rank improved
        best_scenario_country = sorted_countries[0]
        best_scenario_val = country_impacts[best_scenario_country]
        gcc_scenario_avg = sum(country_impacts.values()) / len(country_impacts)
        vs_gcc_scenario = scenario_end - gcc_scenario_avg
        gcc_comparison_available = True
    except Exception:
        rank_shift = 0
        scenario_rank = 0
        baseline_rank = 0
        best_scenario_country = ""
        best_scenario_val = 0.0
        gcc_scenario_avg = scenario_end
        vs_gcc_scenario = 0.0
        gcc_comparison_available = False

    # ── English narratives ────────────────────────────────────────────────────
    preset_label = (
        SCENARIO_PRESETS[preset_name]["name"]
        if preset_name and preset_name in SCENARIO_PRESETS
        else "Custom"
    )

    # Strategic Outlook
    if optimistic:
        strategic_outlook_en = (
            f"Under the **{preset_label}** scenario ({label_en}), "
            f"{flag} {country}'s {ind_name} is projected to {dir_en} by "
            f"{impact_abs:.2f}pp over the {horizon}-period forecast horizon, "
            f"reaching {scenario_end:.1f}{unit} compared to the {baseline_end:.1f}{unit} baseline. "
            f"This trajectory is consistent with {vision} reform priorities and demonstrates "
            f"the structural responsiveness of {country}'s labour market to "
            f"{dominant_label.lower()} interventions. "
            f"{'Sustained reform investment can amplify these gains beyond the modelled horizon.' if impact_abs > 1.5 else 'The moderate magnitude suggests incremental gains achievable through targeted policy alignment.'}"
        )
    else:
        strategic_outlook_en = (
            f"The **{preset_label}** scenario ({label_en}) reveals meaningful downside risk for "
            f"{flag} {country}'s {ind_name}. An estimated {impact_abs:.2f}pp {dir_en2} "
            f"would shift the indicator from {baseline_end:.1f}{unit} to {scenario_end:.1f}{unit}. "
            f"This reflects the vulnerability of the current trajectory to {dominant_label.lower()} headwinds "
            f"compounded by the structural challenge of {challenge}. "
            f"Without countervailing policy measures, this scenario poses a meaningful setback to national objectives."
        )

    # Key Economic Impact
    key_impact_en = (
        f"The primary driver is **{dominant_label}** ({contribs.get(dominant_key, 0):+.3f}pp contribution). "
        f"Total elasticity-weighted impact: **{impact_pp:+.2f}pp** ({impact_pct:+.1f}% relative change). "
        f"Policy lever breakdown: "
        + ", ".join(
            f"{_PARAM_LABELS.get(k, k)} ({v:+.2f}pp)"
            for k, v in contribs.items() if abs(v) > 0.01
        ) + "."
    )

    # Labour implications
    if indicator == "youth_unemployment_rate":
        impl_direction = "reduction" if optimistic else "increase"
        impl_word = "fewer young people facing" if optimistic else "additional young people at risk of"
        labor_implications_en = (
            f"A {impact_abs:.1f}pp {impl_direction} in youth unemployment under this scenario "
            f"represents a {'significant policy achievement' if optimistic else 'serious structural risk'} "
            f"for {country}'s youth cohort. "
            f"The labour market's response to {dominant_label.lower()} changes "
            f"reflects the elasticity-calibrated relationship between investment policy "
            f"and youth employment outcomes. "
            f"{'If sustained beyond the forecast horizon, this improvement could reduce long-term unemployment scarring effects.' if optimistic else 'Without intervention, the trajectory may result in elevated long-term unemployment among youth cohorts.'}"
        )
    elif indicator == "gdp_growth":
        labor_implications_en = (
            f"{'Accelerated' if optimistic else 'Reduced'} GDP growth under this scenario "
            f"carries {'positive' if optimistic else 'negative'} secondary employment effects. "
            f"The Okun-style elasticity model suggests that a {impact_abs:.1f}pp shift in GDP growth "
            f"translates to commensurate changes in labour market absorption capacity. "
            f"{'Strong fiscal headroom created by growth expansion can fund active labour market programmes.' if optimistic else 'Reduced fiscal space may constrain employment programme funding and private-sector hiring incentives.'}"
        )
    else:
        labor_implications_en = (
            f"This scenario's {impact_abs:.1f}pp shift in {ind_name} carries "
            f"{'positive' if optimistic else 'negative'} indirect effects on labour market conditions. "
            f"{'Improved conditions create favourable investment environment supporting youth employment.' if optimistic else 'Deteriorating conditions may constrain employer hiring capacity and youth wage growth.'} "
            f"Policy coordination between {ind_name.lower()} management and active employment programmes "
            f"is advised to maximise the scenario's labour market transmission."
        )

    # Risk assessment
    if optimistic:
        risk_en = (
            f"Primary execution risks under the {label_en} scenario include: "
            f"(1) Implementation lag — policy reforms typically take 12–24 months to transmit fully to employment outcomes; "
            f"(2) Global macroeconomic headwinds that could partially offset the modelled gains; "
            f"(3) The structural challenge of {challenge} may moderate progress even with favourable conditions. "
            f"Forecast model uncertainty (elasticity-based) is inherent — outcomes could vary from the modelled {impact_abs:.1f}pp impact."
        )
    else:
        risk_en = (
            f"Under the {label_en} scenario, key risk amplifiers include: "
            f"(1) Feedback loops — {dominant_label.lower()} deterioration can trigger confidence shocks "
            f"accelerating the modelled {impact_abs:.1f}pp adverse impact; "
            f"(2) The pre-existing structural challenge of {challenge} compounds the downside risk; "
            f"(3) Regional contagion effects if GCC peers face similar conditions simultaneously. "
            f"Early warning monitoring and contingency fiscal measures are recommended."
        )

    # GCC Comparative
    if gcc_comparison_available:
        vs_gcc_dir = "better" if ((vs_gcc_scenario < 0 and lib) or (vs_gcc_scenario > 0 and not lib)) else "worse"
        rank_change_text = (
            f"improving from rank #{baseline_rank} to #{scenario_rank}" if rank_shift > 0
            else (f"declining from rank #{baseline_rank} to #{scenario_rank}" if rank_shift < 0
                  else f"maintaining rank #{baseline_rank}")
        )
        gcc_comparative_en = (
            f"Applying the same scenario parameters across all GCC economies, "
            f"{country} performs {vs_gcc_dir} than the projected GCC average "
            f"({gcc_scenario_avg:.1f}{unit}) by {abs(vs_gcc_scenario):.1f}pp, "
            f"{rank_change_text} in the regional ranking. "
            f"{'This positions ' + country + ' as a regional leader under this scenario.' if scenario_rank == 1 else ''}"
            f"{'The best-performing GCC economy under this scenario is ' + best_scenario_country + ' (' + str(round(best_scenario_val, 1)) + unit + ').' if best_scenario_country != country else ''}"
        )
    else:
        gcc_comparative_en = (
            f"Regional comparative data not available for this scenario configuration. "
            "GCC-wide scenario benchmarking is recommended as a supplementary analysis."
        )

    # Recommended actions (reuse indicator policy + scenario direction)
    from src.intelligence import _INDICATOR_POLICY
    pol = _INDICATOR_POLICY.get(indicator, {})
    pol_key = "improving" if optimistic else "worsening"
    recs_en = pol.get(pol_key, pol.get("improving", []))[:4]
    recs_ar = pol.get(f"{pol_key}_ar", pol.get("improving_ar", []))[:4]

    # ── Arabic narratives ─────────────────────────────────────────────────────
    preset_label_ar = (
        SCENARIO_PRESETS[preset_name]["name_ar"]
        if preset_name and preset_name in SCENARIO_PRESETS
        else "مُخصَّص"
    )

    ar_optimistic_word = "إيجابيًا" if optimistic else "سلبيًا"

    strategic_outlook_ar = (
        f"في إطار سيناريو **{preset_label_ar}** ({label_ar})، "
        f"يُتوقع أن {dir_ar} {ind_name_ar} في {country} بمقدار "
        f"{impact_abs:.2f} نقطة مئوية خلال {horizon} فترات قادمة، "
        f"ليصل إلى {scenario_end:.1f}{unit} مقارنةً بالأساس البالغ {baseline_end:.1f}{unit}. "
        f"يتوافق هذا المسار {ar_optimistic_word} مع أولويات إصلاحات {vision}. "
        f"{'يمكن لاستدامة الاستثمار الإصلاحي تعزيز هذه المكاسب ما وراء أفق التنبؤ.' if optimistic else 'تدابير سياسية مضادة ضرورية لمنع تفاقم هذا المسار.'}"
    )

    dominant_label_ar = _PARAM_LABELS_AR.get(dominant_key, dominant_label)
    key_impact_ar = (
        f"المحرك الرئيسي: **{dominant_label_ar}** ({contribs.get(dominant_key, 0):+.3f} نقطة). "
        f"الأثر الإجمالي الموزون: **{impact_pp:+.2f} نقطة** ({impact_pct:+.1f}% تغيّر نسبي). "
        f"تفصيل الرافعات: "
        + "، ".join(
            f"{_PARAM_LABELS_AR.get(k, k)} ({v:+.2f} نقطة)"
            for k, v in contribs.items() if abs(v) > 0.01
        ) + "."
    )

    if indicator == "youth_unemployment_rate":
        labor_implications_ar = (
            f"{'انخفاض' if optimistic else 'ارتفاع'} بطالة الشباب بمقدار {impact_abs:.1f} نقطة مئوية "
            f"في ظل هذا السيناريو يُمثّل {'إنجازًا سياسيًا مهمًا' if optimistic else 'خطرًا هيكليًا بالغًا'} "
            f"لفئة الشباب في {country}. "
            f"{'إذا استُدام هذا التحسّن، يمكنه تقليص الآثار الندبية طويلة الأمد لبطالة الشباب.' if optimistic else 'دون تدخل، قد تتصاعد البطالة طويلة الأمد في أوساط الفئات الشبابية.'}"
        )
    else:
        labor_implications_ar = (
            f"يحمل هذا السيناريو تداعيات {'إيجابية' if optimistic else 'سلبية'} غير مباشرة "
            f"على سوق العمل. "
            f"{'الظروف المحسّنة تُهيّئ بيئة استثمارية داعمة لتوظيف الشباب.' if optimistic else 'تراجع الأوضاع قد يُقيّد قدرة أصحاب العمل على التوظيف ونمو أجور الشباب.'}"
        )

    risk_assessment_ar = (
        f"المخاطر الرئيسية {'المحيطة بتحقيق' if optimistic else 'الناجمة عن'} سيناريو {label_ar}: "
        f"(1) {'فجوة التنفيذ — تستغرق الإصلاحات 12-24 شهرًا للانتقال إلى نتائج التوظيف.' if optimistic else 'حلقات التغذية الراجعة — تدهور الوضع قد يُسرّع الأثر المُنمذَج.'} "
        f"(2) {'الصدمات الاقتصادية الخارجية قد تُعوّض المكاسب المُنمذَجة جزئيًا.' if optimistic else 'التحدي الهيكلي في ' + challenge_ar + ' يُضاعف مخاطر الجانب السلبي.'} "
        f"(3) {'التحدي الهيكلي في ' + challenge_ar + ' قد يُخفّف وتيرة التحسّن.' if optimistic else 'التداعيات الإقليمية إذا واجهت دول الخليج ظروفًا مماثلة.'}"
    )

    if gcc_comparison_available:
        vs_gcc_dir_ar = "أفضل" if ((vs_gcc_scenario < 0 and lib) or (vs_gcc_scenario > 0 and not lib)) else "أضعف"
        rank_ar = (
            f"تحسّن من المرتبة #{baseline_rank} إلى #{scenario_rank}" if rank_shift > 0
            else (f"تراجع من المرتبة #{baseline_rank} إلى #{scenario_rank}" if rank_shift < 0
                  else f"الحفاظ على المرتبة #{baseline_rank}")
        )
        gcc_comparative_ar = (
            f"بتطبيق معاملات السيناريو ذاتها على جميع اقتصادات الخليج، "
            f"يُسجّل {country} أداءً {vs_gcc_dir_ar} من المتوسط الإقليمي المتوقع "
            f"({gcc_scenario_avg:.1f}{unit}) بفارق {abs(vs_gcc_scenario):.1f} نقطة، "
            f"{rank_ar} في التصنيف الإقليمي. "
        )
    else:
        gcc_comparative_ar = "بيانات المقارنة الإقليمية غير متاحة. تُنصح بالمعايرة الخليجية كتحليل تكميلي."

    return ScenarioIntelligence(
        scenario_label=label_en,
        scenario_label_ar=label_ar,
        severity=severity,
        badge_color=badge_color,
        strategic_outlook_en=strategic_outlook_en,
        strategic_outlook_ar=strategic_outlook_ar,
        key_impact_en=key_impact_en,
        key_impact_ar=key_impact_ar,
        labor_implications_en=labor_implications_en,
        labor_implications_ar=labor_implications_ar,
        risk_assessment_en=risk_en,
        risk_assessment_ar=risk_assessment_ar,
        gcc_comparative_en=gcc_comparative_en,
        gcc_comparative_ar=gcc_comparative_ar,
        recommended_actions_en=recs_en,
        recommended_actions_ar=recs_ar,
        gcc_ranking_shift=rank_shift,
        scenario_end_value=scenario_end,
        baseline_end_value=baseline_end,
    )

"""Decomposition, explanation generation, and Arabic report utilities."""

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd


@dataclass
class Decomposition:
    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    trend_direction: str          # "increasing" | "decreasing" | "stable"
    seasonality_strength: float   # 0–1


@dataclass
class ExplanationResult:
    model_name: str
    model_smape: float
    trend_direction: str
    seasonality_strength: float
    forecast_direction: str
    last_value: float
    forecast_end_value: float
    change_pct: float
    data_quality_issues: List[str]
    feature_importance: Optional[pd.Series]
    confidence_level: float
    freq: str


def decompose_series(y: pd.Series, freq: str = "M") -> Decomposition:
    """Additive STL-style decomposition using statsmodels."""
    from statsmodels.tsa.seasonal import seasonal_decompose

    period = 12 if freq == "M" else 1

    try:
        if period > 1 and len(y) >= 2 * period:
            result = seasonal_decompose(y, model="additive", period=period, extrapolate_trend="freq")
            trend = result.trend.dropna()
            seasonal = result.seasonal
            residual = result.resid.dropna()
        else:
            # No seasonality — use linear trend
            x = np.arange(len(y))
            coeffs = np.polyfit(x, y.values, 1)
            trend_vals = np.polyval(coeffs, x)
            trend = pd.Series(trend_vals, index=y.index)
            seasonal = pd.Series(np.zeros(len(y)), index=y.index)
            residual = y - trend
    except Exception:
        trend = y.copy()
        seasonal = pd.Series(np.zeros(len(y)), index=y.index)
        residual = pd.Series(np.zeros(len(y)), index=y.index)

    # Trend direction from first-vs-last half mean
    mid = len(trend) // 2
    first_half = trend.iloc[:mid].mean()
    second_half = trend.iloc[mid:].mean()
    pct_change = (second_half - first_half) / (abs(first_half) + 1e-8)
    if pct_change > 0.02:
        direction = "increasing"
    elif pct_change < -0.02:
        direction = "decreasing"
    else:
        direction = "stable"

    # Seasonality strength: var(seasonal) / var(seasonal + residual)
    seasonal_var = float(seasonal.var())
    total_var = float((seasonal + residual).var())
    strength = seasonal_var / (total_var + 1e-8) if total_var > 0 else 0.0
    strength = float(np.clip(strength, 0.0, 1.0))

    return Decomposition(
        trend=trend,
        seasonal=seasonal,
        residual=residual,
        trend_direction=direction,
        seasonality_strength=strength,
    )


def generate_explanation(
    series: pd.Series,
    forecast: pd.Series,
    lower: pd.Series,
    upper: pd.Series,
    model_name: str,
    model_smape: float,
    freq: str,
    data_quality_issues: List[str],
    feature_importance: Optional[pd.Series],
    confidence_level: float,
) -> ExplanationResult:
    """Summarise forecasting results into a structured explanation object."""
    decomp = decompose_series(series, freq=freq)
    last_value = float(series.iloc[-1])
    forecast_end_value = float(forecast.iloc[-1])
    change_pct = (forecast_end_value - last_value) / (abs(last_value) + 1e-8) * 100

    if change_pct > 1:
        forecast_direction = "increasing"
    elif change_pct < -1:
        forecast_direction = "decreasing"
    else:
        forecast_direction = "stable"

    return ExplanationResult(
        model_name=model_name,
        model_smape=model_smape,
        trend_direction=decomp.trend_direction,
        seasonality_strength=decomp.seasonality_strength,
        forecast_direction=forecast_direction,
        last_value=last_value,
        forecast_end_value=forecast_end_value,
        change_pct=change_pct,
        data_quality_issues=data_quality_issues,
        feature_importance=feature_importance,
        confidence_level=confidence_level,
        freq=freq,
    )


def generate_arabic_report(explanation: ExplanationResult, indicator_name: str) -> str:
    """Produce an Arabic-language decision-support narrative."""

    freq_label = "شهري" if explanation.freq == "M" else "سنوي"

    trend_map = {
        "increasing": "تصاعدي",
        "decreasing": "تنازلي",
        "stable": "مستقر",
    }
    trend_ar = trend_map.get(explanation.trend_direction, explanation.trend_direction)
    forecast_ar = trend_map.get(explanation.forecast_direction, explanation.forecast_direction)

    seasonality_pct = explanation.seasonality_strength * 100
    if explanation.seasonality_strength > 0.3:
        seasonality_text = f"تُشير البيانات إلى وجود موسمية واضحة بقوة {seasonality_pct:.0f}%."
    elif explanation.seasonality_strength > 0.1:
        seasonality_text = f"لوحظ أثر موسمي معتدل بقوة {seasonality_pct:.0f}%."
    else:
        seasonality_text = "لم يُلاحَظ أثر موسمي واضح في البيانات."

    quality_text = ""
    if explanation.data_quality_issues:
        quality_text = "\n⚠️ ملاحظات جودة البيانات:\n"
        for issue in explanation.data_quality_issues:
            quality_text += f"  • {issue}\n"

    importance_text = ""
    if explanation.feature_importance is not None and len(explanation.feature_importance) > 0:
        top_features = explanation.feature_importance.head(3)
        importance_text = "\n📊 أهم المتغيرات التفسيرية:\n"
        for feat, val in top_features.items():
            importance_text += f"  • {feat}: {val:.4f}\n"

    report = f"""
╔══════════════════════════════════════════════════════════╗
║          تقرير التنبؤ بالمؤشرات الإحصائية الرسمية         ║
╚══════════════════════════════════════════════════════════╝

📌 المؤشر: {indicator_name}
📅 التكرار الزمني: {freq_label}

─────────────────────────────────────────────────────────
1. النموذج المُختار
─────────────────────────────────────────────────────────
النموذج: {explanation.model_name}
دقة النموذج (sMAPE): {explanation.model_smape:.2f}%
مستوى الثقة لفترات التنبؤ: {explanation.confidence_level * 100:.0f}%

─────────────────────────────────────────────────────────
2. تحليل الاتجاه والموسمية
─────────────────────────────────────────────────────────
اتجاه السلسلة التاريخية: {trend_ar}
{seasonality_text}

─────────────────────────────────────────────────────────
3. نتائج التنبؤ
─────────────────────────────────────────────────────────
آخر قيمة مُسجَّلة: {explanation.last_value:,.2f}
القيمة المتوقعة عند نهاية الأفق: {explanation.forecast_end_value:,.2f}
التغيُّر المتوقع: {explanation.change_pct:+.2f}%
اتجاه التنبؤ: {forecast_ar}
{quality_text}{importance_text}
─────────────────────────────────────────────────────────
4. التوصيات
─────────────────────────────────────────────────────────
"""

    if explanation.forecast_direction == "increasing":
        report += "• يُنصح بمراجعة الطاقة الاستيعابية والموارد المخصصة لهذا المؤشر.\n"
        report += "• ينبغي تعزيز خطط التوسع لمواكبة النمو المتوقع.\n"
    elif explanation.forecast_direction == "decreasing":
        report += "• يُنصح بتحليل أسباب التراجع المتوقع واتخاذ إجراءات تصحيحية.\n"
        report += "• ينبغي مراجعة السياسات الحالية للحدّ من الانخفاض.\n"
    else:
        report += "• المؤشر في حالة استقرار نسبي؛ يُنصح بمتابعة التطورات الدورية.\n"

    if explanation.data_quality_issues:
        report += "• يُوصى بتحسين جودة البيانات لرفع دقة التنبؤات المستقبلية.\n"

    report += "\n══════════════════════════════════════════════════════════\n"

    return report

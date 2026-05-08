"""
AI Decision Intelligence Engine.

Generates bilingual (English / Arabic) executive narratives, policy
recommendations, risk assessments, and strategic outlooks from forecast data.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class IntelligenceReport:
    country: str
    indicator: str
    indicator_name: str
    unit: str
    # English
    executive_summary: str
    key_insights: List[str]
    risk_assessment: List[str]
    influencing_factors: List[str]
    policy_recommendations: List[str]
    forecast_outlook: str
    # Arabic
    ar_executive_summary: str
    ar_key_insights: List[str]
    ar_risk_assessment: List[str]
    ar_policy_recommendations: List[str]
    ar_forecast_outlook: str
    # Metadata
    trend_label: str        # "Improving" | "Worsening" | "Stable"
    trend_label_ar: str
    urgency_level: str      # "High" | "Medium" | "Low"
    model_name: str
    model_smape: float


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _slope_label(slope: float, lower_is_better: bool) -> tuple:
    """Return (English label, Arabic label, improving bool)."""
    improving = (slope < 0) if lower_is_better else (slope > 0)
    if abs(slope) < 0.05:
        return "Stable", "مستقر", False
    if improving:
        return "Improving", "في تحسّن", True
    return "Worsening", "في تراجع", False


def _urgency(latest: float, slope: float, lower_is_better: bool) -> str:
    improving = (slope < 0) if lower_is_better else (slope > 0)
    if lower_is_better:
        if latest > 25 or (not improving and latest > 15):
            return "High"
        if latest > 15 or not improving:
            return "Medium"
    else:
        if latest < 40 or (not improving and latest < 70):
            return "High"
        if latest < 65 or not improving:
            return "Medium"
    return "Low"


def _fmt(v: float, unit: str) -> str:
    return f"{v:.1f}{unit}"


def _direction_word(change: float, lower_is_better: bool) -> str:
    if abs(change) < 0.1:
        return "remain broadly stable"
    if (change < 0 and lower_is_better) or (change > 0 and not lower_is_better):
        return f"improve by {abs(change):.1f} percentage points"
    return f"deteriorate by {abs(change):.1f} percentage points"


def _direction_word_ar(change: float, lower_is_better: bool) -> str:
    if abs(change) < 0.1:
        return "يبقى مستقرًا إلى حدٍّ بعيد"
    if (change < 0 and lower_is_better) or (change > 0 and not lower_is_better):
        return f"يتحسّن بمقدار {abs(change):.1f} نقطة مئوية"
    return f"يتراجع بمقدار {abs(change):.1f} نقطة مئوية"


# ──────────────────────────────────────────────────────────────────────────────
# Country context
# ──────────────────────────────────────────────────────────────────────────────

_COUNTRY_CONTEXT = {
    "Saudi Arabia": {
        "vision": "Vision 2030",
        "strength": "ongoing structural labour market reforms and rapid private-sector expansion",
        "challenge": "high public-sector dependency and graduate-skills mismatch",
        "strength_ar": "الإصلاحات الهيكلية المتسارعة في سوق العمل والتوسع السريع في القطاع الخاص",
        "challenge_ar": "الاعتماد المرتفع على القطاع الحكومي وعدم التوافق بين مهارات الخريجين ومتطلبات السوق",
    },
    "UAE": {
        "vision": "UAE Centennial 2071",
        "strength": "world-class digital infrastructure and diversified economic base",
        "challenge": "maintaining competitiveness in attracting high-skilled national youth talent",
        "strength_ar": "البنية التحتية الرقمية العالمية والقاعدة الاقتصادية المتنوعة",
        "challenge_ar": "الحفاظ على التنافسية في استقطاب كفاءات الشباب المواطن",
    },
    "Qatar": {
        "vision": "Qatar National Vision 2030",
        "strength": "strong sovereign wealth and post-2022 World Cup economic momentum",
        "challenge": "expanding private-sector youth employment beyond the oil and gas sector",
        "strength_ar": "الثروة السيادية الضخمة والزخم الاقتصادي في مرحلة ما بعد كأس العالم 2022",
        "challenge_ar": "توسيع توظيف الشباب في القطاع الخاص خارج نطاق قطاع النفط والغاز",
    },
    "Kuwait": {
        "vision": "Kuwait Vision 2035",
        "strength": "significant hydrocarbon revenue providing fiscal space for reform",
        "challenge": "entrenched public-sector preference and slow private-sector development",
        "strength_ar": "عائدات النفط الضخمة التي توفر هامشًا ماليًا واسعًا للإصلاح",
        "challenge_ar": "الميل الراسخ نحو العمل الحكومي وبطء تطوير القطاع الخاص",
    },
    "Bahrain": {
        "vision": "Bahrain Economic Vision 2030",
        "strength": "pioneering financial services sector and progressive labour market policies",
        "challenge": "limited natural resource base intensifying diversification urgency",
        "strength_ar": "ريادة قطاع الخدمات المالية وسياسات سوق العمل التقدمية",
        "challenge_ar": "محدودية الموارد الطبيعية مما يُعجّل الحاجة إلى التنويع الاقتصادي",
    },
    "Oman": {
        "vision": "Oman Vision 2040",
        "strength": "accelerating economic diversification across tourism, logistics, and manufacturing",
        "challenge": "higher youth population growth rate creating sustained labour market pressure",
        "strength_ar": "التنويع الاقتصادي المتسارع في السياحة والخدمات اللوجستية والصناعة",
        "challenge_ar": "المعدل المرتفع لنمو الشباب مما يولّد ضغطًا مستمرًا على سوق العمل",
    },
}

_INDICATOR_POLICY = {
    "youth_unemployment_rate": {
        "improving": [
            "Sustain momentum through targeted SME support programmes that absorb graduate talent.",
            "Institutionalise public–private internship pipelines aligned with national vision priorities.",
            "Expand vocational training tied to in-demand digital and green economy roles.",
            "Strengthen early-warning labour market dashboards to detect emerging unemployment clusters.",
        ],
        "worsening": [
            "Urgently scale active labour market programmes, including subsidised employment schemes.",
            "Introduce accelerated reskilling grants for youth in declining sectors.",
            "Review regulatory barriers to youth entrepreneurship and self-employment.",
            "Commission independent assessment of structural barriers to private-sector hiring.",
        ],
        "improving_ar": [
            "استدامة الزخم من خلال برامج دعم المنشآت الصغيرة والمتوسطة التي تستوعب الكفاءات الشابة.",
            "تأسيس مسارات تدريب موصوفة بين القطاعين العام والخاص متوافقة مع أولويات الرؤية الوطنية.",
            "توسيع برامج التدريب المهني المرتبطة بالوظائف عالية الطلب في الاقتصاد الرقمي والأخضر.",
            "تعزيز لوحات الإنذار المبكر لرصد بؤر البطالة الناشئة.",
        ],
        "worsening_ar": [
            "توسيع نطاق برامج سوق العمل النشطة بشكل عاجل، بما فيها مخططات التوظيف المدعومة.",
            "إطلاق منح إعادة التأهيل المعجّلة للشباب في القطاعات المتراجعة.",
            "مراجعة العقبات التنظيمية أمام ريادة الأعمال الشبابية والعمل الحر.",
            "الاستعانة بتقييم مستقل للعوائق الهيكلية أمام التوظيف في القطاع الخاص.",
        ],
    },
    "labor_force_participation": {
        "improving": [
            "Deepen flexible and remote-work policies to maintain participation gains.",
            "Invest in women-in-tech programmes where gender gaps remain.",
            "Strengthen employer incentive schemes for retaining young workers.",
        ],
        "worsening": [
            "Launch national participation campaigns targeting discouraged youth cohorts.",
            "Introduce participation benchmarks in government procurement criteria.",
            "Reduce friction in job-seeking through unified digital labour market platforms.",
        ],
        "improving_ar": [
            "تعميق سياسات العمل المرن والعمل عن بُعد للحفاظ على مكاسب المشاركة.",
            "الاستثمار في برامج المرأة في التقنية حيث لا تزال الفجوات قائمة.",
            "تعزيز حوافز أصحاب العمل للاحتفاظ بالعمالة الشابة.",
        ],
        "worsening_ar": [
            "إطلاق حملات وطنية تستهدف شريحة الشباب المحبطين عن العمل.",
            "إدراج معايير مشاركة الشباب في شروط المشتريات الحكومية.",
            "تخفيف الاحتكاك في البحث عن العمل عبر منصات رقمية موحّدة.",
        ],
    },
    # ── World Bank indicator: GDP Growth Rate ─────────────────────────────────
    "gdp_growth": {
        "improving": [
            "Leverage fiscal headroom created by GDP growth to fund active labour market programmes.",
            "Use expansion phase to accelerate private-sector capacity building and youth hiring incentives.",
            "Institutionalise counter-cyclical employment buffers to smooth future downturns.",
            "Direct growth dividends toward vocational and digital reskilling funds.",
        ],
        "worsening": [
            "Prioritise productivity-enhancing public investment to restore growth momentum.",
            "Introduce targeted fiscal stimulus measures focused on labour-intensive sectors.",
            "Review structural barriers to non-oil private investment to diversify the growth base.",
            "Strengthen social protection floors to cushion youth employment during low-growth periods.",
        ],
        "improving_ar": [
            "الاستفادة من الهامش المالي الناجم عن النمو الاقتصادي لتمويل برامج سوق العمل النشطة.",
            "توظيف مرحلة التوسع لتسريع بناء قدرات القطاع الخاص وتحفيز توظيف الشباب.",
            "تأسيس مخازن توظيف مضادة للدورة الاقتصادية للتخفيف من آثار التباطؤ المستقبلي.",
            "توجيه عائدات النمو نحو صناديق إعادة التأهيل المهني والرقمي.",
        ],
        "worsening_ar": [
            "إعطاء الأولوية للاستثمار العام المعزز للإنتاجية لاستعادة زخم النمو.",
            "إطلاق حزم تحفيز مالي مُستهدَفة تُركّز على القطاعات كثيفة العمالة.",
            "مراجعة العوائق الهيكلية أمام الاستثمار الخاص غير النفطي لتنويع قاعدة النمو.",
            "تعزيز شبكات الحماية الاجتماعية لحماية توظيف الشباب في فترات النمو المنخفض.",
        ],
    },
    # ── World Bank indicator: Inflation Rate ──────────────────────────────────
    "inflation": {
        "improving": [
            "Sustain inflation discipline through credible monetary and fiscal coordination.",
            "Use price stability to anchor long-term business confidence and private hiring.",
            "Expand price-stabilisation mechanisms for essential goods affecting household budgets.",
            "Institutionalise independent price monitoring to pre-empt supply-side shocks.",
        ],
        "worsening": [
            "Coordinate monetary tightening with targeted support for youth-employment-intensive sectors.",
            "Introduce supply-side relief measures (logistics, food imports) to reduce cost-push inflation.",
            "Protect real wages of young workers through indexed minimum wage adjustments.",
            "Identify and address structural bottlenecks driving persistent inflationary pressure.",
        ],
        "improving_ar": [
            "الحفاظ على انضباط التضخم من خلال التنسيق الموثوق بين السياسات النقدية والمالية.",
            "استثمار استقرار الأسعار لترسيخ ثقة قطاع الأعمال بعيد المدى وتوسيع التوظيف الخاص.",
            "توسيع آليات تثبيت أسعار السلع الأساسية المؤثرة في ميزانيات الأسر.",
            "تأسيس رقابة مستقلة على الأسعار للتحذير المبكر من الصدمات العرضية.",
        ],
        "worsening_ar": [
            "تنسيق التشديد النقدي مع دعم القطاعات كثيفة التوظيف الشبابي.",
            "اتخاذ تدابير تخفيف من جانب العرض (لوجستيات، واردات غذائية) لكبح التضخم الدفعي.",
            "حماية الأجور الحقيقية للعمال الشباب عبر تعديلات الحد الأدنى للأجور المرتبطة بالتضخم.",
            "تشخيص الاختناقات الهيكلية التي تُغذّي ضغوط التضخم المستمرة ومعالجتها.",
        ],
    },
    # ── World Bank indicator: Population Growth Rate ──────────────────────────
    "population_growth": {
        "improving": [
            "Align education and vocational training supply with demographic growth projections.",
            "Use growing youth cohorts as a competitive advantage through targeted skills development.",
            "Invest in labour market data systems that track demographic demand-supply dynamics.",
        ],
        "worsening": [
            "Review migration and residency policies affecting the active workforce composition.",
            "Invest in productivity-enhancing technology to offset declining labour force growth.",
            "Re-evaluate long-term workforce planning frameworks in light of demographic shifts.",
        ],
        "improving_ar": [
            "توافق إمدادات التعليم والتدريب المهني مع توقعات النمو الديموغرافي.",
            "توظيف فئات الشباب المتنامية ميزةً تنافسية من خلال تنمية المهارات الموجّهة.",
            "الاستثمار في أنظمة بيانات سوق العمل لرصد ديناميكيات العرض والطلب الديموغرافية.",
        ],
        "worsening_ar": [
            "مراجعة سياسات الهجرة والإقامة المؤثرة في تركيبة القوة العاملة النشطة.",
            "الاستثمار في تقنيات تعزيز الإنتاجية لتعويض تباطؤ نمو القوة العاملة.",
            "إعادة تقييم أُطر التخطيط للقوى العاملة على المدى البعيد في ضوء التحولات الديموغرافية.",
        ],
    },
    # ── World Bank indicator: Internet Usage ──────────────────────────────────
    "internet_usage": {
        "improving": [
            "Leverage rising connectivity to scale digital skilling platforms for youth.",
            "Invest in cloud and AI infrastructure to capture value from growing digital participation.",
            "Support digital entrepreneurship programmes targeting online talent pools.",
            "Use broadband penetration gains to deliver remote employment opportunities in rural areas.",
        ],
        "worsening": [
            "Prioritise national broadband expansion plans, particularly for underserved regions.",
            "Introduce digital access subsidies for lower-income youth households.",
            "Launch public digital literacy campaigns to raise participation rates.",
            "Review spectrum allocation and telecommunications market competitiveness.",
        ],
        "improving_ar": [
            "الاستفادة من الاتصال المتنامي لتوسيع منصات التأهيل الرقمي للشباب.",
            "الاستثمار في البنية التحتية السحابية والذكاء الاصطناعي لاستثمار المشاركة الرقمية المتنامية.",
            "دعم برامج ريادة الأعمال الرقمية الموجّهة نحو مجمعات المواهب الإلكترونية.",
            "توظيف مكاسب انتشار النطاق العريض لتوفير فرص العمل عن بُعد في المناطق النائية.",
        ],
        "worsening_ar": [
            "إيلاء الأولوية لخطط توسيع النطاق العريض الوطني، لا سيما في المناطق المحرومة.",
            "إدخال دعم للوصول الرقمي لأسر الشباب ذات الدخل المنخفض.",
            "إطلاق حملات وطنية لمحو الأمية الرقمية لرفع معدلات المشاركة.",
            "مراجعة تخصيص الطيف الترددي وتنافسية سوق الاتصالات.",
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Main function
# ──────────────────────────────────────────────────────────────────────────────

def generate_intelligence_report(
    country: str,
    indicator: str,
    historical: pd.Series,
    forecast: pd.Series,
    lower: pd.Series,
    upper: pd.Series,
    model_name: str,
    model_smape: float,
    gcc_average: Optional[pd.Series] = None,
) -> IntelligenceReport:
    """Generate a full bilingual intelligence report from forecast data."""
    from src.gcc_data import INDICATORS, COUNTRIES

    ind_meta = INDICATORS[indicator]
    ind_name = ind_meta["name"]
    unit = ind_meta["unit"]
    lib = INDICATORS[indicator]["lower_is_better"]
    flag = COUNTRIES[country]["flag"]

    # ── Key statistics ────────────────────────────────────────────────────────
    h_vals = historical.values
    f_vals = forecast.values
    n_hist = len(h_vals)

    slope = float(np.polyfit(np.arange(n_hist), h_vals, 1)[0])
    latest = float(h_vals[-1])
    prev = float(h_vals[-2]) if n_hist >= 2 else latest
    yoy = latest - prev

    fc_end = float(f_vals[-1])
    fc_change = fc_end - latest
    horizon = len(f_vals)

    gcc_avg_latest = float(gcc_average.iloc[-1]) if gcc_average is not None else None
    vs_gcc = (latest - gcc_avg_latest) if gcc_avg_latest else None

    trend_en, trend_ar, improving = _slope_label(slope, lib)
    urgency = _urgency(latest, slope, lib)
    pol_key = "improving" if improving else "worsening"

    ctx = _COUNTRY_CONTEXT.get(country, {})
    pol = _INDICATOR_POLICY.get(indicator, {})
    recs_en = pol.get(pol_key, pol.get("improving", []))[:4]
    recs_ar = pol.get(f"{pol_key}_ar", pol.get("improving_ar", []))[:4]

    # ── Forecast confidence interpretation ───────────────────────────────────
    avg_width = float((upper - lower).mean())
    avg_fc = float(forecast.mean())
    uncertainty_pct = avg_width / (abs(avg_fc) + 1e-6) * 100

    if uncertainty_pct < 5:
        confidence_phrase = "with high statistical confidence"
        confidence_ar = "بثقة إحصائية عالية"
    elif uncertainty_pct < 15:
        confidence_phrase = "with moderate confidence"
        confidence_ar = "بثقة إحصائية معتدلة"
    else:
        confidence_phrase = "with elevated uncertainty — wider prediction intervals advised"
        confidence_ar = "مع ارتفاع ملحوظ في درجة عدم اليقين — يُنصح بمراعاة فترات التنبؤ الأوسع"

    # ── English narrative ─────────────────────────────────────────────────────
    direction_phrase = _direction_word(fc_change, lib)

    trajectory_word = "positive" if improving else "concerning"
    exec_summary = (
        f"{flag} {country}'s {ind_name} currently stands at {_fmt(latest, unit)}, "
        f"reflecting a {trajectory_word} trajectory "
        f"over the past decade. AI-driven forecasting — using the {model_name} model "
        f"(sMAPE: {model_smape:.1f}%) — projects this indicator to {direction_phrase} "
        f"over the next {horizon} period(s) {confidence_phrase}. "
        f"{'This improvement aligns with ' + ctx.get('vision','the national vision') + ' reform objectives.' if improving else 'Targeted policy intervention is advised to reverse this trajectory.'}"
    )

    gcc_insight = ""
    if vs_gcc is not None:
        better = (vs_gcc < 0 if lib else vs_gcc > 0)
        gcc_insight = (
            f"{country} performs {'better' if better else 'worse'} than the GCC average "
            f"({_fmt(gcc_avg_latest, unit)}) by {abs(vs_gcc):.1f} percentage points."
        )

    yoy_dir = "declined" if yoy < 0 else "rose"
    yoy_signal = "positive" if (yoy < 0 and lib) or (yoy > 0 and not lib) else "negative"
    fc_dir = "improvement" if (fc_change < 0 and lib) or (fc_change > 0 and not lib) else "deterioration"
    key_insights = [
        f"The {ind_name} {yoy_dir} by {abs(yoy):.1f}pp year-on-year — a {yoy_signal} signal.",
        f"Forecasting model ({model_name}) projects a {abs(fc_change):.1f}pp {fc_dir} "
        f"reaching {_fmt(fc_end, unit)} by end of the forecast horizon.",
    ]
    if gcc_insight:
        key_insights.append(gcc_insight)
    key_insights.append(
        f"The key structural driver remains {ctx.get('strength', 'ongoing national reforms')}."
    )

    risks = [
        f"Global economic headwinds (inflationary pressure, tightening financial conditions) "
        f"may slow projected progress, widening forecast uncertainty intervals.",
        f"Structural challenge: {ctx.get('challenge', 'skills mismatch')} could moderate "
        f"the pace of improvement even under favourable macro conditions.",
        f"Model forecast error (sMAPE {model_smape:.1f}%) suggests "
        f"{'low' if model_smape < 5 else 'moderate' if model_smape < 12 else 'elevated'} "
        f"statistical risk — sensitivity analysis via scenario simulation is recommended.",
    ]
    if not improving:
        risks.insert(0, f"Trend risk: the {ind_name} has been on a worsening trajectory; "
                    f"without intervention, this is expected to persist through the forecast horizon.")

    factors = [
        f"National economic strategy ({ctx.get('vision', 'national vision')}) structural reforms.",
        "Digital economy and technology sector growth absorbing graduate talent.",
        "Global oil market conditions influencing fiscal space for employment programmes.",
        "Demographic dynamics — youth cohort size relative to labour market capacity.",
        "Regional FDI inflows and private-sector investment confidence levels.",
    ]

    outlook = (
        f"Based on the {model_name} model, the {horizon}-period outlook for {country}'s {ind_name} is "
        f"{'cautiously optimistic' if improving else 'challenging'}. "
        f"The indicator is forecast to reach {_fmt(fc_end, unit)} "
        f"(80% prediction interval: {_fmt(float(lower.iloc[-1]), unit)}–{_fmt(float(upper.iloc[-1]), unit)}). "
        f"{'If reform momentum is sustained, further structural improvement is achievable.' if improving else 'Without targeted policy action, the trend is likely to persist — immediate intervention is advisable.'}"
    )

    # ── Arabic narrative ──────────────────────────────────────────────────────
    ind_name_ar = ind_meta.get("name_ar", ind_name)
    vision_ar = ctx.get("vision", "الرؤية الوطنية")
    strength_ar = ctx.get("strength_ar", "الإصلاحات الوطنية الجارية")
    challenge_ar = ctx.get("challenge_ar", "التحديات الهيكلية")
    dir_ar = _direction_word_ar(fc_change, lib)

    ar_exec = (
        f"يبلغ {ind_name_ar} في {country} حاليًا {_fmt(latest, unit)}، "
        f"مما يعكس مسارًا {'إيجابيًا' if improving else 'يستوجب الاهتمام'} خلال العقد الماضي. "
        f"تشير توقعات الذكاء الاصطناعي — باستخدام نموذج {model_name} (sMAPE: {model_smape:.1f}%) — "
        f"إلى أن هذا المؤشر سيتجه نحو أن {dir_ar} خلال الفترة القادمة ({horizon} فترة/فترات) "
        f"{confidence_ar}. "
        f"{'يتوافق ذلك مع أهداف إصلاحات ' + vision_ar + '.' if improving else 'يُنصح بالتدخل السياسي الهادف لعكس هذا المسار.'}"
    )

    fc_dir_ar = "تحسّنًا" if (fc_change < 0 and lib) or (fc_change > 0 and not lib) else "تراجعًا"
    yoy_dir_ar = "انخفض" if yoy < 0 else "ارتفع"
    yoy_signal_ar = "إيجابي" if (yoy < 0 and lib) or (yoy > 0 and not lib) else "سلبي"
    ar_insights = [
        f"{ind_name_ar} {yoy_dir_ar} بمقدار {abs(yoy):.1f} نقطة مئوية مقارنةً بالعام السابق — "
        f"وهو مؤشر {yoy_signal_ar}.",
        f"يتوقع النموذج ({model_name}) {fc_dir_ar} "
        f"بمقدار {abs(fc_change):.1f} نقطة مئوية ليصل المؤشر إلى {_fmt(fc_end, unit)} نهاية أفق التنبؤ.",
        f"يظل المحرك الهيكلي الرئيسي هو {strength_ar}.",
    ]
    if gcc_insight:
        better = (vs_gcc < 0 if lib else vs_gcc > 0) if vs_gcc is not None else False
        ar_insights.append(
            f"يُسجّل {country} أداءً {'أفضل' if better else 'أضعف'} من المتوسط الخليجي "
            f"({_fmt(gcc_avg_latest, unit)}) بفارق {abs(vs_gcc):.1f} نقطة مئوية."
            if vs_gcc is not None else ""
        )

    ar_risks = [
        "تحديات الاقتصاد العالمي (الضغوط التضخمية وتشديد الأوضاع المالية) قد تُبطئ التقدم المتوقع.",
        f"التحدي الهيكلي المتمثل في {challenge_ar} قد يُخفّف وتيرة التحسّن.",
        f"يُشير مؤشر دقة النموذج (sMAPE {model_smape:.1f}%) إلى مستوى مخاطرة "
        f"{'منخفض' if model_smape < 5 else 'معتدل' if model_smape < 12 else 'مرتفع'} — يُنصح بإجراء تحليل السيناريوهات.",
    ]

    ar_outlook = (
        f"استنادًا إلى نموذج {model_name}، تبدو آفاق {ind_name_ar} في {country} خلال {horizon} فترة قادمة "
        f"{'واعدةً بحذر' if improving else 'تحدّيًا يستوجب المعالجة'}. "
        f"يُتوقع أن يصل المؤشر إلى {_fmt(fc_end, unit)} "
        f"(فترة التنبؤ 80%: {_fmt(float(lower.iloc[-1]), unit)} – {_fmt(float(upper.iloc[-1]), unit)}). "
        f"{'استدامة زخم الإصلاح كفيلة بتحقيق مزيد من التحسّن الهيكلي.' if improving else 'دون تدخّل سياسي هادف، يُرجَّح استمرار هذا المسار — ويُنصح بالتحرّك الفوري.'}"
    )

    return IntelligenceReport(
        country=country,
        indicator=indicator,
        indicator_name=ind_name,
        unit=unit,
        executive_summary=exec_summary,
        key_insights=key_insights,
        risk_assessment=risks,
        influencing_factors=factors,
        policy_recommendations=recs_en,
        forecast_outlook=outlook,
        ar_executive_summary=ar_exec,
        ar_key_insights=ar_insights,
        ar_risk_assessment=ar_risks,
        ar_policy_recommendations=recs_ar,
        ar_forecast_outlook=ar_outlook,
        trend_label=trend_en,
        trend_label_ar=trend_ar,
        urgency_level=urgency,
        model_name=model_name,
        model_smape=model_smape,
    )


def format_arabic_executive_report(report: IntelligenceReport) -> str:
    """Produce a formatted Arabic executive report string for download."""
    lines = [
        "╔══════════════════════════════════════════════════════════════════╗",
        "║           منصة الذكاء الإحصائي الخليجي — تقرير تنفيذي           ║",
        "╚══════════════════════════════════════════════════════════════════╝",
        "",
        f"الدولة: {report.country}",
        f"المؤشر: {report.indicator_name}",
        f"النموذج المُختار: {report.model_name}  |  دقة التنبؤ (sMAPE): {report.model_smape:.1f}%",
        f"الاتجاه العام: {report.trend_label_ar}  |  مستوى الأولوية: {report.urgency_level}",
        "",
        "─" * 65,
        "أولاً: الملخص التنفيذي",
        "─" * 65,
        report.ar_executive_summary,
        "",
        "─" * 65,
        "ثانيًا: أبرز المؤشرات والرؤى",
        "─" * 65,
    ]
    for i, insight in enumerate(report.ar_key_insights, 1):
        lines.append(f"  {i}. {insight}")
    lines += [
        "",
        "─" * 65,
        "ثالثًا: تحليل المخاطر",
        "─" * 65,
    ]
    for risk in report.ar_risk_assessment:
        lines.append(f"  ⚠  {risk}")
    lines += [
        "",
        "─" * 65,
        "رابعًا: التوصيات الاستراتيجية",
        "─" * 65,
    ]
    for rec in report.ar_policy_recommendations:
        lines.append(f"  ✦  {rec}")
    lines += [
        "",
        "─" * 65,
        "خامسًا: النظرة المستقبلية",
        "─" * 65,
        report.ar_forecast_outlook,
        "",
        "═" * 65,
    ]
    return "\n".join(lines)

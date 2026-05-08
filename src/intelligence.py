"""
AI Decision Intelligence Engine.

Generates bilingual (English / Arabic) executive narratives, policy
recommendations, risk assessments, strategic alerts, and comparative
GCC intelligence from forecast data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RiskProfile:
    label: str           # Stable | Moderate Risk | High Risk | Recovery Phase |
                         # Structural Pressure | Growth Opportunity |
                         # Inflationary Pressure | Labor Market Volatility
    label_ar: str
    severity: str        # "low" | "medium" | "high" | "critical"
    confidence: str      # "High" | "Moderate" | "Low"
    badge_color: str     # CSS class suffix used in app.py
    rationale: str
    rationale_ar: str


@dataclass
class StrategicAlert:
    title: str
    title_ar: str
    message: str
    message_ar: str
    level: str           # "info" | "warning" | "critical" | "success"
    indicator: str
    country: str


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
    gcc_comparison: str
    causal_interpretation: str
    # Arabic
    ar_executive_summary: str
    ar_key_insights: List[str]
    ar_risk_assessment: List[str]
    ar_policy_recommendations: List[str]
    ar_forecast_outlook: str
    ar_gcc_comparison: str
    ar_causal_interpretation: str
    # Metadata
    trend_label: str        # "Improving" | "Worsening" | "Stable"
    trend_label_ar: str
    urgency_level: str      # "High" | "Medium" | "Low"
    model_name: str
    model_smape: float
    risk_profile: RiskProfile = field(default_factory=lambda: RiskProfile(
        "Stable", "مستقر", "low", "High", "stable", "", ""
    ))
    strategic_alerts: List[StrategicAlert] = field(default_factory=list)


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
        "causal_drivers_en": [
            "Nitaqat localisation quotas are gradually reshaping private-sector hiring patterns.",
            "Rapid expansion of tourism, entertainment, and digital sectors creates new youth employment channels.",
            "Vision 2030 capital projects support construction and infrastructure employment.",
        ],
        "causal_drivers_ar": [
            "تُعيد حصص التوطين (نطاقات) تدريجيًا تشكيل أنماط التوظيف في القطاع الخاص.",
            "التوسع السريع في السياحة والترفيه والقطاعات الرقمية يفتح قنوات توظيف جديدة للشباب.",
            "مشاريع رأس المال في رؤية 2030 تدعم توظيف قطاعي البناء والبنية التحتية.",
        ],
    },
    "UAE": {
        "vision": "UAE Centennial 2071",
        "strength": "world-class digital infrastructure and diversified economic base",
        "challenge": "maintaining competitiveness in attracting high-skilled national youth talent",
        "strength_ar": "البنية التحتية الرقمية العالمية والقاعدة الاقتصادية المتنوعة",
        "challenge_ar": "الحفاظ على التنافسية في استقطاب كفاءات الشباب المواطن",
        "causal_drivers_en": [
            "ADNOC and Mubadala investment mandates accelerate local talent pipelines.",
            "Dubai's position as a global fintech and startup hub creates high-value employment pathways.",
            "National AI and advanced technology strategies drive demand for skilled youth graduates.",
        ],
        "causal_drivers_ar": [
            "تفويضات الاستثمار لأدنوك ومبادلة تُسرّع مسارات المواهب المحلية.",
            "مكانة دبي مركزًا عالميًا للتكنولوجيا المالية والشركات الناشئة تُوجد مسارات توظيف عالية القيمة.",
            "استراتيجيات الذكاء الاصطناعي والتكنولوجيا المتقدمة الوطنية تُحرّك الطلب على خريجي الشباب المهرة.",
        ],
    },
    "Qatar": {
        "vision": "Qatar National Vision 2030",
        "strength": "strong sovereign wealth and post-2022 World Cup economic momentum",
        "challenge": "expanding private-sector youth employment beyond the oil and gas sector",
        "strength_ar": "الثروة السيادية الضخمة والزخم الاقتصادي في مرحلة ما بعد كأس العالم 2022",
        "challenge_ar": "توسيع توظيف الشباب في القطاع الخاص خارج نطاق قطاع النفط والغاز",
        "causal_drivers_en": [
            "World Cup 2022 infrastructure legacy creates sustained demand in hospitality and services.",
            "Qatar Investment Authority capital deployment supports economic diversification programmes.",
            "LNG expansion plans provide revenue underpinning employment-linked public spending.",
        ],
        "causal_drivers_ar": [
            "الإرث البنية التحتي لكأس العالم 2022 يُبقي الطلب مستمرًا في قطاعي الضيافة والخدمات.",
            "توظيف رأس مال جهاز قطر للاستثمار يدعم برامج التنويع الاقتصادي.",
            "خطط توسعة الغاز الطبيعي المسال توفر الإيرادات لدعم الإنفاق العام المرتبط بالتوظيف.",
        ],
    },
    "Kuwait": {
        "vision": "Kuwait Vision 2035",
        "strength": "significant hydrocarbon revenue providing fiscal space for reform",
        "challenge": "entrenched public-sector preference and slow private-sector development",
        "strength_ar": "عائدات النفط الضخمة التي توفر هامشًا ماليًا واسعًا للإصلاح",
        "challenge_ar": "الميل الراسخ نحو العمل الحكومي وبطء تطوير القطاع الخاص",
        "causal_drivers_en": [
            "Persistently high public-sector wage premium reduces incentives for private employment.",
            "Kuwait Vision 2035 New Kuwait initiatives target economic diversification but progress is gradual.",
            "Oil price cycles directly affect public spending capacity and public hiring volumes.",
        ],
        "causal_drivers_ar": [
            "علاوة الأجر الحكومي المرتفعة باستمرار تُقلّص الحوافز للعمل الخاص.",
            "مبادرات 'الكويت الجديدة' ضمن رؤية 2035 تستهدف التنويع الاقتصادي لكن التقدم تدريجي.",
            "دورات أسعار النفط تؤثر مباشرةً في طاقة الإنفاق العام وأحجام التوظيف الحكومي.",
        ],
    },
    "Bahrain": {
        "vision": "Bahrain Economic Vision 2030",
        "strength": "pioneering financial services sector and progressive labour market policies",
        "challenge": "limited natural resource base intensifying diversification urgency",
        "strength_ar": "ريادة قطاع الخدمات المالية وسياسات سوق العمل التقدمية",
        "challenge_ar": "محدودية الموارد الطبيعية مما يُعجّل الحاجة إلى التنويع الاقتصادي",
        "causal_drivers_en": [
            "Labour Market Regulatory Authority (LMRA) reforms are the most progressive in the GCC.",
            "Bahrain FinTech Bay and financial services cluster create high-quality graduate employment.",
            "Lower fiscal buffers relative to peers make youth employment highly sensitive to oil shocks.",
        ],
        "causal_drivers_ar": [
            "إصلاحات هيئة تنظيم سوق العمل هي الأكثر تقدمًا في منطقة الخليج.",
            "مبادرة البحرين للتكنولوجيا المالية وعنقود الخدمات المالية يوفران توظيفًا عالي الجودة للخريجين.",
            "انخفاض الاحتياطيات المالية مقارنةً بالدول المجاورة يجعل توظيف الشباب حساسًا لصدمات النفط.",
        ],
    },
    "Oman": {
        "vision": "Oman Vision 2040",
        "strength": "accelerating economic diversification across tourism, logistics, and manufacturing",
        "challenge": "higher youth population growth rate creating sustained labour market pressure",
        "strength_ar": "التنويع الاقتصادي المتسارع في السياحة والخدمات اللوجستية والصناعة",
        "challenge_ar": "المعدل المرتفع لنمو الشباب مما يولّد ضغطًا مستمرًا على سوق العمل",
        "causal_drivers_en": [
            "Oman Vision 2040 logistics and industrial clusters are creating structured graduate pathways.",
            "Port of Sohar and Duqm economic zone expansion drive engineering and technical employment.",
            "Higher youth population growth rate means labour market absorption must outpace cohort growth.",
        ],
        "causal_drivers_ar": [
            "عناقيد اللوجستيات والصناعة ضمن رؤية عُمان 2040 تُوجد مسارات منظمة للخريجين.",
            "توسّع ميناء صحار والمنطقة الاقتصادية الخاصة بالدقم يدفعان التوظيف الهندسي والتقني.",
            "المعدل المرتفع لنمو شريحة الشباب يعني أن قدرة سوق العمل على الاستيعاب يجب أن تتجاوز نمو الفئة.",
        ],
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
    "population_growth": {
        "improving": [
            "Align education and vocational training supply with demographic growth projections.",
            "Use growing youth cohorts as a competitive advantage through targeted skills development.",
            "Invest in labour market data systems that track demographic demand-supply dynamics.",
            "Build forward-looking workforce planning frameworks integrated with national vision targets.",
        ],
        "worsening": [
            "Review migration and residency policies affecting the active workforce composition.",
            "Invest in productivity-enhancing technology to offset declining labour force growth.",
            "Re-evaluate long-term workforce planning frameworks in light of demographic shifts.",
            "Develop incentive structures to maintain sustainable population growth rates.",
        ],
        "improving_ar": [
            "توافق إمدادات التعليم والتدريب المهني مع توقعات النمو الديموغرافي.",
            "توظيف فئات الشباب المتنامية ميزةً تنافسية من خلال تنمية المهارات الموجّهة.",
            "الاستثمار في أنظمة بيانات سوق العمل لرصد ديناميكيات العرض والطلب الديموغرافية.",
            "بناء أطر تخطيط استشرافي للقوى العاملة متكاملة مع أهداف الرؤية الوطنية.",
        ],
        "worsening_ar": [
            "مراجعة سياسات الهجرة والإقامة المؤثرة في تركيبة القوة العاملة النشطة.",
            "الاستثمار في تقنيات تعزيز الإنتاجية لتعويض تباطؤ نمو القوة العاملة.",
            "إعادة تقييم أُطر التخطيط للقوى العاملة على المدى البعيد في ضوء التحولات الديموغرافية.",
            "تطوير هياكل حوافز للحفاظ على معدلات نمو سكانية مستدامة.",
        ],
    },
    "internet_usage": {
        "improving": [
            "Leverage rising connectivity to scale digital skilling platforms for youth.",
            "Invest in cloud and AI infrastructure to capture value from growing digital participation.",
            "Support digital entrepreneurship programmes targeting online talent pools.",
            "Use broadband penetration gains to deliver remote employment opportunities.",
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
            "توظيف مكاسب انتشار النطاق العريض لتوفير فرص العمل عن بُعد.",
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
# Strategic Risk Engine
# ──────────────────────────────────────────────────────────────────────────────

def compute_risk_profile(
    indicator: str,
    latest: float,
    slope: float,
    improving: bool,
    uncertainty_pct: float,
    historical: pd.Series,
) -> RiskProfile:
    """
    Classify the current indicator situation into a dynamic risk label.
    Uses trend slope, recent volatility, target range adherence, and
    post-deterioration recovery patterns to assign a contextual label.
    """
    from src.gcc_data import INDICATORS
    lib = INDICATORS[indicator]["lower_is_better"]
    target_min, target_max = INDICATORS[indicator].get("target_range", (0, 100))

    # Volatility from recent percentage changes
    volatility = 0.0
    if len(historical) >= 4:
        pct_changes = historical.pct_change().dropna()
        volatility = float(pct_changes.std())

    # Recovery detection: early half worsening, late half improving
    is_recovery = False
    if len(historical) >= 6:
        vals = historical.values
        mid = len(vals) // 2
        early_slope = float(np.polyfit(np.arange(mid), vals[:mid], 1)[0])
        late_slope = float(np.polyfit(np.arange(len(vals) - mid), vals[mid:], 1)[0])
        early_worsening = (early_slope > 0 and lib) or (early_slope < 0 and not lib)
        late_improving = (late_slope < 0 and lib) or (late_slope > 0 and not lib)
        is_recovery = early_worsening and late_improving and improving

    in_target = target_min <= latest <= target_max

    # ── Indicator-specific overrides ─────────────────────────────────────────
    if indicator == "inflation":
        if latest > 5.0:
            return RiskProfile(
                label="Inflationary Pressure",
                label_ar="ضغط تضخمي",
                severity="high",
                confidence="High",
                badge_color="inflationary",
                rationale=(
                    f"Inflation at {latest:.1f}% substantially exceeds the 3% policy threshold, "
                    "posing direct risk to household purchasing power and real wage growth for youth workers."
                ),
                rationale_ar=(
                    f"يتجاوز معدل التضخم عند {latest:.1f}% الحد السياسي البالغ 3% بشكل ملحوظ، "
                    "مما يُشكّل خطرًا مباشرًا على القدرة الشرائية للأسر ونمو الأجور الحقيقية للعمال الشباب."
                ),
            )
        if latest > 3.0:
            return RiskProfile(
                label="Moderate Risk",
                label_ar="مخاطر معتدلة",
                severity="medium",
                confidence="High",
                badge_color="moderate-risk",
                rationale=f"Inflation at {latest:.1f}% is slightly above the 3% target. Continued monitoring is warranted.",
                rationale_ar=f"التضخم عند {latest:.1f}% يتجاوز الهدف البالغ 3% قليلاً. المراقبة المستمرة ضرورية.",
            )

    if indicator == "youth_unemployment_rate":
        if latest > 25.0:
            return RiskProfile(
                label="High Risk",
                label_ar="مخاطر عالية",
                severity="critical",
                confidence="High",
                badge_color="high-risk",
                rationale=(
                    f"Youth unemployment at {latest:.1f}% is critically elevated. "
                    "Structural intervention is required to prevent long-term labour market scarring effects."
                ),
                rationale_ar=(
                    f"بطالة الشباب عند {latest:.1f}% في مستوى حرج. "
                    "التدخل الهيكلي ضروري لمنع الآثار الندبية طويلة الأمد على سوق العمل."
                ),
            )
        if latest > 15.0 and not improving:
            return RiskProfile(
                label="Labor Market Volatility",
                label_ar="تقلبات سوق العمل",
                severity="high",
                confidence="Moderate",
                badge_color="labor-volatility",
                rationale=(
                    f"Youth unemployment at {latest:.1f}% with a worsening trend signals labour market instability. "
                    "Targeted policy response is required to prevent structural deterioration."
                ),
                rationale_ar=(
                    f"بطالة الشباب عند {latest:.1f}% مع اتجاه متراجع تُشير إلى عدم استقرار سوق العمل. "
                    "استجابة سياسية موجّهة مطلوبة لمنع التدهور الهيكلي."
                ),
            )

    # ── General pattern logic ─────────────────────────────────────────────────
    if is_recovery:
        return RiskProfile(
            label="Recovery Phase",
            label_ar="مرحلة التعافي",
            severity="medium",
            confidence="Moderate",
            badge_color="recovery",
            rationale=(
                "The indicator shows a recovery trajectory after a prior deterioration phase. "
                "Sustaining current policy direction and monitoring leading indicators is critical."
            ),
            rationale_ar=(
                "يُظهر المؤشر مسار تعافٍ بعد مرحلة تراجع سابقة. "
                "الحفاظ على التوجه السياسي الحالي ومراقبة المؤشرات الرائدة أمر محوري."
            ),
        )

    if improving and in_target:
        return RiskProfile(
            label="Stable",
            label_ar="مستقر",
            severity="low",
            confidence="High",
            badge_color="stable",
            rationale=(
                f"The indicator sits within the target range ({target_min}–{target_max}%) "
                "and is following an improving trajectory. The near-term risk outlook is low."
            ),
            rationale_ar=(
                f"يقع المؤشر ضمن النطاق المستهدف ({target_min}–{target_max}%) "
                "ويتبع مسارًا تحسّنيًا. مخاطر التوقعات على المدى القريب منخفضة."
            ),
        )

    if not lib and improving:
        return RiskProfile(
            label="Growth Opportunity",
            label_ar="فرصة نمو",
            severity="low",
            confidence="High",
            badge_color="growth-opportunity",
            rationale=(
                "A strong upward trajectory presents a growth opportunity. "
                "Sustained investment and policy alignment can amplify these gains further."
            ),
            rationale_ar=(
                "المسار التصاعدي القوي يُمثّل فرصة نمو واعدة. "
                "الاستثمار المستدام ومواءمة السياسات يُمكنهما تعزيز هذه المكاسب أكثر."
            ),
        )

    if not improving and abs(slope) > 0.3:
        return RiskProfile(
            label="Structural Pressure",
            label_ar="ضغط هيكلي",
            severity="high",
            confidence="High",
            badge_color="structural-pressure",
            rationale=(
                f"A persistent worsening trend (annualised slope: {slope:+.2f}pp) "
                "indicates deep-rooted structural pressure that short-term interventions alone cannot resolve."
            ),
            rationale_ar=(
                f"الاتجاه المتدهور المستمر (الميل السنوي: {slope:+.2f} نقطة) "
                "يُشير إلى ضغط هيكلي متجذّر لا يمكن لتدخلات قصيرة الأمد وحدها أن تحلّه."
            ),
        )

    if not improving:
        return RiskProfile(
            label="Moderate Risk",
            label_ar="مخاطر معتدلة",
            severity="medium",
            confidence="Moderate",
            badge_color="moderate-risk",
            rationale=(
                "The indicator is on a worsening trend. "
                "Without corrective policy action, further deterioration is expected."
            ),
            rationale_ar=(
                "المؤشر في اتجاه متراجع. "
                "دون تدخل سياسي تصحيحي، يُتوقع استمرار التدهور."
            ),
        )

    # Improving but outside target or elevated uncertainty
    if uncertainty_pct > 15:
        return RiskProfile(
            label="Moderate Risk",
            label_ar="مخاطر معتدلة",
            severity="medium",
            confidence="Low",
            badge_color="moderate-risk",
            rationale=(
                "Improving trend but elevated forecast uncertainty warrants cautious optimism. "
                "Scenario stress-testing is recommended before committing to policy design."
            ),
            rationale_ar=(
                "الاتجاه إيجابي لكن ارتفاع عدم اليقين في التوقعات يستدعي تفاؤلاً حذرًا. "
                "يُنصح باختبارات الإجهاد للسيناريوهات قبل الالتزام بتصميم السياسات."
            ),
        )

    return RiskProfile(
        label="Stable",
        label_ar="مستقر",
        severity="low",
        confidence="High",
        badge_color="stable",
        rationale="Trajectory is stable with manageable uncertainty levels. Continued monitoring is advised.",
        rationale_ar="المسار مستقر مع مستويات مقبولة من عدم اليقين. يُنصح بالمتابعة الدورية.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategic Alert Generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_strategic_alerts(
    country: str,
    indicator: str,
    latest: float,
    slope: float,
    improving: bool,
    risk_profile: RiskProfile,
    gcc_avg_latest: Optional[float] = None,
    yoy_change: float = 0.0,
) -> List[StrategicAlert]:
    """Generate a prioritised list of strategic alerts for the indicator/country."""
    from src.gcc_data import INDICATORS, COUNTRIES
    lib = INDICATORS[indicator]["lower_is_better"]
    ind_name = INDICATORS[indicator]["name"]
    ind_name_ar = INDICATORS[indicator].get("name_ar", ind_name)
    target_min, target_max = INDICATORS[indicator].get("target_range", (0, 100))
    flag = COUNTRIES[country]["flag"]

    alerts: List[StrategicAlert] = []

    # Alert 1: Critical risk level
    if risk_profile.severity == "critical":
        alerts.append(StrategicAlert(
            title=f"CRITICAL — {ind_name} Requires Immediate Policy Action",
            title_ar=f"حرج — {ind_name_ar} يستوجب تدخلاً سياسيًا فوريًا",
            message=(
                f"{flag} {country}'s {ind_name} stands at {latest:.1f}%, "
                f"classified as critical risk. {risk_profile.rationale}"
            ),
            message_ar=(
                f"{ind_name_ar} في {country} عند {latest:.1f}%، "
                f"مُصنَّف كخطر حرج. {risk_profile.rationale_ar}"
            ),
            level="critical",
            indicator=indicator,
            country=country,
        ))

    # Alert 2: Significant YoY movement
    abs_yoy = abs(yoy_change)
    if abs_yoy > 1.5:
        worsening_yoy = (yoy_change > 0 and lib) or (yoy_change < 0 and not lib)
        if worsening_yoy:
            direction_en = "accelerated deterioration"
            direction_ar = "تسارع في التدهور"
            alert_level = "warning"
        else:
            direction_en = "significant improvement"
            direction_ar = "تحسّن ملحوظ"
            alert_level = "success"
        alerts.append(StrategicAlert(
            title=f"YoY Signal: {direction_en.title()} ({abs_yoy:.1f}pp shift)",
            title_ar=f"إشارة سنوية: {direction_ar} ({abs_yoy:.1f} نقطة مئوية)",
            message=(
                f"The {ind_name} in {country} changed by {yoy_change:+.1f}pp year-on-year, "
                f"signalling {direction_en} that warrants close monitoring."
            ),
            message_ar=(
                f"تغيّر {ind_name_ar} في {country} بمقدار {yoy_change:+.1f} نقطة مئوية سنويًا، "
                f"مما يُشير إلى {direction_ar} يستوجب المتابعة الدقيقة."
            ),
            level=alert_level,
            indicator=indicator,
            country=country,
        ))

    # Alert 3: GCC peer divergence
    if gcc_avg_latest is not None:
        vs_gcc = latest - gcc_avg_latest
        worse_than_gcc = (vs_gcc > 0 and lib) or (vs_gcc < 0 and not lib)
        if abs(vs_gcc) > 2.5:
            if worse_than_gcc:
                alerts.append(StrategicAlert(
                    title=f"GCC Divergence — Underperforming Regional Peers by {abs(vs_gcc):.1f}pp",
                    title_ar=f"تباين خليجي — أداء دون النظراء الإقليميين بفارق {abs(vs_gcc):.1f} نقطة",
                    message=(
                        f"{country}'s {ind_name} ({latest:.1f}%) significantly underperforms "
                        f"the GCC average ({gcc_avg_latest:.1f}%). "
                        "Regional benchmarking reveals a structural gap. Peer-learning from top performers is recommended."
                    ),
                    message_ar=(
                        f"أداء {country} في {ind_name_ar} ({latest:.1f}%) يتخلف عن المتوسط الخليجي "
                        f"({gcc_avg_latest:.1f}%) بشكل ملحوظ. "
                        "التعلم من التجارب الرائدة في المنطقة موصى به."
                    ),
                    level="warning",
                    indicator=indicator,
                    country=country,
                ))
            else:
                alerts.append(StrategicAlert(
                    title=f"GCC Regional Leader — Outperforming Average by {abs(vs_gcc):.1f}pp",
                    title_ar=f"ريادة خليجية — تفوّق على المتوسط بفارق {abs(vs_gcc):.1f} نقطة",
                    message=(
                        f"{country}'s {ind_name} ({latest:.1f}%) outperforms the GCC average "
                        f"({gcc_avg_latest:.1f}%). "
                        "This leadership creates an opportunity to share policy models regionally and attract investment."
                    ),
                    message_ar=(
                        f"أداء {country} في {ind_name_ar} ({latest:.1f}%) يتفوق على المتوسط الخليجي "
                        f"({gcc_avg_latest:.1f}%). "
                        "هذه الريادة تُوفّر فرصة لمشاركة النماذج السياسية إقليميًا واستقطاب الاستثمارات."
                    ),
                    level="success",
                    indicator=indicator,
                    country=country,
                ))

    # Alert 4: Outside target range
    outside_target = (latest > target_max and lib) or (latest < target_min and not lib)
    if outside_target:
        alerts.append(StrategicAlert(
            title=f"Target Range Alert — Outside Optimal Band ({target_min}–{target_max}%)",
            title_ar=f"تنبيه النطاق المستهدف — خارج النطاق الأمثل ({target_min}–{target_max}%)",
            message=(
                f"{country}'s {ind_name} ({latest:.1f}%) is outside the optimal target range "
                f"of {target_min}–{target_max}%. Policy measures are needed to converge toward target."
            ),
            message_ar=(
                f"{ind_name_ar} في {country} ({latest:.1f}%) خارج النطاق الأمثل "
                f"({target_min}–{target_max}%). تدابير سياسية مطلوبة للتقريب من الهدف."
            ),
            level="warning",
            indicator=indicator,
            country=country,
        ))

    return alerts


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
    vs_gcc = (latest - gcc_avg_latest) if gcc_avg_latest is not None else None

    trend_en, trend_ar, improving = _slope_label(slope, lib)
    urgency = _urgency(latest, slope, lib)
    pol_key = "improving" if improving else "worsening"

    ctx = _COUNTRY_CONTEXT.get(country, {})
    pol = _INDICATOR_POLICY.get(indicator, {})
    recs_en = pol.get(pol_key, pol.get("improving", []))[:4]
    recs_ar = pol.get(f"{pol_key}_ar", pol.get("improving_ar", []))[:4]

    # ── Forecast confidence ───────────────────────────────────────────────────
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

    smape_risk = "low" if model_smape < 5 else ("moderate" if model_smape < 12 else "elevated")

    # ── Risk profile & alerts ─────────────────────────────────────────────────
    risk_profile = compute_risk_profile(
        indicator=indicator,
        latest=latest,
        slope=slope,
        improving=improving,
        uncertainty_pct=uncertainty_pct,
        historical=historical,
    )

    strategic_alerts = generate_strategic_alerts(
        country=country,
        indicator=indicator,
        latest=latest,
        slope=slope,
        improving=improving,
        risk_profile=risk_profile,
        gcc_avg_latest=gcc_avg_latest,
        yoy_change=yoy,
    )

    # ── English narrative ─────────────────────────────────────────────────────
    direction_phrase = _direction_word(fc_change, lib)
    trajectory_word = "positive" if improving else "concerning"
    vision_name = ctx.get("vision", "the national vision")
    country_strength = ctx.get("strength", "ongoing national reforms")
    country_challenge = ctx.get("challenge", "structural challenges")

    exec_summary = (
        f"{flag} {country}'s {ind_name} currently stands at {_fmt(latest, unit)}, "
        f"reflecting a {trajectory_word} trajectory over the observed period. "
        f"The {model_name} model (sMAPE: {model_smape:.1f}%) — selected via expanding-window "
        f"cross-validation — projects this indicator to {direction_phrase} "
        f"over the next {horizon} period(s) {confidence_phrase}. "
        f"Risk profile: {risk_profile.label}. "
        f"{'This improvement is broadly consistent with ' + vision_name + ' reform priorities.' if improving else 'Targeted policy intervention is recommended to arrest this trajectory.'}"
    )

    # GCC comparison section
    if vs_gcc is not None:
        better = (vs_gcc < 0 if lib else vs_gcc > 0)
        rel_word = "better" if better else "worse"
        gcc_comparison = (
            f"{country} performs {rel_word} than the GCC regional average "
            f"({_fmt(gcc_avg_latest, unit)}) by {abs(vs_gcc):.1f} percentage points, "
            f"ranking {'among the top performers' if better and abs(vs_gcc) > 3 else 'above regional average' if better else 'below regional average'} "
            f"in the GCC. "
        )
        if better and abs(vs_gcc) > 3:
            gcc_comparison += (
                f"This performance lead reflects {country_strength}. "
                "Maintaining this position requires sustained policy investment and reform continuity."
            )
        elif not better and abs(vs_gcc) > 3:
            gcc_comparison += (
                f"The gap against regional peers is driven primarily by {country_challenge}. "
                "Peer-learning from GCC leaders and adapting best-practice policy frameworks "
                "offers the most direct path to convergence."
            )
        else:
            gcc_comparison += (
                "The performance is broadly in line with regional peers. "
                "Incremental policy improvements offer scope for further differentiation."
            )
    else:
        gcc_comparison = (
            f"GCC comparative data not available for this configuration. "
            "Regional benchmarking is recommended as a supplementary analysis."
        )

    # Causal interpretation section
    causal_drivers = ctx.get("causal_drivers_en", [])
    if causal_drivers:
        causal_interpretation = (
            f"The observed trajectory in {country}'s {ind_name} is driven by a combination "
            f"of structural and cyclical factors. Key causal mechanisms include: "
            + " ".join(f"({i+1}) {d}" for i, d in enumerate(causal_drivers[:3]))
            + f" Statistical model diagnostics (sMAPE: {model_smape:.1f}%, risk: {smape_risk}) "
            f"suggest {'reliable signal with manageable uncertainty' if smape_risk == 'low' else 'moderate signal reliability — scenario analysis is advisable' if smape_risk == 'moderate' else 'elevated model uncertainty — results should be interpreted with caution'}."
        )
    else:
        causal_interpretation = (
            f"The trend in {country}'s {ind_name} reflects the interplay of national structural reforms, "
            f"regional economic conditions, and demographic dynamics. "
            f"The {model_name} model captures the primary autocorrelation patterns in the data. "
            f"Model reliability is {smape_risk} (sMAPE: {model_smape:.1f}%)."
        )

    yoy_dir = "declined" if yoy < 0 else "rose"
    yoy_signal = "positive" if (yoy < 0 and lib) or (yoy > 0 and not lib) else "negative"
    fc_dir = "improvement" if (fc_change < 0 and lib) or (fc_change > 0 and not lib) else "deterioration"
    key_insights = [
        f"The {ind_name} {yoy_dir} by {abs(yoy):.1f}pp year-on-year — a {yoy_signal} signal.",
        f"The {model_name} model projects a {abs(fc_change):.1f}pp {fc_dir}, "
        f"reaching {_fmt(fc_end, unit)} by end of the forecast horizon.",
    ]
    if vs_gcc is not None:
        better = (vs_gcc < 0 if lib else vs_gcc > 0)
        key_insights.append(
            f"{country} performs {'better' if better else 'worse'} than the GCC average "
            f"({_fmt(gcc_avg_latest, unit)}) by {abs(vs_gcc):.1f}pp."
        )
    key_insights.append(
        f"Primary structural driver: {country_strength}."
    )

    risks = [
        f"Global economic headwinds (inflationary pressure, financial tightening) "
        f"may slow projected progress, widening forecast uncertainty intervals.",
        f"Structural challenge: {country_challenge} could moderate improvement pace "
        f"even under favourable macro conditions.",
        f"Model forecast error (sMAPE {model_smape:.1f}%) indicates {smape_risk} statistical risk — "
        f"scenario sensitivity analysis is recommended.",
    ]
    if not improving:
        risks.insert(0,
            f"Trend risk: the {ind_name} has been on a worsening trajectory; "
            f"without intervention, this is expected to persist through the forecast horizon."
        )

    factors = [
        f"National economic strategy ({vision_name}) structural reforms.",
        "Digital economy and technology sector growth absorbing graduate talent.",
        "Global energy market conditions influencing fiscal space for employment programmes.",
        "Demographic dynamics — youth cohort size relative to labour market absorption capacity.",
        "Regional FDI inflows and private-sector investment confidence levels.",
    ]

    outlook = (
        f"Based on the {model_name} model, the {horizon}-period outlook for {country}'s {ind_name} is "
        f"{'cautiously optimistic' if improving else 'challenging and requires policy attention'}. "
        f"The indicator is forecast to reach {_fmt(fc_end, unit)} "
        f"(80% prediction interval: {_fmt(float(lower.iloc[-1]), unit)}–{_fmt(float(upper.iloc[-1]), unit)}). "
        f"{'If reform momentum is sustained, further structural improvement is achievable beyond the forecast horizon.' if improving else 'Without targeted policy action, the deteriorating trend is likely to persist — immediate evidence-based intervention is advisable.'}"
    )

    # ── Arabic narrative ──────────────────────────────────────────────────────
    ind_name_ar = ind_meta.get("name_ar", ind_name)
    vision_ar = ctx.get("vision", "الرؤية الوطنية")
    strength_ar = ctx.get("strength_ar", "الإصلاحات الوطنية الجارية")
    challenge_ar = ctx.get("challenge_ar", "التحديات الهيكلية")
    dir_ar = _direction_word_ar(fc_change, lib)

    ar_trajectory = "إيجابيًا" if improving else "يستوجب الاهتمام"
    ar_reform_note = (
        ("يتوافق ذلك مع أهداف إصلاحات " + vision_ar + ".")
        if improving
        else "يُنصح بالتدخل السياسي الهادف لعكس هذا المسار."
    )

    ar_exec = (
        f"يبلغ {ind_name_ar} في {country} حاليًا {_fmt(latest, unit)}، "
        f"مما يعكس مسارًا {ar_trajectory} خلال الفترة المرصودة. "
        f"تشير توقعات نموذج {model_name} (sMAPE: {model_smape:.1f}%) — "
        f"المُختار عبر التحقق المتقاطع بالنوافذ المتوسعة — "
        f"إلى أن هذا المؤشر سيتجه نحو أن {dir_ar} خلال {horizon} فترة قادمة "
        f"{confidence_ar}. "
        f"تصنيف المخاطر: {risk_profile.label_ar}. "
        f"{ar_reform_note}"
    )

    # Arabic GCC comparison
    if vs_gcc is not None:
        better_ar = (vs_gcc < 0 if lib else vs_gcc > 0)
        ar_rel = "أفضل" if better_ar else "أضعف"
        ar_gcc_comparison = (
            f"يُسجّل {country} أداءً {ar_rel} من المتوسط الإقليمي الخليجي "
            f"({_fmt(gcc_avg_latest, unit)}) بفارق {abs(vs_gcc):.1f} نقطة مئوية. "
        )
        if better_ar and abs(vs_gcc) > 3:
            ar_gcc_comparison += (
                f"يعكس هذا التفوق {strength_ar}. "
                "الحفاظ على هذه المكانة يستلزم استمرار الاستثمار السياسي وديمومة الإصلاح."
            )
        elif not better_ar and abs(vs_gcc) > 3:
            ar_gcc_comparison += (
                f"يُعزى الفارق عن النظراء الإقليميين أساسًا إلى {challenge_ar}. "
                "التعلم من التجارب الرائدة في الخليج وتكييف الأطر السياسية المثلى "
                "يُوفّران أقصر طريق للتقارب."
            )
        else:
            ar_gcc_comparison += (
                "الأداء يتوافق إجمالاً مع النظراء الإقليميين. "
                "التحسينات السياسية التدريجية تُتيح مجالاً للتميّز."
            )
    else:
        ar_gcc_comparison = "بيانات المقارنة الخليجية غير متاحة لهذا التكوين. تُنصح بالمعايرة الإقليمية كتحليل تكميلي."

    # Arabic causal interpretation
    causal_drivers_ar = ctx.get("causal_drivers_ar", [])
    if causal_drivers_ar:
        ar_causal = (
            f"يتشكّل المسار المرصود في {ind_name_ar} لدى {country} من مزيج العوامل الهيكلية والدورية. "
            "أبرز الآليات السببية: "
            + " ".join(f"({i+1}) {d}" for i, d in enumerate(causal_drivers_ar[:3]))
            + f" يُشير تشخيص النموذج الإحصائي (sMAPE: {model_smape:.1f}%) إلى "
            f"{'إشارة موثوقة مع عدم يقين قابل للإدارة' if smape_risk == 'low' else 'موثوقية إشارة معتدلة — يُنصح بتحليل السيناريوهات' if smape_risk == 'moderate' else 'عدم يقين مرتفع في النموذج — ينبغي تفسير النتائج بحذر'}."
        )
    else:
        ar_causal = (
            f"يعكس الاتجاه في {ind_name_ar} لدى {country} التفاعل بين الإصلاحات الهيكلية الوطنية "
            f"والأوضاع الاقتصادية الإقليمية والديناميكيات الديموغرافية. "
            f"يلتقط نموذج {model_name} الأنماط الرئيسية للارتباط الذاتي في البيانات. "
            f"موثوقية النموذج: {smape_risk} (sMAPE: {model_smape:.1f}%)."
        )

    fc_dir_ar = "تحسّنًا" if (fc_change < 0 and lib) or (fc_change > 0 and not lib) else "تراجعًا"
    yoy_dir_ar = "انخفض" if yoy < 0 else "ارتفع"
    yoy_signal_ar = "إيجابي" if (yoy < 0 and lib) or (yoy > 0 and not lib) else "سلبي"
    ar_insights = [
        f"{ind_name_ar} {yoy_dir_ar} بمقدار {abs(yoy):.1f} نقطة مئوية مقارنةً بالعام السابق — "
        f"وهو مؤشر {yoy_signal_ar}.",
        f"يتوقع نموذج {model_name} {fc_dir_ar} "
        f"بمقدار {abs(fc_change):.1f} نقطة ليصل المؤشر إلى {_fmt(fc_end, unit)} نهاية أفق التنبؤ.",
        f"المحرك الهيكلي الرئيسي: {strength_ar}.",
    ]
    if vs_gcc is not None:
        better_ar2 = (vs_gcc < 0 if lib else vs_gcc > 0)
        ar_insights.append(
            f"يُسجّل {country} أداءً {'أفضل' if better_ar2 else 'أضعف'} من المتوسط الخليجي "
            f"({_fmt(gcc_avg_latest, unit)}) بفارق {abs(vs_gcc):.1f} نقطة مئوية."
        )

    ar_risks = [
        "تحديات الاقتصاد العالمي (الضغوط التضخمية وتشديد الأوضاع المالية) قد تُبطئ التقدم المتوقع.",
        f"التحدي الهيكلي المتمثل في {challenge_ar} قد يُخفّف وتيرة التحسّن حتى في ظل ظروف اقتصادية مواتية.",
        f"دقة النموذج (sMAPE {model_smape:.1f}%) تُشير إلى مستوى مخاطرة "
        f"{'منخفض' if smape_risk == 'low' else 'معتدل' if smape_risk == 'moderate' else 'مرتفع'} — يُنصح بتحليل السيناريوهات.",
    ]
    if not improving:
        ar_risks.insert(0,
            f"مخاطر الاتجاه: {ind_name_ar} على مسار تراجعي؛ دون تدخل، يُتوقع استمرار ذلك عبر أفق التنبؤ."
        )

    ar_outlook = (
        f"استنادًا إلى نموذج {model_name}، تبدو آفاق {ind_name_ar} في {country} خلال {horizon} فترة قادمة "
        f"{'واعدةً بحذر' if improving else 'تحدّيًا يستوجب المعالجة'}. "
        f"يُتوقع أن يصل المؤشر إلى {_fmt(fc_end, unit)} "
        f"(فترة التنبؤ 80%: {_fmt(float(lower.iloc[-1]), unit)} – {_fmt(float(upper.iloc[-1]), unit)}). "
        f"{'استدامة زخم الإصلاح كفيلة بتحقيق تحسّن هيكلي إضافي ما وراء أفق التنبؤ.' if improving else 'دون تدخّل سياسي هادف قائم على الأدلة، يُرجَّح استمرار مسار التدهور — ويُنصح بالتحرّك الفوري.'}"
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
        gcc_comparison=gcc_comparison,
        causal_interpretation=causal_interpretation,
        ar_executive_summary=ar_exec,
        ar_key_insights=ar_insights,
        ar_risk_assessment=ar_risks,
        ar_policy_recommendations=recs_ar,
        ar_forecast_outlook=ar_outlook,
        ar_gcc_comparison=ar_gcc_comparison,
        ar_causal_interpretation=ar_causal,
        trend_label=trend_en,
        trend_label_ar=trend_ar,
        urgency_level=urgency,
        model_name=model_name,
        model_smape=model_smape,
        risk_profile=risk_profile,
        strategic_alerts=strategic_alerts,
    )


def format_arabic_executive_report(report: IntelligenceReport) -> str:
    """Produce a formatted Arabic executive report with structured ministry-grade sections."""
    lines = [
        "╔══════════════════════════════════════════════════════════════════╗",
        "║           منصة الذكاء الإحصائي الخليجي — تقرير تنفيذي           ║",
        "╚══════════════════════════════════════════════════════════════════╝",
        "",
        f"الدولة: {report.country}",
        f"المؤشر: {report.indicator_name}",
        f"النموذج المُختار: {report.model_name}  |  دقة التنبؤ (sMAPE): {report.model_smape:.1f}%",
        f"الاتجاه العام: {report.trend_label_ar}  |  مستوى الأولوية: {report.urgency_level}",
        f"تصنيف المخاطر: {report.risk_profile.label_ar}  |  مستوى الثقة: {report.risk_profile.confidence}",
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
        "رابعًا: العوامل السببية والمحركات الرئيسية",
        "─" * 65,
        report.ar_causal_interpretation,
        "",
        "─" * 65,
        "خامسًا: مقارنة خليجية",
        "─" * 65,
        report.ar_gcc_comparison,
        "",
        "─" * 65,
        "سادسًا: التوصيات الاستراتيجية",
        "─" * 65,
    ]
    for rec in report.ar_policy_recommendations:
        lines.append(f"  ✦  {rec}")
    lines += [
        "",
        "─" * 65,
        "سابعًا: النظرة المستقبلية والتوقعات",
        "─" * 65,
        report.ar_forecast_outlook,
        "",
        "─" * 65,
        "ثامنًا: التنبيهات الاستراتيجية",
        "─" * 65,
    ]
    if report.strategic_alerts:
        for alert in report.strategic_alerts:
            level_ar = {
                "critical": "حرج",
                "warning": "تحذير",
                "success": "إيجابي",
                "info": "معلومة",
            }.get(alert.level, alert.level)
            lines.append(f"  [{level_ar}] {alert.title_ar}")
            lines.append(f"         {alert.message_ar}")
            lines.append("")
    else:
        lines.append("  لا توجد تنبيهات استراتيجية نشطة.")
    lines += [
        "",
        "═" * 65,
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Priority 5 — Explainability & Trust Intelligence
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ConfidenceClassification:
    label: str          # "High Confidence" | "Moderate Confidence" | "Elevated Uncertainty" | "Volatile Outlook" | "Unstable Forecast"
    label_ar: str
    score: int          # 0–100
    color: str          # hex
    tier: str           # "A" | "B" | "C" | "D" | "E"
    explanation_en: str
    explanation_ar: str


@dataclass
class DriverInsight:
    rank: int
    feature_name: str
    label_en: str
    label_ar: str
    direction: str       # "positive" | "negative" | "neutral"
    direction_ar: str
    influence_pct: float
    explanation_en: str
    explanation_ar: str


# LightGBM feature name → (EN label, AR label, positive_means, explanation_en, explanation_ar)
_FEATURE_NARRATIVE: Dict[str, tuple] = {
    "lag_1":       ("Recent Historical Level",      "المستوى التاريخي الأخير",
                    True,
                    "The most recent observed value — strongest direct autocorrelation signal.",
                    "أحدث قيمة مرصودة — أقوى إشارة ارتباط ذاتي مباشر."),
    "lag_2":       ("2-Period Lag",                 "التأخر بفترتين",
                    True,
                    "Captures short-term momentum from two periods prior.",
                    "يلتقط الزخم قصير المدى من فترتين سابقتين."),
    "lag_3":       ("3-Period Lag",                 "التأخر بثلاث فترات",
                    True,
                    "Early echo of trend reversals from three periods back.",
                    "صدى مبكر لانعكاسات الاتجاه من ثلاث فترات سابقة."),
    "lag_6":       ("6-Period Memory",              "الذاكرة لست فترات",
                    True,
                    "Medium-term historical pattern — captures semi-annual cycles.",
                    "النمط التاريخي متوسط المدى — يلتقط الدورات نصف السنوية."),
    "lag_12":      ("12-Period Annual Memory",      "الذاكرة السنوية (12 فترة)",
                    True,
                    "Annual cycle memory — strongly predictive for annual frequency data.",
                    "ذاكرة الدورة السنوية — تنبؤية بقوة للبيانات السنوية التواتر."),
    "roll_mean_3": ("Short-Term Trend Momentum",    "زخم الاتجاه قصير المدى",
                    True,
                    "3-period rolling average — captures local trend acceleration or deceleration.",
                    "المتوسط المتحرك لـ3 فترات — يلتقط تسارع أو تباطؤ الاتجاه المحلي."),
    "roll_mean_6": ("Medium-Term Structural Trend", "الاتجاه الهيكلي متوسط المدى",
                    True,
                    "6-period rolling average — reflects sustained policy or macro-economic shifts.",
                    "المتوسط المتحرك لـ6 فترات — يعكس التحولات السياسية أو الاقتصادية الكلية المستدامة."),
    "roll_mean_12":("Long-Term Structural Signal",  "الإشارة الهيكلية طويلة المدى",
                    True,
                    "12-period rolling average — captures deep structural economic trends.",
                    "المتوسط المتحرك لـ12 فترة — يلتقط الاتجاهات الاقتصادية الهيكلية العميقة."),
    "roll_std_3":  ("Recent Volatility",            "التذبذب الأخير",
                    False,
                    "3-period rolling standard deviation — elevated values signal forecast instability.",
                    "الانحراف المعياري المتحرك لـ3 فترات — القيم المرتفعة تُشير إلى عدم استقرار التنبؤ."),
    "roll_std_6":  ("Medium-Term Volatility",       "التذبذب متوسط المدى",
                    False,
                    "6-period volatility — persistent instability dampens forecast confidence.",
                    "تذبذب الست فترات — عدم الاستقرار المستمر يُضعف ثقة التنبؤ."),
    "roll_std_12": ("Long-Term Stability Signal",   "إشارة الاستقرار طويلة المدى",
                    False,
                    "12-period volatility — high values indicate structural instability across economic cycles.",
                    "تذبذب 12 فترة — القيم المرتفعة تُشير إلى عدم استقرار هيكلي عبر الدورات الاقتصادية."),
    "year_idx":    ("Structural Time Trend",        "الاتجاه الزمني الهيكلي",
                    True,
                    "Long-run structural drift — captures transformational reform impacts over years.",
                    "الانجراف الهيكلي طويل الأمد — يلتقط آثار الإصلاحات التحولية عبر السنوات."),
    "month":       ("Seasonal Employment Cycle",    "الدورة الموسمية للتوظيف",
                    True,
                    "Intra-year seasonality — graduation cycles, fiscal-year hiring waves, and seasonal demand.",
                    "الموسمية داخل العام — دورات التخرج وموجات التوظيف السنوية والطلب الموسمي."),
    "quarter":     ("Quarterly Seasonal Pattern",   "النمط الموسمي الفصلي",
                    True,
                    "Quarterly cyclicality — fiscal quarter-driven hiring and policy implementation rhythms.",
                    "الدورية الفصلية — التوظيف المدفوع بالربع المالي وإيقاعات تنفيذ السياسات."),
}


def compute_confidence_classification(
    smape: float,
    interval_width_mean: float,
    volatility: float,
    horizon: int,
) -> ConfidenceClassification:
    """Compute a trust-oriented confidence classification from model and data quality signals."""
    score = 70

    # sMAPE contribution
    if smape < 5:
        score += 20
    elif smape < 12:
        score += 8
    elif smape < 20:
        score -= 8
    else:
        score -= 22

    # Horizon contribution (longer = more uncertain)
    if horizon <= 2:
        score += 10
    elif horizon <= 3:
        score += 3
    elif horizon <= 5:
        score -= 5
    else:
        score -= 12

    # Interval width contribution
    if interval_width_mean < 1.5:
        score += 8
    elif interval_width_mean < 3.0:
        score += 2
    elif interval_width_mean < 5.0:
        score -= 5
    else:
        score -= 12

    # Volatility contribution
    if volatility < 10:
        score += 5
    elif volatility < 20:
        pass
    else:
        score -= 8

    score = max(10, min(100, score))

    if score >= 85:
        label = "High Confidence"
        label_ar = "ثقة عالية"
        color = "#1A7A4A"
        tier = "A"
        explanation_en = (
            f"The model achieves strong predictive accuracy (sMAPE {smape:.1f}%) with a "
            f"{horizon}-period horizon and narrow prediction intervals. "
            "Forecasts are statistically robust and suitable for strategic planning."
        )
        explanation_ar = (
            f"يحقق النموذج دقة تنبؤية عالية (sMAPE {smape:.1f}%) بأفق {horizon} فترات "
            "وفترات تنبؤ ضيقة. التوقعات متينة إحصائيًا وملائمة للتخطيط الاستراتيجي."
        )
    elif score >= 70:
        label = "Moderate Confidence"
        label_ar = "ثقة معتدلة"
        color = "#1B4F72"
        tier = "B"
        explanation_en = (
            f"The model shows reliable performance (sMAPE {smape:.1f}%) with manageable "
            f"uncertainty across the {horizon}-period horizon. "
            "Results are directionally sound; scenario sensitivity analysis is recommended."
        )
        explanation_ar = (
            f"يُظهر النموذج أداءً موثوقًا (sMAPE {smape:.1f}%) مع عدم يقين قابل للإدارة "
            f"عبر أفق {horizon} فترات. النتائج سليمة اتجاهيًا؛ يُوصى بتحليل حساسية السيناريوهات."
        )
    elif score >= 55:
        label = "Elevated Uncertainty"
        label_ar = "شُحّ اليقين"
        color = "#C07820"
        tier = "C"
        explanation_en = (
            f"Forecast uncertainty is elevated (sMAPE {smape:.1f}%, horizon {horizon} periods). "
            "Directional trends remain informative, but point estimates carry meaningful uncertainty. "
            "Use alongside scenario simulation for robust planning."
        )
        explanation_ar = (
            f"عدم اليقين في التنبؤ مرتفع (sMAPE {smape:.1f}%، أفق {horizon} فترات). "
            "الاتجاهات لا تزال مفيدة، لكن التقديرات النقطية تحمل شكًا ذا معنى. "
            "يُستحسن استخدامها جنبًا إلى جنب مع محاكاة السيناريوهات."
        )
    elif score >= 40:
        label = "Volatile Outlook"
        label_ar = "توقعات متقلبة"
        color = "#A93226"
        tier = "D"
        explanation_en = (
            f"High model uncertainty (sMAPE {smape:.1f}%) and elevated data volatility "
            f"limit forecast reliability across the {horizon}-period horizon. "
            "Treat point forecasts as indicative only; scenario analysis is essential."
        )
        explanation_ar = (
            f"يُقيّد عدم يقين النموذج المرتفع (sMAPE {smape:.1f}%) والتذبذب الكبير في البيانات "
            f"موثوقية التنبؤ عبر أفق {horizon} فترات. "
            "اعتبر التنبؤات النقطية إرشادية فقط؛ تحليل السيناريوهات ضروري."
        )
    else:
        label = "Unstable Forecast"
        label_ar = "توقعات غير مستقرة"
        color = "#7B241C"
        tier = "E"
        explanation_en = (
            f"Forecast stability is low (sMAPE {smape:.1f}%, score {score}/100). "
            "The data series exhibits high structural volatility. "
            "Results should be treated with significant caution and validated against domain expertise."
        )
        explanation_ar = (
            f"استقرار التنبؤ منخفض (sMAPE {smape:.1f}%، نتيجة {score}/100). "
            "تُظهر السلسلة الزمنية تذبذبًا هيكليًا عاليًا. "
            "ينبغي التعامل مع النتائج بحذر بالغ والتحقق منها بخبرة القطاع."
        )

    return ConfidenceClassification(
        label=label, label_ar=label_ar, score=score, color=color,
        tier=tier, explanation_en=explanation_en, explanation_ar=explanation_ar,
    )


def interpret_feature_importance(
    feature_importances: "pd.Series",
    indicator: str,
    improving: bool,
) -> List[DriverInsight]:
    """
    Convert raw LightGBM feature importances into executive-readable driver insights.
    Returns top-8 drivers with directional interpretation and policy narrative.
    """
    total = feature_importances.sum()
    if total == 0:
        return []

    lib = True  # lower-is-better default; most indicators are lower-is-better
    try:
        from src.gcc_data import INDICATORS
        lib = INDICATORS.get(indicator, {}).get("lower_is_better", True)
    except Exception:
        pass

    insights: List[DriverInsight] = []
    for rank, (feat, imp) in enumerate(feature_importances.head(8).items(), start=1):
        pct = float(imp) / float(total) * 100
        narrative = _FEATURE_NARRATIVE.get(feat)

        if narrative:
            label_en, label_ar, pos_means, expl_en, expl_ar = narrative
        else:
            # Fallback for any lag not explicitly listed
            label_en = feat.replace("_", " ").title()
            label_ar = feat.replace("_", " ")
            pos_means = True
            expl_en = "Historical pattern feature contributing to model predictions."
            expl_ar = "ميزة النمط التاريخي المساهمة في تنبؤات النموذج."

        # Volatility/std features: high importance + worsening trend = negative signal
        is_vol = "std" in feat
        if is_vol:
            direction = "negative"
            direction_ar = "سلبي"
        else:
            # For most features: improving context = positive direction
            direction = "positive" if improving else "neutral"
            direction_ar = "إيجابي" if improving else "محايد"

        insights.append(DriverInsight(
            rank=rank,
            feature_name=feat,
            label_en=label_en,
            label_ar=label_ar,
            direction=direction,
            direction_ar=direction_ar,
            influence_pct=round(pct, 1),
            explanation_en=expl_en,
            explanation_ar=expl_ar,
        ))

    return insights


def compute_model_quality_tier(smape: float, model_name: str) -> Dict:
    """Return a human-readable model quality interpretation dict."""
    if smape < 5:
        tier = "Excellent"
        tier_ar = "ممتاز"
        color = "#1A7A4A"
        badge = "A+"
        rationale_en = (
            f"{model_name} achieved exceptional predictive accuracy (sMAPE {smape:.1f}%). "
            "This level of accuracy supports high-confidence strategic planning."
        )
        rationale_ar = (
            f"حقّق {model_name} دقة تنبؤية استثنائية (sMAPE {smape:.1f}%). "
            "هذا المستوى من الدقة يدعم التخطيط الاستراتيجي عالي الثقة."
        )
        stability = "High stability — forecasts are reliable across the projection horizon."
        stability_ar = "استقرار عالٍ — التوقعات موثوقة عبر أفق الإسقاط."
    elif smape < 12:
        tier = "Good"
        tier_ar = "جيد"
        color = "#1B4F72"
        badge = "B"
        rationale_en = (
            f"{model_name} demonstrates solid performance (sMAPE {smape:.1f}%). "
            "Forecasts are directionally reliable with manageable uncertainty bands."
        )
        rationale_ar = (
            f"يُظهر {model_name} أداءً متينًا (sMAPE {smape:.1f}%). "
            "التوقعات موثوقة اتجاهيًا مع فرق عدم يقين قابلة للإدارة."
        )
        stability = "Moderate stability — directional trends are reliable; point estimates carry some uncertainty."
        stability_ar = "استقرار معتدل — الاتجاهات موثوقة؛ التقديرات النقطية تحمل بعض الشك."
    elif smape < 25:
        tier = "Moderate"
        tier_ar = "معتدل"
        color = "#C07820"
        badge = "C"
        rationale_en = (
            f"{model_name} shows moderate accuracy (sMAPE {smape:.1f}%). "
            "This may reflect underlying data volatility or structural breaks. "
            "Use forecasts for directional guidance rather than precise point estimates."
        )
        rationale_ar = (
            f"يُظهر {model_name} دقة معتدلة (sMAPE {smape:.1f}%). "
            "قد يعكس ذلك تذبذبًا في البيانات أو تحولات هيكلية. "
            "استخدم التوقعات للتوجيه الاتجاهي لا للتقديرات النقطية الدقيقة."
        )
        stability = "Reduced stability — data volatility or structural breaks are limiting precision."
        stability_ar = "استقرار منخفض — تذبذب البيانات أو التحولات الهيكلية تُقيّد الدقة."
    else:
        tier = "Limited"
        tier_ar = "محدود"
        color = "#A93226"
        badge = "D"
        rationale_en = (
            f"{model_name} achieved limited accuracy (sMAPE {smape:.1f}%) on this dataset. "
            "High volatility or structural irregularities constrain model performance. "
            "Results should be interpreted with significant caution."
        )
        rationale_ar = (
            f"حقّق {model_name} دقة محدودة (sMAPE {smape:.1f}%) على هذه البيانات. "
            "يُقيّد التذبذب العالي أو الشذوذات الهيكلية أداء النموذج. "
            "ينبغي تفسير النتائج بحذر بالغ."
        )
        stability = "Low stability — treat outputs as indicative only; scenario analysis is essential."
        stability_ar = "استقرار منخفض — اعتبر النتائج إرشادية فقط؛ تحليل السيناريوهات ضروري."

    return {
        "tier": tier, "tier_ar": tier_ar, "color": color, "badge": badge,
        "rationale_en": rationale_en, "rationale_ar": rationale_ar,
        "stability_en": stability, "stability_ar": stability_ar,
    }

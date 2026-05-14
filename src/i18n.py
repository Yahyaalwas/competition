"""
Bilingual translations for the GCC Employment Intelligence Platform.
Supports English (EN) and Arabic (AR).
"""

TRANSLATIONS: dict[str, dict[str, str]] = {
    # Navigation
    "nav_overview":  {"EN": "🌍  GCC Overview",           "AR": "🌍  نظرة عامة على دول مجلس التعاون"},
    "nav_country":   {"EN": "🔍  Country Explorer",        "AR": "🔍  استكشاف الدول"},
    "nav_forecast":  {"EN": "📈  Forecast Center",         "AR": "📈  مركز التنبؤات"},
    "nav_insights":  {"EN": "🤖  AI Insights",             "AR": "🤖  رؤى الذكاء الاصطناعي"},
    "nav_scenario":  {"EN": "⚙️  Scenario Simulator",      "AR": "⚙️  محاكاة السيناريوهات"},
    "nav_explain":   {"EN": "🔬  Explainability",          "AR": "🔬  الشفافية والتفسير"},

    # Sidebar
    "app_title":         {"EN": "GCC Employment Intelligence",                      "AR": "ذكاء توظيف دول مجلس التعاون"},
    "app_badge":         {"EN": "AI POLICY ANALYTICS",                              "AR": "تحليلات السياسات بالذكاء الاصطناعي"},
    "demo_flow_title":   {"EN": "📋 Demo Flow",                                     "AR": "📋 مسار العرض التجريبي"},
    "demo_1":            {"EN": "1 · Regional overview &amp; KPIs",                 "AR": "1 · نظرة إقليمية ومؤشرات الأداء"},
    "demo_2":            {"EN": "2 · Country deep-dive",                            "AR": "2 · تحليل معمق للدولة"},
    "demo_3":            {"EN": "3 · Run AI forecast",                              "AR": "3 · تشغيل التنبؤ بالذكاء الاصطناعي"},
    "demo_4":            {"EN": "4 · Read AI intelligence",                         "AR": "4 · قراءة الرؤى الذكية"},
    "demo_5":            {"EN": "5 · Simulate scenarios",                           "AR": "5 · محاكاة السيناريوهات"},
    "demo_6":            {"EN": "6 · Review explainability",                        "AR": "6 · مراجعة الشفافية"},
    "btn_refresh":       {"EN": "🔄 Refresh Data",                                  "AR": "🔄 تحديث البيانات"},
    "data_source":       {"EN": "DATA SOURCE",                                      "AR": "مصدر البيانات"},
    "cache_live":        {"EN": "Cache: Live",                                      "AR": "البيانات: نشطة"},

    # Section headers
    "sec_latest_values":      {"EN": "Latest Values (2024)",                    "AR": "أحدث القيم (2024)"},
    "sec_country_rankings":   {"EN": "Country Rankings (2024)",                 "AR": "تصنيف الدول (2024)"},
    "sec_regional_summary":   {"EN": "Regional Performance Summary",            "AR": "ملخص الأداء الإقليمي"},
    "sec_yoy_heatmap":        {"EN": "Year-on-Year Change Heatmap",             "AR": "خريطة التغير السنوي"},
    "sec_ai_snapshot":        {"EN": "AI Regional Intelligence Snapshot",       "AR": "لقطة الذكاء الإقليمي"},
    "sec_historical_trend":   {"EN": "Historical Trend vs GCC Average",         "AR": "الاتجاه التاريخي مقارنة بمتوسط دول المجلس"},
    "sec_all_indicators":     {"EN": "All Indicators Snapshot",                 "AR": "لمحة عن جميع المؤشرات"},
    "sec_yoy_changes":        {"EN": "Year-on-Year Changes",                    "AR": "التغيرات السنوية"},
    "sec_ai_assessment":      {"EN": "AI Intelligence Assessment",              "AR": "التقييم الذكي"},
    "sec_results":            {"EN": "Results",                                 "AR": "النتائج"},
    "sec_strategic_alerts":   {"EN": "Strategic Alerts",                        "AR": "التنبيهات الاستراتيجية"},
    "sec_exec_summary":       {"EN": "Executive Summary",                       "AR": "الملخص التنفيذي"},
    "sec_key_insights":       {"EN": "Key Insights",                            "AR": "الرؤى الرئيسية"},
    "sec_gcc_intelligence":   {"EN": "Comparative GCC Intelligence",            "AR": "الذكاء المقارن لدول المجلس"},
    "sec_causal_driver":      {"EN": "Causal & Driver Interpretation",          "AR": "تفسير العوامل المحركة"},
    "sec_risk_assessment":    {"EN": "Risk Assessment",                         "AR": "تقييم المخاطر"},
    "sec_influencing":        {"EN": "Influencing Factors",                     "AR": "العوامل المؤثرة"},
    "sec_policy_recs":        {"EN": "Strategic Policy Recommendations",        "AR": "التوصيات السياسية الاستراتيجية"},
    "sec_forecast_outlook":   {"EN": "Forecast Outlook",                        "AR": "توقعات المستقبل"},
    "sec_scenario_presets":   {"EN": "Strategic Scenario Presets",              "AR": "سيناريوهات السياسات الاستراتيجية"},
    "sec_policy_levers":      {"EN": "Policy Levers",                           "AR": "أدوات السياسات"},
    "sec_baseline_vs_scenario": {"EN": "Baseline vs Scenario Forecast",         "AR": "التنبؤ الأساسي مقابل السيناريو"},
    "sec_driver_breakdown":   {"EN": "Driver Contribution Breakdown",           "AR": "تحليل مساهمة العوامل"},
    "sec_exec_scenario_report": {"EN": "Executive Scenario Intelligence Report", "AR": "تقرير السيناريو التنفيذي الذكي"},
    "sec_ai_transparency":    {"EN": "Responsible AI & Methodology",            "AR": "الذكاء الاصطناعي المسؤول والمنهجية"},
    "sec_model_quality":      {"EN": "Model Quality Assessment",                "AR": "تقييم جودة النموذج"},

    # KPI labels
    "kpi_latest":    {"EN": "Latest Value (2024)",      "AR": "أحدث قيمة (2024)"},
    "kpi_gcc_avg":   {"EN": "GCC Average (2024)",       "AR": "متوسط دول المجلس (2024)"},
    "kpi_cagr":      {"EN": "5-Year CAGR",              "AR": "معدل النمو السنوي المركب (5 سنوات)"},
    "kpi_rank":      {"EN": "GCC Rank (2024)",          "AR": "ترتيب في دول المجلس (2024)"},
    "kpi_improving": {"EN": "Improving",                "AR": "في تحسن"},
    "kpi_worsening": {"EN": "Worsening",                "AR": "في تراجع"},
    "kpi_best":      {"EN": "Best",                     "AR": "الأفضل"},
    "yoy_label":     {"EN": "YoY",                      "AR": "سنويًا"},

    # Form labels
    "lbl_select_indicator": {"EN": "Select Indicator",   "AR": "اختر المؤشر"},
    "lbl_country":          {"EN": "Country",            "AR": "الدولة"},
    "lbl_indicator":        {"EN": "Indicator",          "AR": "المؤشر"},
    "lbl_frequency":        {"EN": "Frequency",          "AR": "الترددية"},
    "lbl_horizon":          {"EN": "Forecast Horizon",   "AR": "أفق التنبؤ"},
    "lbl_confidence":       {"EN": "Confidence Level",   "AR": "مستوى الثقة"},
    "lbl_scenario":         {"EN": "Scenario",           "AR": "السيناريو"},

    # Buttons
    "btn_run_forecast":        {"EN": "▶ Run Demo Forecast",       "AR": "▶ تشغيل التنبؤ التجريبي"},
    "btn_reset":               {"EN": "↺ Reset to Baseline",       "AR": "↺ إعادة ضبط الخط الأساسي"},
    "btn_apply":               {"EN": "✓ Apply Scenario",          "AR": "✓ تطبيق السيناريو"},
    "btn_download_forecast":   {"EN": "⬇ Download Forecast CSV",   "AR": "⬇ تحميل بيانات التنبؤ"},
    "btn_download_brief":      {"EN": "⬇ Download Executive Brief", "AR": "⬇ تحميل الموجز التنفيذي"},
    "btn_download_report_en":  {"EN": "⬇ Download Report (EN)",    "AR": "⬇ تحميل التقرير (إنجليزي)"},
    "btn_download_report_ar":  {"EN": "⬇ Download Report (AR)",    "AR": "⬇ تحميل التقرير (عربي)"},

    # Tab labels
    "tab_english":         {"EN": "English",                 "AR": "الإنجليزية"},
    "tab_arabic":          {"EN": "Arabic (العربية)",        "AR": "العربية"},
    "tab_model_reliability": {"EN": "📊 Model Reliability",  "AR": "📊 موثوقية النموذج"},
    "tab_driver_intel":    {"EN": "🔍 Driver Intelligence",  "AR": "🔍 ذكاء العوامل"},
    "tab_forecast_conf":   {"EN": "📉 Forecast Confidence",  "AR": "📉 ثقة التنبؤ"},
    "tab_decomp":          {"EN": "📊 Decomposition",        "AR": "📊 التحليل التفكيكي"},
    "tab_ai_transparency": {"EN": "🛡️ AI Transparency",      "AR": "🛡️ شفافية الذكاء الاصطناعي"},

    # Stats bar
    "stat_nations":    {"EN": "GCC NATIONS",           "AR": "دول مجلس التعاون"},
    "stat_indicators": {"EN": "INDICATORS",            "AR": "المؤشرات"},
    "stat_years":      {"EN": "YEARS OF DATA",         "AR": "سنوات البيانات"},
    "stat_models":     {"EN": "AI MODELS",             "AR": "نماذج الذكاء الاصطناعي"},
    "stat_scenarios":  {"EN": "SCENARIOS",             "AR": "السيناريوهات"},
    "stat_languages":  {"EN": "LANGUAGES",             "AR": "اللغات"},

    # Table columns
    "col_country":  {"EN": "Country",        "AR": "الدولة"},
    "col_latest":   {"EN": "Latest (%)",     "AR": "أحدث قيمة (%)"},
    "col_yoy":      {"EN": "YoY Change",     "AR": "التغير السنوي"},
    "col_cagr":     {"EN": "5-Yr CAGR",      "AR": "معدل نمو 5 سنوات"},
    "col_vs_gcc":   {"EN": "vs GCC Avg",     "AR": "مقارنة بالمتوسط"},
    "col_trend":    {"EN": "Trend",          "AR": "الاتجاه"},
    "col_rank":     {"EN": "Rank",           "AR": "الترتيب"},

    # Page subtitles
    "overview_subtitle": {
        "EN": "AI-powered statistical intelligence for Gulf policy planning and youth labour market strategy",
        "AR": "ذكاء إحصائي مدعوم بالذكاء الاصطناعي لتخطيط السياسات الخليجية واستراتيجية سوق العمل للشباب",
    },
    "country_intro": {
        "EN": "Select a GCC nation for deep-dive historical analysis, all-indicators snapshot, and AI intelligence assessment.",
        "AR": "اختر دولة من دول مجلس التعاون لإجراء تحليل تاريخي معمق ونظرة شاملة على جميع المؤشرات.",
    },
    "forecast_intro": {
        "EN": "Model policy scenarios and simulate alternative futures",
        "AR": "نمذجة سيناريوهات السياسات ومحاكاة المستقبل البديل",
    },

    # Trend labels
    "trend_improving": {"EN": "Improving", "AR": "في تحسن"},
    "trend_worsening": {"EN": "Worsening", "AR": "في تراجع"},
    "trend_stable":    {"EN": "Stable",    "AR": "مستقر"},
}


def T(key: str, lang: str = "EN") -> str:
    """Return the translated string for *key* in *lang*, falling back to EN."""
    return TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS.get(key, {}).get("EN", key))


def is_ar(lang: str) -> bool:
    """Return True when the active language is Arabic."""
    return lang == "AR"

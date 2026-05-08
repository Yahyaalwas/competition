"""
GCC Youth Employment Intelligence Platform
==========================================
AI-powered statistical intelligence and decision-support platform
for forecasting youth employment trends across Gulf Cooperation Council nations.

Run with:  streamlit run app.py
"""

import copy
import io
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

from src import data as data_module
from src import evaluate as eval_module
from src import gcc_data
from src import intelligence as intel_module
from src import scenario as scenario_module
from src.models.baselines import NaiveModel, SeasonalNaiveModel, MovingAverageModel, DriftModel
from src.models.arima_model import ARIMAModel
from src.models.ml_model import LightGBMModel

# ──────────────────────────────────────────────────────────────────────────────
# Page config & theme
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GCC Youth Employment Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PRIMARY   = "#1B4F72"
_GOLD      = "#C39B4E"
_SUCCESS   = "#1A7A4A"
_WARNING   = "#C07820"
_DANGER    = "#A93226"
_LIGHT_BG  = "#F4F6F9"
_CARD_BG   = "#FFFFFF"

_COUNTRY_COLORS = {
    "Saudi Arabia": "#006C35",
    "UAE":          "#00732F",
    "Qatar":        "#8D1B3D",
    "Kuwait":       "#007A3D",
    "Bahrain":      "#CE1126",
    "Oman":         "#DB161B",
}

st.markdown(f"""
<style>
/* ══ Reset & global ══════════════════════════════════════════════════════════ */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(160deg, #EEF2F7 0%, #E8EDF4 60%, #EDF1F7 100%);
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #091320 0%, #0D2034 40%, #122A45 75%, #0D2034 100%);
    border-right: 1px solid rgba(195,155,78,0.18);
}}
[data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
[data-testid="stSidebar"] .stRadio > label {{ color: #D0DCE8 !important; font-size:0.85rem; }}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {{ color: #9EB5C8 !important; }}
div[data-testid="metric-container"] {{
    background: white; border-radius: 12px; padding: 14px;
    box-shadow: 0 3px 14px rgba(0,0,0,0.08);
}}
/* smooth all Streamlit elements */
*, *::before, *::after {{ transition: box-shadow 0.2s ease; }}

/* ══ Hero banner (Overview page) ════════════════════════════════════════════ */
.hero-banner {{
    background: linear-gradient(135deg, #091320 0%, #0D2A42 30%, #1B4F72 65%, #1A6392 100%);
    border-radius: 20px; padding: 2.6rem 3rem 1.8rem;
    color: white; margin-bottom: 2rem;
    box-shadow: 0 14px 52px rgba(9,19,32,0.42);
    position: relative; overflow: hidden;
    border: 1px solid rgba(195,155,78,0.22);
}}
.hero-banner::before {{
    content: '';
    position: absolute; top: -90px; right: -50px;
    width: 480px; height: 480px;
    background: radial-gradient(circle, rgba(195,155,78,0.13) 0%, transparent 65%);
    pointer-events: none;
}}
.hero-banner::after {{
    content: '';
    position: absolute; bottom: -70px; left: -40px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(41,128,185,0.18) 0%, transparent 60%);
    pointer-events: none;
}}
.hero-eyebrow {{
    display: inline-block;
    background: rgba(195,155,78,0.18); border: 1px solid rgba(195,155,78,0.45);
    color: #E8C96E; padding: 3px 14px; border-radius: 30px;
    font-size: 0.66rem; font-weight: 700; letter-spacing: 1.4px;
    text-transform: uppercase; margin-bottom: 0.9rem;
}}
.hero-title {{
    margin: 0; font-size: 2.1rem; font-weight: 900; letter-spacing: -0.8px;
    line-height: 1.15; text-shadow: 0 2px 20px rgba(0,0,0,0.25);
}}
.hero-subtitle {{ margin: 0.45rem 0 0.15rem; font-size: 1.0rem; opacity: 0.78; }}
.hero-mission {{ margin: 0.15rem 0 0; font-size: 0.82rem; opacity: 0.55; font-style: italic; }}
.hero-divider {{
    border: none; border-top: 1px solid rgba(255,255,255,0.12);
    margin: 1.5rem 0 1.2rem;
}}
.hero-stats {{
    display: flex; align-items: stretch; gap: 0;
    background: rgba(0,0,0,0.22); border-radius: 12px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}}
.hero-stat {{
    flex: 1; padding: 0.85rem 1.1rem; text-align: center;
    border-right: 1px solid rgba(255,255,255,0.08);
    transition: background 0.2s ease;
}}
.hero-stat:last-child {{ border-right: none; }}
.hero-stat:hover {{ background: rgba(255,255,255,0.06); }}
.hero-stat-val {{ font-size: 1.45rem; font-weight: 800; color: #E8C96E; line-height: 1; }}
.hero-stat-lbl {{
    font-size: 0.62rem; opacity: 0.58; text-transform: uppercase;
    letter-spacing: 0.7px; margin-top: 4px;
}}
.hero-stat-sub {{ font-size: 0.70rem; opacity: 0.72; margin-top: 2px; }}

/* ══ Page sub-banners ════════════════════════════════════════════════════════ */
.platform-banner {{
    background: linear-gradient(135deg, #1B4F72 0%, #2874A6 60%, #2980B9 100%);
    color: white; padding: 1.6rem 2rem; border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 6px 28px rgba(27,79,114,0.30);
    position: relative; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}}
.platform-banner::after {{
    content: '';
    position: absolute; right: -30px; top: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(195,155,78,0.18) 0%, transparent 70%);
    pointer-events: none;
}}
.platform-banner h1 {{ margin:0; font-size:1.65rem; font-weight:800; letter-spacing:-0.4px; }}
.platform-banner p  {{ margin:0.35rem 0 0; font-size:0.88rem; opacity:0.82; }}

/* ══ Section headers ═════════════════════════════════════════════════════════ */
.section-header {{
    border-left: 4px solid {_GOLD}; padding-left: 12px;
    margin: 2rem 0 1rem; color: {_PRIMARY}; font-weight: 800; font-size: 1.05rem;
    letter-spacing: -0.2px;
}}

/* ══ KPI cards ═══════════════════════════════════════════════════════════════ */
.kpi-card {{
    background: white; border-radius: 14px; padding: 1.3rem 1.1rem;
    box-shadow: 0 3px 16px rgba(0,0,0,0.075);
    text-align: center; position: relative; overflow: hidden;
    border: 1px solid rgba(27,79,114,0.065);
    transition: transform 0.22s cubic-bezier(.25,.46,.45,.94),
                box-shadow 0.22s ease;
}}
.kpi-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {_PRIMARY}, {_GOLD});
}}
.kpi-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 32px rgba(27,79,114,0.18);
    border-color: rgba(27,79,114,0.12);
}}
.kpi-val   {{ font-size: 1.9rem; font-weight: 800; color: {_PRIMARY}; line-height:1.1; }}
.kpi-label {{ font-size: 0.67rem; color: #888; text-transform: uppercase; letter-spacing:.7px; margin-top:5px; font-weight:600; }}
.kpi-delta {{ font-size: 0.82rem; margin-top:6px; font-weight:700; }}
.delta-good {{ color: {_SUCCESS}; }}
.delta-bad  {{ color: {_DANGER}; }}

/* ══ Insight cards ═══════════════════════════════════════════════════════════ */
.insight-card {{
    background: white; border-radius: 10px; padding: 1rem 1.2rem;
    margin: 0.45rem 0; box-shadow: 0 2px 12px rgba(0,0,0,0.065);
    border-left: 4px solid {_PRIMARY}; line-height: 1.65;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}}
.insight-card:hover {{
    transform: translateX(2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}}
.risk-card    {{ border-left-color: {_DANGER}; background: #FFFBFB; }}
.rec-card     {{ border-left-color: {_SUCCESS}; background: #FAFFFC; }}
.outlook-card {{ border-left-color: {_GOLD}; background: #FFFCF5; }}

/* ══ Executive cards ═════════════════════════════════════════════════════════ */
.exec-card {{
    background: linear-gradient(135deg, #ffffff 0%, #F8FAFD 100%);
    border-radius: 14px; padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(27,79,114,0.09);
    border: 1px solid rgba(27,79,114,0.07);
    margin: 0.5rem 0; line-height: 1.65;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}}
.exec-card:hover {{ box-shadow: 0 8px 30px rgba(27,79,114,0.15); transform: translateY(-2px); }}
.exec-card-eyebrow {{
    font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.9px;
    color: {_GOLD}; font-weight: 700; margin-bottom: 0.45rem;
}}

/* ══ Arabic block ════════════════════════════════════════════════════════════ */
.arabic-block {{
    direction: rtl; text-align: right;
    font-family: 'Amiri', 'Traditional Arabic', 'Arial', sans-serif;
    line-height: 2.1; font-size: 1.0rem;
    background: white; border-radius: 10px; padding: 1.3rem 1.6rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.065); margin: 0.5rem 0;
    border-right: 4px solid {_GOLD};
    transition: box-shadow 0.2s ease;
}}
.arabic-block:hover {{ box-shadow: 0 5px 22px rgba(0,0,0,0.1); }}

/* ══ Badge system ════════════════════════════════════════════════════════════ */
.badge {{
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: .3px;
    margin: 2px; border: 1px solid transparent;
}}
.badge-improving          {{ background:#D5F5E3; color:{_SUCCESS};  border-color:{_SUCCESS}; }}
.badge-worsening          {{ background:#FADBD8; color:{_DANGER};   border-color:{_DANGER}; }}
.badge-stable             {{ background:#EAF2FF; color:{_PRIMARY};  border-color:{_PRIMARY}; }}
.badge-high               {{ background:#FADBD8; color:{_DANGER};   border-color:{_DANGER}; }}
.badge-medium             {{ background:#FDEBD0; color:{_WARNING};  border-color:{_WARNING}; }}
.badge-low                {{ background:#D5F5E3; color:{_SUCCESS};  border-color:{_SUCCESS}; }}
.badge-high-risk          {{ background:#FADBD8; color:{_DANGER};   border-color:{_DANGER}; }}
.badge-moderate-risk      {{ background:#FDEBD0; color:{_WARNING};  border-color:{_WARNING}; }}
.badge-recovery           {{ background:#E8F8F5; color:#148F77;     border-color:#148F77; }}
.badge-structural-pressure{{ background:#FDFEFE; color:#7B241C;     border-color:#7B241C; }}
.badge-growth-opportunity {{ background:#EAFAF1; color:{_SUCCESS};  border-color:{_SUCCESS}; }}
.badge-inflationary       {{ background:#FEF9E7; color:#9A7D0A;     border-color:#9A7D0A; }}
.badge-labor-volatility   {{ background:#F5EEF8; color:#6C3483;     border-color:#6C3483; }}

/* ══ Alert cards ═════════════════════════════════════════════════════════════ */
.alert-card {{
    border-radius: 10px; padding: 0.9rem 1.2rem; margin: 0.4rem 0;
    font-size: 0.88rem; border-left: 5px solid;
    transition: transform 0.15s ease;
}}
.alert-card:hover {{ transform: translateX(3px); }}
.alert-critical {{ background: #FDEDEC; border-color: {_DANGER}; }}
.alert-warning  {{ background: #FEF9E7; border-color: {_WARNING}; }}
.alert-success  {{ background: #EAFAF1; border-color: {_SUCCESS}; }}
.alert-info     {{ background: #EAF2FF; border-color: {_PRIMARY}; }}
.alert-title    {{ font-weight: 700; font-size: 0.86rem; margin-bottom: 4px; }}
.alert-msg      {{ font-size: 0.82rem; opacity: 0.9; line-height: 1.5; }}

/* ══ Risk panels ═════════════════════════════════════════════════════════════ */
.risk-panel {{
    background: white; border-radius: 12px; padding: 1.1rem 1.4rem;
    box-shadow: 0 3px 16px rgba(0,0,0,0.08); margin-bottom: 1rem;
    border-top: 4px solid {_DANGER};
    transition: box-shadow 0.2s ease;
}}
.risk-panel:hover {{ box-shadow: 0 6px 26px rgba(0,0,0,0.13); }}
.risk-label {{ font-size: 1.0rem; font-weight: 800; margin-bottom: 4px; }}
.risk-rationale {{ font-size: 0.82rem; color: #555; line-height: 1.56; }}

/* ══ Country intel cards (AI Overview row) ═══════════════════════════════════ */
.country-intel-card {{
    background: white; border-radius: 12px; padding: 0.75rem 0.65rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); text-align: center;
    border-top: 3px solid {_PRIMARY};
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid rgba(27,79,114,0.06);
}}
.country-intel-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 26px rgba(27,79,114,0.15);
}}

/* ══ Data source strip ═══════════════════════════════════════════════════════ */
.data-source-strip {{
    background: rgba(27,79,114,0.055); border-radius: 8px;
    padding: 0.4rem 0.9rem; font-size: 0.72rem; color: #666;
    border-left: 3px solid {_GOLD}; margin-bottom: 1rem;
}}

/* ══ Intelligence highlight strip ═══════════════════════════════════════════ */
.intel-highlight {{
    background: linear-gradient(135deg, {_PRIMARY} 0%, #2980B9 100%);
    border-radius: 10px; padding: 0.8rem 1.2rem;
    color: white; margin: 0.3rem 0; font-size: 0.85rem; line-height: 1.5;
    box-shadow: 0 3px 14px rgba(27,79,114,0.28);
}}

/* ══ Custom scrollbar ════════════════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: #EEF2F7; }}
::-webkit-scrollbar-thumb {{ background: #B8CCE0; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {_PRIMARY}; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0.5rem 1.6rem;">
        <div style="font-size:2.8rem; line-height:1; margin-bottom:0.5rem;">🌍</div>
        <div style="font-weight:800; font-size:0.95rem; letter-spacing:-0.2px;
                    line-height:1.3; margin-bottom:3px;">
            GCC Employment Intelligence
        </div>
        <div style="display:inline-block; background:rgba(195,155,78,0.2);
                    border:1px solid rgba(195,155,78,0.4); color:#E8C96E;
                    padding:2px 10px; border-radius:20px;
                    font-size:0.60rem; font-weight:700; letter-spacing:1.0px;
                    text-transform:uppercase; margin-top:4px;">
            AI POLICY ANALYTICS
        </div>
    </div>
    """, unsafe_allow_html=True)

    PAGE = st.radio(
        "Navigation",
        [
            "🌍  GCC Overview",
            "🔍  Country Explorer",
            "📈  Forecast Center",
            "🤖  AI Insights",
            "⚙️  Scenario Simulator",
            "🔬  Explainability",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("---")

    # ── Data source & refresh ─────────────────────────────────────────────────
    from src.wb_data import get_metadata, is_cache_available
    meta = get_metadata()
    last_updated = meta.get("last_updated", "Not yet fetched")
    cache_ok = is_cache_available()

    cache_icon = "🟢" if cache_ok else "🔴"
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.07); border-radius:8px; '
        f'padding:0.7rem 0.9rem; font-size:0.71rem; line-height:1.65; '
        f'border-left:2px solid rgba(195,155,78,0.4);">'
        f'<div style="font-weight:700; font-size:0.68rem; text-transform:uppercase; '
        f'letter-spacing:0.6px; opacity:0.7; margin-bottom:4px;">Data Source</div>'
        f'World Bank Open Data API v2<br>'
        f'{cache_icon} Cache: {"Live" if cache_ok else "Not available"}<br>'
        f'<span style="opacity:0.65;">Updated: {last_updated}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True, help="Re-fetch all indicators from World Bank API"):
        with st.spinner("Fetching data from World Bank Open Data…"):
            try:
                gcc_data.refresh(force=True)
                for k in list(st.session_state.keys()):
                    if k in ("fc_results", "fc_meta"):
                        del st.session_state[k]
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")

    if not cache_ok:
        st.warning("⚠ No local cache. Click **Refresh Data** to fetch from World Bank.", icon="⚠️")

    st.markdown(
        '<div style="font-size:0.62rem; opacity:0.38; padding-top:0.9rem; text-align:center;">'
        '© 2025 GCC Statistical Intelligence Platform<br>'
        'Powered by World Bank Open Data'
        '</div>',
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _plotly_base(title: str = "") -> go.Layout:
    return go.Layout(
        title=dict(text=title, font=dict(size=14, color=_PRIMARY, family="sans-serif"), x=0),
        template="plotly_white",
        font=dict(family="sans-serif", size=12),
        margin=dict(l=50, r=20, t=50 if title else 20, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )


def _line_fig(
    series_dict: dict,
    title: str = "",
    yaxis_title: str = "Value",
    show_points: bool = False,
) -> go.Figure:
    fig = go.Figure(layout=_plotly_base(title))
    for name, s in series_dict.items():
        color = _COUNTRY_COLORS.get(name, _PRIMARY)
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values,
            name=name, line=dict(color=color, width=2.2),
            mode="lines+markers" if show_points else "lines",
            marker=dict(size=5, color=color) if show_points else dict(),
        ))
    fig.update_layout(yaxis_title=yaxis_title, hovermode="x unified")
    return fig


def _get_models(freq: str = "Y") -> list:
    seasonal_period = 12 if freq == "M" else 1
    return [
        NaiveModel(),
        SeasonalNaiveModel(period=seasonal_period),
        MovingAverageModel(window=3),
        DriftModel(),
        ARIMAModel(auto_order=True, max_p=2, max_d=2, max_q=2,
                   max_P=1, max_D=1, max_Q=1,
                   seasonal_period=seasonal_period, use_seasonal=(freq == "M"), freq=freq),
        LightGBMModel(n_lags=3 if freq == "Y" else 12,
                      rolling_windows=[2, 3] if freq == "Y" else [3, 6, 12],
                      n_estimators=80, freq=freq),
    ]


@st.cache_data(show_spinner=False)
def _run_forecast(country: str, indicator: str, freq: str, horizon: int, alpha: float):
    """Cache forecast results by (country, indicator, freq, horizon, alpha)."""
    if freq == "M":
        y = gcc_data.get_monthly_series(country, indicator)
    else:
        y = gcc_data.get_series(country, indicator)

    df = pd.DataFrame({"value": y})
    df = data_module.clean_data(df, "value", "interpolate")

    models = _get_models(freq)
    min_train = 24 if freq == "M" else 6
    n_folds = max(1, min(3, (len(df) - min_train) // max(horizon, 1)))

    backtest = eval_module.backtest_all_models(
        models=models, df=df, value_column="value",
        horizon=horizon, n_folds=n_folds, min_train_size=min_train, alpha=alpha,
    )
    best_model = copy.deepcopy(next(m for m in models if m.name == backtest.best_model_name))
    best_model.fit(y)
    fc, lo, hi = best_model.predict_interval(horizon=horizon, alpha=alpha)
    return y, fc, lo, hi, backtest, best_model


def _kpi_card(label: str, value: str, delta: str = "", good: bool = True) -> str:
    delta_cls = "delta-good" if good else "delta-bad"
    delta_html = f'<div class="kpi-delta {delta_cls}">{delta}</div>' if delta else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-val">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'{delta_html}'
        f'</div>'
    )


def _insight_html(text: str, kind: str = "insight") -> str:
    cls = {"risk": "risk-card", "rec": "rec-card", "outlook": "outlook-card"}.get(kind, "insight-card")
    icon = {"risk": "⚠️", "rec": "✦", "outlook": "🔭"}.get(kind, "•")
    return f'<div class="insight-card {cls}">{icon} {text}</div>'


def _exec_card(eyebrow: str, body: str) -> str:
    """Premium executive insight card with gold eyebrow label."""
    return (
        f'<div class="exec-card">'
        f'<div class="exec-card-eyebrow">{eyebrow}</div>'
        f'{body}'
        f'</div>'
    )


def _badge(text: str, kind: str) -> str:
    cls = f"badge-{kind.lower().replace(' ', '-')}"
    return f'<span class="badge {cls}">{text}</span>'


def _alert_card(title: str, message: str, level: str = "info") -> str:
    icons = {"critical": "🚨", "warning": "⚠️", "success": "✅", "info": "ℹ️"}
    icon = icons.get(level, "•")
    return (
        f'<div class="alert-card alert-{level}">'
        f'<div class="alert-title">{icon} {title}</div>'
        f'<div class="alert-msg">{message}</div>'
        f'</div>'
    )


def _risk_panel(label: str, severity: str, confidence: str, rationale: str) -> str:
    colors = {
        "low": "#1A7A4A",
        "medium": "#C07820",
        "high": "#A93226",
        "critical": "#7B241C",
    }
    color = colors.get(severity, "#1B4F72")
    return (
        f'<div class="risk-panel" style="border-top-color:{color};">'
        f'<div class="risk-label" style="color:{color};">{label}</div>'
        f'<div style="font-size:0.75rem;color:#888;margin-bottom:6px;">'
        f'Severity: {severity.title()} &nbsp;|&nbsp; Forecast Confidence: {confidence}'
        f'</div>'
        f'<div class="risk-rationale">{rationale}</div>'
        f'</div>'
    )


def _banner(title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div class="platform-banner">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>""", unsafe_allow_html=True)


def _section(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 1 – GCC Overview
# ──────────────────────────────────────────────────────────────────────────────

def page_gcc_overview():
    from src.wb_data import get_metadata, is_cache_available
    wb_meta = get_metadata()
    src_label  = wb_meta.get("source", "World Bank Open Data")
    src_url    = wb_meta.get("source_url", "https://data.worldbank.org")
    updated_at = wb_meta.get("last_updated", "—")

    if not is_cache_available():
        _banner(
            "🌍 GCC Youth Employment Intelligence Hub",
            "Regional comparative analysis · Six-country dashboard · 2010–2024",
        )
        st.warning(
            "⚠ Local data cache not found. Use the **🔄 Refresh Data** button in the sidebar "
            "to fetch real data from World Bank Open Data.",
            icon="⚠️",
        )
        return

    # ── Compute hero stats (youth unemployment — flagship indicator) ──────────
    _hero_ind = "youth_unemployment_rate"
    _hero_stats = {c: gcc_data.get_trend_stats(c, _hero_ind) for c in gcc_data.COUNTRIES}
    _gcc_avg_unem = sum(s["latest"] for s in _hero_stats.values()) / len(_hero_stats)
    _best_country = min(_hero_stats, key=lambda c: _hero_stats[c]["latest"])
    _worst_country = max(_hero_stats, key=lambda c: _hero_stats[c]["latest"])
    _n_improving = sum(1 for s in _hero_stats.values() if s["improving"])
    _best_flag = gcc_data.COUNTRIES[_best_country]["flag"]

    hero_stats_html = (
        f'<div class="hero-stats">'
        f'<div class="hero-stat">'
        f'  <div class="hero-stat-val">{_gcc_avg_unem:.1f}%</div>'
        f'  <div class="hero-stat-lbl">GCC Avg Unemployment</div>'
        f'  <div class="hero-stat-sub">Youth (15–24)</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'  <div class="hero-stat-val">{_best_flag} {_hero_stats[_best_country]["latest"]:.1f}%</div>'
        f'  <div class="hero-stat-lbl">Best Performer</div>'
        f'  <div class="hero-stat-sub">{_best_country}</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'  <div class="hero-stat-val">{_n_improving}/6</div>'
        f'  <div class="hero-stat-lbl">Countries Improving</div>'
        f'  <div class="hero-stat-sub">Youth unemployment</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'  <div class="hero-stat-val">{_hero_stats[_worst_country]["latest"]:.1f}%</div>'
        f'  <div class="hero-stat-lbl">Highest Rate</div>'
        f'  <div class="hero-stat-sub">{_worst_country}</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'  <div class="hero-stat-val">5</div>'
        f'  <div class="hero-stat-lbl">Indicators Tracked</div>'
        f'  <div class="hero-stat-sub">WB Open Data</div>'
        f'</div>'
        f'</div>'
    )

    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-eyebrow">GCC STRATEGIC INTELLIGENCE PLATFORM</div>
        <h1 class="hero-title">🌍 GCC Youth Employment Intelligence Hub</h1>
        <p class="hero-subtitle">
            AI-powered statistical intelligence for Gulf policy planning and youth labour market strategy
        </p>
        <p class="hero-mission">
            Six GCC nations · Five World Bank indicators · 2010–2024 · {src_label} · Updated: {updated_at}
        </p>
        <hr class="hero-divider">
        {hero_stats_html}
    </div>
    """, unsafe_allow_html=True)

    ind = st.selectbox(
        "Select Indicator",
        list(gcc_data.INDICATORS.keys()),
        format_func=lambda k: gcc_data.INDICATORS[k]["name"],
        key="overview_ind",
    )
    meta = gcc_data.INDICATORS[ind]
    lib = meta["lower_is_better"]

    # ── KPI cards ────────────────────────────────────────────────────────────
    _section("Latest Values (2024)")
    stats = {c: gcc_data.get_trend_stats(c, ind) for c in gcc_data.COUNTRIES}
    cols = st.columns(6)
    for i, (country, info) in enumerate(gcc_data.COUNTRIES.items()):
        s = stats[country]
        yoy = s["yoy_change"]
        good = (yoy < 0) if lib else (yoy > 0)
        arrow = "↓" if yoy < 0 else "↑"
        delta = f"{arrow} {abs(yoy):.1f}pp YoY"
        cols[i].markdown(
            _kpi_card(f"{info['flag']} {country}", f"{s['latest']:.1f}%", delta, good),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Trend chart ──────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        _section(f"Trend: {meta['name']} (2015–2024)")
        df_all = gcc_data.get_all_countries_df(ind)
        gcc_avg = gcc_data.get_gcc_average(ind)

        fig = go.Figure(layout=_plotly_base())
        for country in gcc_data.COUNTRIES:
            clr = _COUNTRY_COLORS[country]
            fig.add_trace(go.Scatter(
                x=df_all.index, y=df_all[country],
                name=country, line=dict(color=clr, width=2),
                mode="lines+markers", marker=dict(size=5),
            ))
        fig.add_trace(go.Scatter(
            x=gcc_avg.index, y=gcc_avg.values,
            name="GCC Average", line=dict(color=_GOLD, width=2.5, dash="dash"),
            mode="lines",
        ))
        fig.update_layout(
            yaxis_title=f"{meta['name']} ({meta['unit']})",
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.15, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        _section("Country Rankings (2024)")
        rankings = gcc_data.get_rankings(ind)
        fig2 = go.Figure(layout=_plotly_base())
        bar_colors = [_COUNTRY_COLORS[c] for c in rankings["country"]]
        fig2.add_trace(go.Bar(
            x=rankings["value"], y=rankings["flag"] + " " + rankings["country"],
            orientation="h", marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in rankings["value"]],
            textposition="outside",
        ))
        fig2.update_layout(
            xaxis_title=meta["unit"],
            yaxis=dict(autorange="reversed"),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Regional summary table ────────────────────────────────────────────────
    _section("Regional Performance Summary")
    summary_rows = []
    for country, info in gcc_data.COUNTRIES.items():
        s = stats[country]
        trend_en, _, improving = (
            ("Improving", "", True) if s["improving"] else
            ("Stable", "", False) if abs(s["slope"]) < 0.05 else
            ("Worsening", "", False)
        )
        summary_rows.append({
            "Country": f"{info['flag']} {country}",
            "Latest (%)": f"{s['latest']:.1f}",
            "YoY Change": f"{'↓' if s['yoy_change'] < 0 else '↑'} {abs(s['yoy_change']):.1f}pp",
            "5-Yr CAGR": f"{s['cagr_5y']:+.1f}%",
            "vs GCC Avg": f"{s['latest'] - s['gcc_avg_2024']:+.1f}pp",
            "Trend": trend_en,
            "Rank": s["rank_2024"],
        })
    st.dataframe(
        pd.DataFrame(summary_rows).set_index("Country"),
        use_container_width=True,
    )

    # ── Year-on-year heatmap ──────────────────────────────────────────────────
    _section("Year-on-Year Change Heatmap")
    df_all_yoy = df_all.diff().dropna()
    fig3 = go.Figure(go.Heatmap(
        z=df_all_yoy.T.values,
        x=[str(d.year) for d in df_all_yoy.index],
        y=list(gcc_data.COUNTRIES.keys()),
        colorscale="RdYlGn_r" if lib else "RdYlGn",
        zmid=0,
        text=df_all_yoy.T.round(1).astype(str).values,
        texttemplate="%{text}pp",
        hoverongaps=False,
    ))
    fig3.update_layout(_plotly_base(), height=250,
                       xaxis_title="Year", yaxis_title="")
    st.plotly_chart(fig3, use_container_width=True)

    # ── AI Regional Intelligence Snapshot ────────────────────────────────────
    _section("AI Regional Intelligence Snapshot")
    st.markdown(
        '<div class="data-source-strip">'
        '🤖 Real-time risk classification — based on latest value, trend direction, and optimal target range'
        '</div>',
        unsafe_allow_html=True,
    )
    ri_cols = st.columns(6)
    for i, (country, info) in enumerate(gcc_data.COUNTRIES.items()):
        s = stats[country]
        historical_s = gcc_data.get_series(country, ind)
        _, _, improving_c = intel_module._slope_label(s["slope"], lib)
        rp = intel_module.compute_risk_profile(
            indicator=ind,
            latest=s["latest"],
            slope=s["slope"],
            improving=improving_c,
            uncertainty_pct=10.0,
            historical=historical_s,
        )
        trend_arrow = "↓" if s["yoy_change"] < 0 else "↑"
        trend_color = "#1A7A4A" if ((s["yoy_change"] < 0 and lib) or (s["yoy_change"] > 0 and not lib)) else "#A93226"
        ri_cols[i].markdown(
            f'<div class="country-intel-card">'
            f'<div style="font-size:1.1rem;">{info["flag"]}</div>'
            f'<div style="font-size:0.78rem;font-weight:700;margin:3px 0;">{country}</div>'
            f'<div style="font-size:1.1rem;font-weight:800;color:#1B4F72;">{s["latest"]:.1f}%</div>'
            f'<div style="font-size:0.70rem;color:{trend_color};font-weight:600;">'
            f'{trend_arrow} {abs(s["yoy_change"]):.1f}pp YoY</div>'
            f'<div style="margin-top:5px;">{_badge(rp.label, rp.badge_color)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 2 – Country Explorer
# ──────────────────────────────────────────────────────────────────────────────

def page_country_explorer():
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        country = st.selectbox(
            "Country",
            list(gcc_data.COUNTRIES.keys()),
            format_func=lambda c: f"{gcc_data.COUNTRIES[c]['flag']} {c}",
            key="explorer_country",
        )
    with col_sel2:
        ind = st.selectbox(
            "Indicator",
            list(gcc_data.INDICATORS.keys()),
            format_func=lambda k: gcc_data.INDICATORS[k]["name"],
            key="explorer_ind",
        )

    info = gcc_data.COUNTRIES[country]
    meta = gcc_data.INDICATORS[ind]
    s = gcc_data.get_trend_stats(country, ind)
    lib = meta["lower_is_better"]

    _banner(
        f"{info['flag']} {country} — Strategic Employment Intelligence",
        f"{meta['name']} · {info['vision']} · 2010–2024 · Source: World Bank Open Data",
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    good_yoy = (s["yoy_change"] < 0) if lib else (s["yoy_change"] > 0)
    arrow = "↓" if s["yoy_change"] < 0 else "↑"

    k1.markdown(_kpi_card(
        "Latest Value (2024)", f"{s['latest']:.1f}%",
        f"{arrow} {abs(s['yoy_change']):.1f}pp YoY", good_yoy,
    ), unsafe_allow_html=True)
    k2.markdown(_kpi_card(
        "GCC Average (2024)", f"{s['gcc_avg_2024']:.1f}%",
        f"vs avg: {s['latest'] - s['gcc_avg_2024']:+.1f}pp",
        (s["latest"] < s["gcc_avg_2024"]) if lib else (s["latest"] > s["gcc_avg_2024"]),
    ), unsafe_allow_html=True)
    k3.markdown(_kpi_card(
        "5-Year CAGR", f"{s['cagr_5y']:+.1f}%",
        "Improving" if s["improving"] else "Worsening",
        s["improving"],
    ), unsafe_allow_html=True)
    k4.markdown(_kpi_card(
        f"GCC Rank (2024)", f"#{s['rank_2024']} of 6",
        "Best" if s["rank_2024"] == 1 else "",
        s["rank_2024"] <= 2,
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main trend chart ──────────────────────────────────────────────────────
    col_main, col_side = st.columns([2, 1])
    with col_main:
        _section(f"{country}: Historical Trend vs GCC Average")
        annual = gcc_data.get_series(country, ind)
        gcc_avg = gcc_data.get_gcc_average(ind)
        fig = go.Figure(layout=_plotly_base())
        fig.add_trace(go.Scatter(
            x=annual.index, y=annual.values,
            name=country, line=dict(color=_COUNTRY_COLORS[country], width=2.5),
            mode="lines+markers", marker=dict(size=6),
        ))
        fig.add_trace(go.Scatter(
            x=gcc_avg.index, y=gcc_avg.values,
            name="GCC Average", line=dict(color=_GOLD, width=2, dash="dot"),
            mode="lines",
        ))
        fig.update_layout(
            yaxis_title=f"{meta['name']} (%)",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        _section("All Indicators Snapshot")
        snap_rows = []
        for k, m in gcc_data.INDICATORS.items():
            ts = gcc_data.get_trend_stats(country, k)
            snap_rows.append({
                "Indicator": m["name"][:30],
                "Value": f"{ts['latest']:.1f}%",
                "Trend": "↑" if ts["improving"] else "↓",
            })
        st.dataframe(pd.DataFrame(snap_rows).set_index("Indicator"), use_container_width=True)

    # ── Year-on-year bar chart ────────────────────────────────────────────────
    _section("Year-on-Year Changes")
    yoy_series = annual.diff().dropna()
    bar_colors = [
        (_SUCCESS if (v < 0 if lib else v > 0) else _DANGER)
        for v in yoy_series.values
    ]
    fig2 = go.Figure(layout=_plotly_base())
    fig2.add_trace(go.Bar(
        x=[str(d.year) for d in yoy_series.index],
        y=yoy_series.values,
        marker_color=bar_colors,
        text=[f"{v:+.1f}pp" for v in yoy_series.values],
        textposition="outside",
    ))
    fig2.add_hline(y=0, line_color="gray", line_width=1)
    fig2.update_layout(yaxis_title="YoY Change (pp)", height=280)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Country context executive card ───────────────────────────────────────
    ctx = intel_module._COUNTRY_CONTEXT.get(country, {})
    if ctx:
        st.markdown(
            _exec_card(
                f"🏛 {info['vision']} — STRATEGIC CONTEXT",
                f'<span style="color:{_SUCCESS}">✦ Competitive Strength:</span> {ctx.get("strength","")}<br>'
                f'<span style="color:{_DANGER}">⚠ Structural Challenge:</span> {ctx.get("challenge","")}',
            ),
            unsafe_allow_html=True,
        )

    # ── AI Risk & Intelligence Quick Panel ───────────────────────────────────
    _section("AI Intelligence Assessment")
    _, _, improving_c = intel_module._slope_label(s["slope"], lib)
    rp = intel_module.compute_risk_profile(
        indicator=ind,
        latest=s["latest"],
        slope=s["slope"],
        improving=improving_c,
        uncertainty_pct=10.0,
        historical=annual,
    )
    alerts = intel_module.generate_strategic_alerts(
        country=country,
        indicator=ind,
        latest=s["latest"],
        slope=s["slope"],
        improving=improving_c,
        risk_profile=rp,
        gcc_avg_latest=s.get("gcc_avg_2024"),
        yoy_change=s["yoy_change"],
    )

    ai_c1, ai_c2 = st.columns([1, 2])
    with ai_c1:
        st.markdown(_risk_panel(rp.label, rp.severity, rp.confidence, rp.rationale),
                    unsafe_allow_html=True)
    with ai_c2:
        if alerts:
            for alert in alerts[:3]:
                st.markdown(_alert_card(alert.title, alert.message, alert.level),
                            unsafe_allow_html=True)
        else:
            st.markdown(
                _alert_card("No Active Strategic Alerts",
                            "All indicators are within normal operating parameters.", "info"),
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 3 – Forecast Center
# ──────────────────────────────────────────────────────────────────────────────

def page_forecast_center():
    _banner(
        "📈 AI Forecast Center",
        "Time-series forecasting · Expanding-window cross-validation · Six model ensemble · Probabilistic prediction intervals",
    )

    # ── Config ───────────────────────────────────────────────────────────────
    cfg1, cfg2, cfg3, cfg4 = st.columns(4)
    country = cfg1.selectbox(
        "Country",
        list(gcc_data.COUNTRIES.keys()),
        format_func=lambda c: f"{gcc_data.COUNTRIES[c]['flag']} {c}",
        key="fc_country",
    )
    ind = cfg2.selectbox(
        "Indicator",
        list(gcc_data.INDICATORS.keys()),
        format_func=lambda k: gcc_data.INDICATORS[k]["name"],
        key="fc_ind",
    )
    freq = cfg3.selectbox("Frequency", ["Annual", "Monthly"],
                           key="fc_freq")
    freq_code = "Y" if freq == "Annual" else "M"
    max_h = 5 if freq_code == "Y" else 24
    horizon = cfg4.slider("Forecast Horizon", 1, max_h, 3 if freq_code == "Y" else 12, key="fc_horizon")

    confidence = st.slider("Confidence Level", 0.70, 0.95, 0.80, 0.05, key="fc_conf")
    alpha = 1 - confidence

    run_col, _ = st.columns([1, 4])
    run = run_col.button("🚀 Run Forecast", type="primary", use_container_width=True)

    if run or "fc_results" in st.session_state:
        if run:
            with st.spinner("Running backtesting and model selection…"):
                try:
                    y, fc, lo, hi, backtest, best_model = _run_forecast(
                        country, ind, freq_code, horizon, alpha,
                    )
                    st.session_state["fc_results"] = (y, fc, lo, hi, backtest, best_model)
                    st.session_state["fc_meta"] = (country, ind, freq_code, horizon, confidence)
                except Exception as e:
                    st.error(f"Forecasting error: {e}")
                    return

        if "fc_results" not in st.session_state:
            return

        y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
        meta = gcc_data.INDICATORS[ind]

        st.markdown("<br>", unsafe_allow_html=True)
        _section("Results")

        smape_tier = "Excellent" if backtest.best_model_smape < 5 else ("Good" if backtest.best_model_smape < 12 else "Moderate")
        smape_color = _SUCCESS if backtest.best_model_smape < 5 else (_WARNING if backtest.best_model_smape < 12 else _DANGER)
        st.markdown(
            _exec_card(
                "🏆 MODEL SELECTION RESULT — EXPANDING-WINDOW CROSS-VALIDATION",
                f'<strong>Best Model:</strong> {backtest.best_model_name} &nbsp;|&nbsp; '
                f'sMAPE: <strong style="color:{smape_color}">{backtest.best_model_smape:.2f}%</strong> '
                f'(<em>{smape_tier}</em>) &nbsp;|&nbsp; '
                f'RMSE: <strong>{backtest.best_model_rmse:.3f}</strong>',
            ),
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3 = st.tabs(["📈 Forecast Chart", "📊 Model Comparison", "📋 Forecast Table"])

        with tab1:
            fig = go.Figure(layout=_plotly_base(f"{gcc_data.COUNTRIES[country]['flag']} {country} — {meta['name']} Forecast"))
            fig.add_trace(go.Scatter(
                x=y.index, y=y.values, name="Historical",
                line=dict(color=_COUNTRY_COLORS.get(country, _PRIMARY), width=2.5),
                mode="lines+markers", marker=dict(size=5),
            ))
            fig.add_trace(go.Scatter(
                x=fc.index, y=fc.values, name="Forecast",
                line=dict(color=_GOLD, width=2.5, dash="dash"),
                mode="lines+markers", marker=dict(size=6, symbol="diamond"),
            ))
            fig.add_trace(go.Scatter(
                x=list(hi.index) + list(lo.index[::-1]),
                y=list(hi.values) + list(lo.values[::-1]),
                fill="toself", fillcolor=f"rgba(195,155,78,0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{confidence*100:.0f}% Prediction Interval",
                showlegend=True,
            ))
            # Separator line
            fig.add_vline(x=str(y.index[-1]), line_dash="dot", line_color="gray", opacity=0.5)
            fig.update_layout(
                yaxis_title=f"{meta['name']} ({meta['unit']})",
                hovermode="x unified", height=420,
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            comp = backtest.comparison_df.copy().round(3)
            fig2 = go.Figure(layout=_plotly_base("Model Comparison — sMAPE (lower is better)"))
            colors_bar = [_GOLD if m == backtest.best_model_name else "#AABBCC" for m in comp["model"]]
            fig2.add_trace(go.Bar(
                x=comp["model"], y=comp["smape"],
                marker_color=colors_bar,
                text=[f"{v:.2f}%" for v in comp["smape"]],
                textposition="outside",
            ))
            fig2.update_layout(yaxis_title="sMAPE (%)", height=320)
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(comp.set_index("model"), use_container_width=True)

        with tab3:
            fc_df = pd.DataFrame({
                "Period": fc.index.strftime("%Y-%m-%d"),
                f"Forecast ({meta['unit']})": fc.values.round(2),
                f"Lower ({confidence*100:.0f}%)": lo.values.round(2),
                f"Upper ({confidence*100:.0f}%)": hi.values.round(2),
            })
            st.dataframe(fc_df, use_container_width=True, hide_index=True)
            csv = fc_df.to_csv(index=False).encode()
            st.download_button("⬇ Download Forecast CSV", csv, "forecast.csv", "text/csv")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 4 – AI Insights
# ──────────────────────────────────────────────────────────────────────────────

def page_ai_insights():
    _banner(
        "🤖 AI Decision Intelligence",
        "Ministry-grade bilingual analysis · Strategic risk engine · Policy recommendations · Comparative GCC intelligence",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.info("💡 Run a forecast in the **Forecast Center** first to generate AI insights.")
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    gcc_avg = gcc_data.get_gcc_average(ind)

    with st.spinner("Generating AI intelligence report…"):
        report = intel_module.generate_intelligence_report(
            country=country, indicator=ind,
            historical=y, forecast=fc, lower=lo, upper=hi,
            model_name=backtest.best_model_name,
            model_smape=backtest.best_model_smape,
            gcc_average=gcc_avg,
        )

    # ── Strategic Alerts strip ────────────────────────────────────────────────
    if report.strategic_alerts:
        _section("Strategic Alerts")
        for alert in report.strategic_alerts:
            st.markdown(_alert_card(alert.title, alert.message, alert.level),
                        unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    tab_en, tab_ar = st.tabs(["🇬🇧 English Report", "🇸🇦 التقرير العربي"])

    # ── English ──────────────────────────────────────────────────────────────
    with tab_en:
        # Risk profile + trend/urgency badges
        trend_badge = _badge(report.trend_label, report.trend_label.lower())
        urgency_badge = _badge(f"Priority: {report.urgency_level}", report.urgency_level.lower())
        risk_badge = _badge(
            f"Risk: {report.risk_profile.label}",
            report.risk_profile.badge_color,
        )
        conf_badge = _badge(
            f"Confidence: {report.risk_profile.confidence}",
            "low" if report.risk_profile.confidence == "High" else "medium",
        )
        st.markdown(f"{trend_badge} {urgency_badge} {risk_badge} {conf_badge}",
                    unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Risk Panel
        st.markdown(
            _risk_panel(
                report.risk_profile.label,
                report.risk_profile.severity,
                report.risk_profile.confidence,
                report.risk_profile.rationale,
            ),
            unsafe_allow_html=True,
        )

        _section("Executive Summary")
        st.markdown(
            _exec_card("EXECUTIVE INTELLIGENCE SUMMARY", report.executive_summary),
            unsafe_allow_html=True,
        )

        _section("Key Insights")
        for ins in report.key_insights:
            st.markdown(_insight_html(ins), unsafe_allow_html=True)

        # GCC Comparison & Causal Interpretation side by side
        col_gcc, col_causal = st.columns(2)
        with col_gcc:
            _section("Comparative GCC Intelligence")
            st.markdown(
                _exec_card("REGIONAL BENCHMARKING ANALYSIS", report.gcc_comparison),
                unsafe_allow_html=True,
            )
        with col_causal:
            _section("Causal & Driver Interpretation")
            st.markdown(
                _exec_card("STRUCTURAL DRIVER ANALYSIS", report.causal_interpretation),
                unsafe_allow_html=True,
            )

        col_r, col_f = st.columns(2)
        with col_r:
            _section("Risk Assessment")
            for risk in report.risk_assessment:
                st.markdown(_insight_html(risk, "risk"), unsafe_allow_html=True)
        with col_f:
            _section("Influencing Factors")
            for fac in report.influencing_factors:
                st.markdown(_insight_html(fac), unsafe_allow_html=True)

        _section("Strategic Policy Recommendations")
        for rec in report.policy_recommendations:
            st.markdown(_insight_html(rec, "rec"), unsafe_allow_html=True)

        _section("Forecast Outlook")
        st.markdown(
            _exec_card("🔭 FORECAST OUTLOOK & STRATEGIC HORIZON", report.forecast_outlook),
            unsafe_allow_html=True,
        )

    # ── Arabic ───────────────────────────────────────────────────────────────
    with tab_ar:
        trend_badge_ar = _badge(report.trend_label_ar, report.trend_label.lower())
        risk_badge_ar = _badge(report.risk_profile.label_ar, report.risk_profile.badge_color)
        st.markdown(f"{trend_badge_ar} {risk_badge_ar}", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        def _ar_block(title: str, content: str) -> None:
            st.markdown(f"**{title}**")
            st.markdown(f'<div class="arabic-block">{content}</div>', unsafe_allow_html=True)

        def _ar_list_block(title: str, items: list) -> None:
            st.markdown(f"**{title}**")
            content = "<br>".join(f"• {i}" for i in items)
            st.markdown(f'<div class="arabic-block">{content}</div>', unsafe_allow_html=True)

        _ar_block("الملخص التنفيذي", report.ar_executive_summary)
        _ar_list_block("أبرز المؤشرات والرؤى", report.ar_key_insights)

        col_gcc_ar, col_causal_ar = st.columns(2)
        with col_gcc_ar:
            _ar_block("مقارنة خليجية", report.ar_gcc_comparison)
        with col_causal_ar:
            _ar_block("العوامل السببية والمحركات", report.ar_causal_interpretation)

        col_r2, col_f2 = st.columns(2)
        with col_r2:
            _ar_list_block("تحليل المخاطر", report.ar_risk_assessment)
        with col_f2:
            _ar_list_block("التوصيات الاستراتيجية", report.ar_policy_recommendations)

        _ar_block("النظرة المستقبلية والتوقعات", report.ar_forecast_outlook)

        # Arabic alerts
        if report.strategic_alerts:
            st.markdown("**التنبيهات الاستراتيجية**")
            for alert in report.strategic_alerts:
                st.markdown(
                    f'<div class="arabic-block alert-{alert.level}" '
                    f'style="border-right:4px solid; margin:0.3rem 0; padding:0.8rem 1rem;">'
                    f'<strong>{alert.title_ar}</strong><br>{alert.message_ar}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Download
        ar_report_text = intel_module.format_arabic_executive_report(report)
        st.download_button(
            "⬇ تحميل التقرير العربي الكامل",
            ar_report_text.encode("utf-8"),
            "gcc_executive_report_ar.txt",
            "text/plain",
        )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 5 – Scenario Simulator
# ──────────────────────────────────────────────────────────────────────────────

def page_scenario_simulator():
    _banner(
        "⚙️ Policy Scenario Simulator",
        "What-if analysis · Elasticity-based impact modelling · Bilingual narrative · Strategic policy planning",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.info("💡 Run a forecast in the **Forecast Center** first to enable scenario simulation.")
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    meta = gcc_data.INDICATORS[ind]

    st.markdown(
        _exec_card(
            "SCENARIO CONFIGURATION",
            f'Country: <strong>{gcc_data.COUNTRIES[country]["flag"]} {country}</strong> &nbsp;|&nbsp; '
            f'Indicator: <strong>{meta["name"]}</strong> &nbsp;|&nbsp; '
            f'Baseline Model: <strong>{backtest.best_model_name}</strong>',
        ),
        unsafe_allow_html=True,
    )

    param_configs = scenario_module.get_param_config()

    # ── Sliders in sidebar-style left panel ──────────────────────────────────
    col_params, col_results = st.columns([1, 2])

    with col_params:
        _section("Policy Levers")
        st.markdown('<div style="font-size:0.78rem;color:#666;margin-bottom:0.8rem;">Adjust each parameter from its baseline. Values represent change in percentage points (pp).</div>', unsafe_allow_html=True)

        params: dict = {}
        for p in param_configs:
            params[p["key"]] = st.slider(
                p["label"],
                min_value=p["min"], max_value=p["max"],
                value=p["default"], step=p["step"],
                key=f"scenario_{p['key']}",
                help=f"Arabic: {p['label_ar']}",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        run_scenario = st.button("🔄 Recompute Scenario", type="primary", use_container_width=True)

    with col_results:
        result = scenario_module.apply_scenario(
            baseline_forecast=fc, baseline_lower=lo, baseline_upper=hi,
            params=params, indicator=ind, country=country,
        )

        # ── Impact summary ───────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        impact_good = result.optimistic
        arrow = "↓" if result.total_impact_pp < 0 else "↑"

        m1.markdown(_kpi_card(
            "Baseline Forecast (End)",
            f"{result.baseline_forecast.iloc[-1]:.2f}%",
        ), unsafe_allow_html=True)
        m2.markdown(_kpi_card(
            "Scenario Forecast (End)",
            f"{result.scenario_forecast.iloc[-1]:.2f}%",
            f"{arrow} {abs(result.total_impact_pp):.2f}pp", impact_good,
        ), unsafe_allow_html=True)
        m3.markdown(_kpi_card(
            "Relative Impact",
            f"{result.total_impact_pct:+.1f}%",
            "Favourable" if impact_good else "Adverse", impact_good,
        ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Scenario chart ───────────────────────────────────────────────────
        _section("Baseline vs Scenario Forecast")
        fig = go.Figure(layout=_plotly_base())

        # Historical
        fig.add_trace(go.Scatter(
            x=y.index, y=y.values, name="Historical",
            line=dict(color=_COUNTRY_COLORS.get(country, _PRIMARY), width=2),
            mode="lines+markers", marker=dict(size=4),
        ))
        # Baseline
        fig.add_trace(go.Scatter(
            x=result.baseline_forecast.index, y=result.baseline_forecast.values,
            name="Baseline Forecast",
            line=dict(color="#888", width=2, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=list(result.baseline_upper.index) + list(result.baseline_lower.index[::-1]),
            y=list(result.baseline_upper.values) + list(result.baseline_lower.values[::-1]),
            fill="toself", fillcolor="rgba(150,150,150,0.1)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        ))
        # Scenario
        sc_color = _SUCCESS if impact_good else _DANGER
        fig.add_trace(go.Scatter(
            x=result.scenario_forecast.index, y=result.scenario_forecast.values,
            name="Scenario Forecast",
            line=dict(color=sc_color, width=2.5),
            mode="lines+markers", marker=dict(size=6, symbol="diamond"),
        ))
        fig.add_trace(go.Scatter(
            x=list(result.scenario_upper.index) + list(result.scenario_lower.index[::-1]),
            y=list(result.scenario_upper.values) + list(result.scenario_lower.values[::-1]),
            fill="toself", fillcolor=f"rgba({'26,122,74' if impact_good else '169,50,38'},0.1)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        ))
        fig.add_vline(x=str(y.index[-1]), line_dash="dot", line_color="gray", opacity=0.5)
        fig.update_layout(yaxis_title=f"{meta['name']} (%)", hovermode="x unified", height=360)
        st.plotly_chart(fig, use_container_width=True)

        # ── Driver waterfall ─────────────────────────────────────────────────
        _section("Driver Contribution Breakdown")
        active = {k: v for k, v in result.driver_contributions.items() if abs(v) > 1e-4}
        if active:
            driver_labels = [scenario_module._PARAM_LABELS.get(k, k) for k in active]
            driver_vals = list(active.values())
            bar_colors_d = [_SUCCESS if ((v < 0 and meta["lower_is_better"]) or (v > 0 and not meta["lower_is_better"])) else _DANGER for v in driver_vals]

            fig_d = go.Figure(layout=_plotly_base())
            fig_d.add_trace(go.Bar(
                x=driver_labels, y=driver_vals,
                marker_color=bar_colors_d,
                text=[f"{v:+.3f}pp" for v in driver_vals],
                textposition="outside",
            ))
            fig_d.add_hline(y=0, line_color="gray", line_width=1)
            fig_d.update_layout(yaxis_title="Impact (pp)", height=280)
            st.plotly_chart(fig_d, use_container_width=True)

        # ── AI Narrative ─────────────────────────────────────────────────────
        _section("AI Scenario Interpretation")
        st.markdown(
            _exec_card(
                "AI SCENARIO NARRATIVE",
                result.summary_en,
            ),
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="arabic-block">{result.summary_ar}</div>',
                    unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 6 – Explainability
# ──────────────────────────────────────────────────────────────────────────────

def page_explainability():
    _banner(
        "🔬 AI Explainability Center",
        "Transparent forecasting · Model diagnostics · Feature importance · Decomposition · Uncertainty analysis",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.info("💡 Run a forecast in the **Forecast Center** first to view explainability diagnostics.")
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    meta = gcc_data.INDICATORS[ind]

    tab_model, tab_fi, tab_decomp, tab_ci = st.tabs([
        "📊 Model Performance",
        "🔑 Feature Importance",
        "📉 Decomposition",
        "📐 Confidence Intervals",
    ])

    # ── Model Performance ─────────────────────────────────────────────────────
    with tab_model:
        _section("Cross-Validation Model Comparison")
        st.markdown(
            _exec_card(
                "METHODOLOGY — EXPANDING-WINDOW CROSS-VALIDATION",
                "Models were evaluated using <strong>expanding-window cross-validation</strong>. "
                "sMAPE (Symmetric Mean Absolute Percentage Error) is the primary selection metric — "
                "it is robust to near-zero values and symmetric around over/under-forecasting errors.",
            ),
            unsafe_allow_html=True,
        )

        comp = backtest.comparison_df.copy()

        col_t, col_ch = st.columns([1, 2])
        with col_t:
            display = comp.set_index("model").round(3)
            display.columns = ["MAE", "RMSE", "MAPE (%)", "sMAPE (%)"]
            st.dataframe(
                display.style.highlight_min(subset=["sMAPE (%)"], color="#D5F5E3"),
                use_container_width=True,
            )

        with col_ch:
            fig = go.Figure(layout=_plotly_base("sMAPE by Model (lower = better)"))
            bar_c = [_GOLD if m == backtest.best_model_name else "#AABBCC" for m in comp["model"]]
            fig.add_trace(go.Bar(
                x=comp["model"], y=comp["smape"],
                marker_color=bar_c,
                text=[f"{v:.2f}%" for v in comp["smape"]],
                textposition="outside",
            ))
            fig.update_layout(yaxis_title="sMAPE (%)", height=300)
            st.plotly_chart(fig, use_container_width=True)

        # ── Metric explanations ───────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        _section("Metric Definitions")
        m1, m2, m3, m4 = st.columns(4)
        for col, name, desc in [
            (m1, "MAE", "Mean absolute difference between forecast and actual values."),
            (m2, "RMSE", "Root mean squared error — penalises large errors more heavily."),
            (m3, "MAPE", "Mean absolute % error — undefined near zero values."),
            (m4, "sMAPE", "Symmetric MAPE — the primary competition-grade metric used here."),
        ]:
            col.markdown(f'<div class="insight-card"><strong>{name}</strong><br><span style="font-size:0.82rem">{desc}</span></div>',
                         unsafe_allow_html=True)

    # ── Feature Importance ────────────────────────────────────────────────────
    with tab_fi:
        _section("Feature Importance (LightGBM)")
        if hasattr(best_model, "get_feature_importance"):
            try:
                fi = best_model.get_feature_importance().head(15)
                fig = go.Figure(layout=_plotly_base("Top Feature Importances"))
                fig.add_trace(go.Bar(
                    x=fi.values[::-1], y=fi.index.tolist()[::-1],
                    orientation="h", marker_color=_PRIMARY,
                    text=[f"{v:.1f}" for v in fi.values[::-1]],
                    textposition="outside",
                ))
                fig.update_layout(xaxis_title="Importance Score", height=max(300, len(fi) * 22 + 60))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(
                    _exec_card(
                        "FEATURE IMPORTANCE — LIGHTGBM INTERPRETATION",
                        "Feature importance reflects how much each input variable contributed to the LightGBM model's "
                        "predictions. <strong>Lag features</strong> capture autocorrelation; "
                        "<strong>rolling statistics</strong> capture local trend momentum; "
                        "<strong>calendar features</strong> (month, year) capture seasonality and structural drift.",
                    ),
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.info(f"Feature importance not available for {best_model.name}: {e}")
        else:
            st.info(f"Feature importance is specific to the LightGBM model. The selected best model is **{best_model.name}**.")

    # ── Decomposition ─────────────────────────────────────────────────────────
    with tab_decomp:
        _section("Time-Series Decomposition")
        from src.explain import decompose_series
        with st.spinner("Decomposing series…"):
            try:
                decomp = decompose_series(y, freq=freq_code)
                c1, c2 = st.columns(2)
                c1.metric("Trend Direction", decomp.trend_direction.capitalize())
                c2.metric("Seasonality Strength", f"{decomp.seasonality_strength:.0%}")

                components = [
                    ("Observed", y, _COUNTRY_COLORS.get(country, _PRIMARY)),
                    ("Trend", decomp.trend, _PRIMARY),
                    ("Seasonal", decomp.seasonal, _GOLD),
                    ("Residual", decomp.residual, _DANGER),
                ]
                fig = go.Figure()
                for i, (name, series, color) in enumerate(components):
                    fig.add_trace(go.Scatter(
                        x=series.index, y=series.values,
                        name=name, line=dict(color=color, width=1.8),
                        xaxis="x", yaxis=f"y{i+1}",
                    ))
                fig.update_layout(
                    template="plotly_white",
                    height=600,
                    grid=dict(rows=4, columns=1, pattern="independent"),
                    yaxis=dict(title="Observed", domain=[0.77, 1.0]),
                    yaxis2=dict(title="Trend", domain=[0.52, 0.74]),
                    yaxis3=dict(title="Seasonal", domain=[0.27, 0.49]),
                    yaxis4=dict(title="Residual", domain=[0.0, 0.24]),
                    legend=dict(orientation="h", y=-0.05),
                    margin=dict(l=60, r=20, t=30, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Decomposition not available: {e}")

    # ── Confidence Intervals ─────────────────────────────────────────────────
    with tab_ci:
        _section("Prediction Interval Analysis")
        widths = (hi - lo).values
        horizon_labels = [f"H+{i+1}" for i in range(len(widths))]

        fig = go.Figure(layout=_plotly_base("Prediction Interval Width by Horizon"))
        fig.add_trace(go.Bar(
            x=horizon_labels, y=widths,
            marker_color=_PRIMARY,
            text=[f"{w:.2f}pp" for w in widths],
            textposition="outside",
        ))
        fig.update_layout(yaxis_title="Interval Width (pp)", height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            _exec_card(
                "🔭 UNCERTAINTY INTERPRETATION",
                f'The <strong>{confidence*100:.0f}% prediction interval</strong> means that if model assumptions hold, '
                f'{confidence*100:.0f}% of actual future values should fall within the shaded band. '
                f'Wider intervals at longer horizons reflect compounding uncertainty — a natural property of all '
                f'time-series forecasting models. Average interval width: '
                f'<strong>{widths.mean():.2f} percentage points</strong>.',
            ),
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if PAGE.startswith("🌍"):
        page_gcc_overview()
    elif PAGE.startswith("🔍"):
        page_country_explorer()
    elif PAGE.startswith("📈"):
        page_forecast_center()
    elif PAGE.startswith("🤖"):
        page_ai_insights()
    elif PAGE.startswith("⚙️"):
        page_scenario_simulator()
    elif PAGE.startswith("🔬"):
        page_explainability()


if __name__ == "__main__":
    main()

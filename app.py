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
/* ── Global ── */
[data-testid="stAppViewContainer"] {{ background-color: {_LIGHT_BG}; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {_PRIMARY} 0%, #0D2F45 100%); }}
[data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
[data-testid="stSidebar"] .stRadio > label {{ color: #E8EDF2 !important; font-size:0.85rem; }}
[data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stSlider label {{ color: #BDD0DF !important; }}
div[data-testid="metric-container"] {{ background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.07); }}

/* ── Banner ── */
.platform-banner {{
    background: linear-gradient(135deg, {_PRIMARY} 0%, #2874A6 100%);
    color: white; padding: 1.8rem 2rem; border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(27,79,114,0.25);
}}
.platform-banner h1 {{ margin:0; font-size:1.7rem; font-weight:700; letter-spacing:-0.3px; }}
.platform-banner p  {{ margin:0.3rem 0 0; font-size:0.9rem; opacity:0.85; }}

/* ── Section header ── */
.section-header {{
    border-left: 4px solid {_GOLD}; padding-left: 12px;
    margin: 1.5rem 0 1rem; color: {_PRIMARY}; font-weight: 700; font-size: 1.1rem;
}}

/* ── KPI card ── */
.kpi-card {{
    background: white; border-radius: 10px; padding: 1.1rem 1.2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-top: 3px solid {_PRIMARY}; text-align: center;
    transition: transform .15s ease;
}}
.kpi-card:hover {{ transform: translateY(-2px); }}
.kpi-val  {{ font-size: 1.9rem; font-weight: 700; color: {_PRIMARY}; line-height:1.1; }}
.kpi-label{{ font-size: 0.72rem; color: #666; text-transform: uppercase; letter-spacing:.5px; margin-top:4px; }}
.kpi-delta{{ font-size: 0.82rem; margin-top:4px; font-weight:600; }}
.delta-good{{ color: {_SUCCESS}; }}
.delta-bad {{ color: {_DANGER};  }}

/* ── Insight cards ── */
.insight-card {{
    background: white; border-radius: 8px; padding: 1rem 1.2rem;
    margin: 0.5rem 0; box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    border-left: 4px solid {_PRIMARY};
}}
.risk-card    {{ border-left-color: {_DANGER}; }}
.rec-card     {{ border-left-color: {_SUCCESS}; }}
.outlook-card {{ border-left-color: {_GOLD}; background: #FFFBF2; }}

/* ── Arabic ── */
.arabic-block {{
    direction: rtl; text-align: right;
    font-family: 'Amiri', 'Traditional Arabic', 'Arial', sans-serif;
    line-height: 2.0; font-size: 1.0rem;
    background: white; border-radius: 8px; padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin: 0.5rem 0;
    border-right: 4px solid {_GOLD};
}}

/* ── Badge ── */
.badge {{
    display:inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: .3px;
}}
.badge-improving {{ background:#D5F5E3; color:{_SUCCESS}; }}
.badge-worsening {{ background:#FADBD8; color:{_DANGER}; }}
.badge-stable    {{ background:#EAF2FF; color:{_PRIMARY}; }}
.badge-high      {{ background:#FADBD8; color:{_DANGER}; }}
.badge-medium    {{ background:#FDEBD0; color:{_WARNING}; }}
.badge-low       {{ background:#D5F5E3; color:{_SUCCESS}; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem;">
        <div style="font-size:2.5rem;">🌍</div>
        <div style="font-weight:700; font-size:1.0rem; letter-spacing:-0.3px;">GCC Employment Intelligence</div>
        <div style="font-size:0.72rem; opacity:0.65; margin-top:2px;">AI Policy Analytics Platform</div>
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

    st.markdown(
        f'<div style="font-size:0.72rem; opacity:0.7; line-height:1.6;">'
        f'<strong>Data source</strong><br>'
        f'World Bank Open Data<br>'
        f'<span style="opacity:0.8;">Last updated:<br>{last_updated}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True, help="Re-fetch all indicators from World Bank API"):
        with st.spinner("Fetching data from World Bank Open Data…"):
            try:
                gcc_data.refresh(force=True)
                # Clear any cached forecasts that depend on the data
                for k in list(st.session_state.keys()):
                    if k in ("fc_results", "fc_meta"):
                        del st.session_state[k]
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")

    if not cache_ok:
        st.warning("⚠ No local cache found. Click **Refresh Data** to fetch from World Bank.", icon="⚠️")

    st.markdown(
        '<div style="font-size:0.68rem; opacity:0.45; padding-top:0.8rem;">'
        '© 2025 GCC Statistical Intelligence Platform'
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
    return f"""
    <div class="kpi-card">
        <div class="kpi-val">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>"""


def _insight_html(text: str, kind: str = "insight") -> str:
    cls = {"risk": "risk-card", "rec": "rec-card", "outlook": "outlook-card"}.get(kind, "insight-card")
    icon = {"risk": "⚠️", "rec": "✦", "outlook": "🔭"}.get(kind, "•")
    return f'<div class="insight-card {cls}">{icon} {text}</div>'


def _badge(text: str, kind: str) -> str:
    cls = f"badge-{kind.lower()}"
    return f'<span class="badge {cls}">{text}</span>'


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

    _banner(
        "🌍 GCC Youth Employment Intelligence Hub",
        f"Regional comparative analysis · Six-country dashboard · 2010–2024 · Source: {src_label}",
    )

    if not is_cache_available():
        st.warning(
            "⚠ Local data cache not found. Use the **🔄 Refresh Data** button in the sidebar "
            "to fetch real data from World Bank Open Data.",
            icon="⚠️",
        )
        return

    # ── Source attribution strip ──────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.75rem; color:#666; margin-bottom:0.8rem;">'
        f'📡 <strong>Data:</strong> <a href="{src_url}" target="_blank">{src_label}</a> '
        f'&nbsp;|&nbsp; Last fetched: {updated_at}'
        f'</div>',
        unsafe_allow_html=True,
    )

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
        f"{info['flag']} {country} — Employment Intelligence",
        f"{meta['name']} · {info['vision']} · In-depth analysis 2015–2024",
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

    # ── Country context card ──────────────────────────────────────────────────
    ctx = intel_module._COUNTRY_CONTEXT.get(country, {})
    if ctx:
        st.markdown(f"""
        <div class="insight-card">
            <strong>🏛 {info['vision']} Context</strong><br>
            <span style="color:{_SUCCESS}">✦ Strength:</span> {ctx.get('strength','')}<br>
            <span style="color:{_DANGER}">⚠ Challenge:</span> {ctx.get('challenge','')}
        </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 3 – Forecast Center
# ──────────────────────────────────────────────────────────────────────────────

def page_forecast_center():
    _banner(
        "📈 Forecast Center",
        "AI-powered time-series forecasting · Model selection via expanding-window cross-validation",
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

        # Best model badge
        urgency_color = {"Low": _SUCCESS, "Medium": _WARNING, "High": _DANGER}.get(
            "Low", _PRIMARY
        )
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:1rem 1.5rem;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);
                    border-left:5px solid {_GOLD};margin-bottom:1rem;">
            🏆 <strong>Best Model:</strong> {backtest.best_model_name} &nbsp;|&nbsp;
            sMAPE: <strong>{backtest.best_model_smape:.2f}%</strong> &nbsp;|&nbsp;
            RMSE: <strong>{backtest.best_model_rmse:.3f}</strong>
        </div>""", unsafe_allow_html=True)

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
        "Bilingual executive analysis · Policy recommendations · Strategic outlook",
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

    tab_en, tab_ar = st.tabs(["🇬🇧 English Report", "🇸🇦 التقرير العربي"])

    # ── English ──────────────────────────────────────────────────────────────
    with tab_en:
        trend_badge = _badge(report.trend_label, report.trend_label.lower())
        urgency_badge = _badge(f"Priority: {report.urgency_level}", report.urgency_level.lower())
        st.markdown(f"{trend_badge} {urgency_badge}", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        _section("Executive Summary")
        st.markdown(f'<div class="insight-card">{report.executive_summary}</div>',
                    unsafe_allow_html=True)

        _section("Key Insights")
        for ins in report.key_insights:
            st.markdown(_insight_html(ins), unsafe_allow_html=True)

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
        st.markdown(f'<div class="insight-card outlook-card">{report.forecast_outlook}</div>',
                    unsafe_allow_html=True)

    # ── Arabic ───────────────────────────────────────────────────────────────
    with tab_ar:
        trend_badge_ar = _badge(report.trend_label_ar, report.trend_label.lower())
        st.markdown(f"{trend_badge_ar}", unsafe_allow_html=True)
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

        col_r2, col_f2 = st.columns(2)
        with col_r2:
            _ar_list_block("تحليل المخاطر", report.ar_risk_assessment)
        with col_f2:
            _ar_list_block("التوصيات الاستراتيجية", report.ar_policy_recommendations)

        _ar_block("النظرة المستقبلية", report.ar_forecast_outlook)

        # Download
        ar_report_text = intel_module.format_arabic_executive_report(report)
        st.download_button(
            "⬇ تحميل التقرير العربي",
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
        "AI-powered 'what-if' analysis · Elasticity-based impact modelling · Strategic planning tool",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.info("💡 Run a forecast in the **Forecast Center** first to enable scenario simulation.")
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    meta = gcc_data.INDICATORS[ind]

    st.markdown(f"""
    <div class="insight-card" style="margin-bottom:1rem;">
        Simulating scenarios for: <strong>{gcc_data.COUNTRIES[country]['flag']} {country}</strong> —
        <strong>{meta['name']}</strong> · Baseline model: <strong>{backtest.best_model_name}</strong>
    </div>""", unsafe_allow_html=True)

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
        st.markdown(f'<div class="insight-card {"rec-card" if impact_good else "risk-card"}">{result.summary_en}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="arabic-block">{result.summary_ar}</div>',
                    unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 6 – Explainability
# ──────────────────────────────────────────────────────────────────────────────

def page_explainability():
    _banner(
        "🔬 Explainability Center",
        "Transparent AI · Model diagnostics · Prediction interval analysis · Decomposition",
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
        st.markdown("""
        <div class="insight-card" style="margin-bottom:1rem;">
            Models were evaluated using <strong>expanding-window cross-validation</strong>.
            sMAPE (Symmetric Mean Absolute Percentage Error) is the primary selection metric —
            it is robust to near-zero values and symmetric around over/under-forecasting.
        </div>""", unsafe_allow_html=True)

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
                st.markdown("""
                <div class="insight-card">
                    Feature importance reflects how much each input variable contributed to the LightGBM model's
                    predictions across the training period. Lag features capture autocorrelation; rolling statistics
                    capture local trends; calendar features (month, year) capture seasonality and drift.
                </div>""", unsafe_allow_html=True)
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

        st.markdown(f"""
        <div class="insight-card outlook-card">
            <strong>🔭 Uncertainty Interpretation</strong><br>
            The <strong>{confidence*100:.0f}% prediction interval</strong> means that if the model assumptions hold,
            {confidence*100:.0f}% of actual future values should fall within the shaded band.
            Wider intervals at longer horizons reflect compounding uncertainty — a natural property of all
            time-series forecasting models. The average interval width is
            <strong>{widths.mean():.2f} percentage points</strong>.
        </div>""", unsafe_allow_html=True)


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

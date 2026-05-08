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

/* ══ Scenario preset cards ═══════════════════════════════════════════════════ */
.preset-card {{
    background: white; border-radius: 12px; padding: 0.85rem 0.9rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border: 1.5px solid #E0E8F0; text-align: center;
    transition: all 0.2s cubic-bezier(.25,.46,.45,.94);
    min-height: 96px;
}}
.preset-card:hover {{
    box-shadow: 0 6px 22px rgba(27,79,114,0.16);
    border-color: {_PRIMARY}; transform: translateY(-2px);
}}
.preset-card.active {{
    border-color: {_SUCCESS};
    background: linear-gradient(135deg, white 0%, #EAFAF1 100%);
    box-shadow: 0 4px 18px rgba(26,122,74,0.18);
}}
.preset-icon {{ font-size: 1.55rem; line-height: 1; margin-bottom: 0.3rem; }}
.preset-name {{ font-weight: 700; font-size: 0.80rem; color: {_PRIMARY}; line-height: 1.2; }}
.preset-desc {{ font-size: 0.64rem; color: #888; margin-top: 3px; line-height: 1.3; }}

/* ══ Scenario intel banner ═══════════════════════════════════════════════════ */
.scenario-intel-banner {{
    border-radius: 12px; padding: 1rem 1.4rem; margin: 0.8rem 0;
    display: flex; align-items: center; gap: 1rem;
    border: 1px solid;
}}
.scenario-intel-banner.opportunity {{
    background: linear-gradient(135deg, #EAFAF1 0%, #F3FBF7 100%);
    border-color: {_SUCCESS};
}}
.scenario-intel-banner.risk {{
    background: linear-gradient(135deg, #FDEDEC 0%, #FEF5F5 100%);
    border-color: {_DANGER};
}}
.scenario-intel-banner.warning {{
    background: linear-gradient(135deg, #FEF9E7 0%, #FDFBF2 100%);
    border-color: {_WARNING};
}}
.scenario-intel-banner.pressure {{
    background: linear-gradient(135deg, #F5EEF8 0%, #F9F5FB 100%);
    border-color: #6C3483;
}}
.scenario-intel-banner.neutral {{
    background: linear-gradient(135deg, #EAF2FF 0%, #F5F8FC 100%);
    border-color: {_PRIMARY};
}}
.scenario-intel-icon {{ font-size: 2rem; line-height: 1; }}
.scenario-intel-label {{ font-size: 1.05rem; font-weight: 800; line-height: 1.2; }}
.scenario-intel-sub {{ font-size: 0.78rem; opacity: 0.75; margin-top: 2px; }}

/* ══ Scenario report section ══════════════════════════════════════════════════ */
.scenario-section {{
    background: white; border-radius: 10px; padding: 1rem 1.3rem;
    margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-left: 4px solid {_PRIMARY}; line-height: 1.65;
}}
.scenario-section-title {{
    font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.9px;
    font-weight: 700; color: {_GOLD}; margin-bottom: 0.45rem;
}}

/* ══ Custom scrollbar ════════════════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: #EEF2F7; }}
::-webkit-scrollbar-thumb {{ background: #B8CCE0; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {_PRIMARY}; }}

/* ══ Demo guide & next-step CTA (Priority 6) ════════════════════════════════ */
.demo-guide-card {{
    background: linear-gradient(135deg, #F5F8FD 0%, #EEF3FB 100%);
    border-radius: 16px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
    border: 1.5px solid rgba(27,79,114,0.14);
    box-shadow: 0 4px 20px rgba(27,79,114,0.08);
}}
.demo-guide-title {{
    font-size: 1.1rem; font-weight: 800; color: {_PRIMARY}; margin-bottom: 0.4rem;
}}
.demo-guide-sub {{
    font-size: 0.87rem; color: #555; line-height: 1.6; margin-bottom: 1rem;
}}
.demo-steps {{
    display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1.2rem;
}}
.demo-step {{
    display: flex; align-items: center; gap: 8px;
    background: white; border-radius: 8px; padding: 0.5rem 0.75rem;
    border: 1px solid rgba(27,79,114,0.1); font-size: 0.78rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}}
.demo-step-num {{
    width: 20px; height: 20px; border-radius: 50%;
    background: {_PRIMARY}; color: white;
    font-size: 0.65rem; font-weight: 800;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}}
.next-step-cta {{
    background: linear-gradient(135deg, {_PRIMARY} 0%, #2874A6 100%);
    border-radius: 12px; padding: 1rem 1.4rem; margin-top: 2rem;
    color: white; display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 18px rgba(27,79,114,0.28);
}}
.next-step-label {{
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.8px;
    opacity: 0.75; margin-bottom: 3px;
}}
.next-step-title {{ font-size: 1.0rem; font-weight: 800; }}
.next-step-arrow {{ font-size: 1.6rem; opacity: 0.8; }}
.quick-demo-bar {{
    background: linear-gradient(135deg, #EAFAF1 0%, #F5FBF8 100%);
    border-radius: 10px; padding: 0.75rem 1.1rem; margin-bottom: 1rem;
    border: 1px solid rgba(26,122,74,0.2);
    display: flex; align-items: center; gap: 1rem;
}}
.story-panel {{
    background: white; border-radius: 14px; padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(27,79,114,0.08);
    border: 1px solid rgba(27,79,114,0.07); margin-bottom: 1.5rem;
}}
.story-panel-title {{
    font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.9px;
    color: {_GOLD}; font-weight: 700; margin-bottom: 0.5rem;
}}
.impact-stat-row {{
    display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem;
}}
.impact-stat {{
    flex: 1; min-width: 120px; background: {_LIGHT_BG}; border-radius: 10px;
    padding: 0.8rem 1rem; text-align: center; border: 1px solid rgba(27,79,114,0.06);
}}
.impact-stat-num {{ font-size: 1.5rem; font-weight: 900; color: {_PRIMARY}; }}
.impact-stat-lbl {{ font-size: 0.67rem; color: #777; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
/* ══ Trust & confidence panel (Priority 5) ═══════════════════════════════════ */
.trust-header {{
    background: linear-gradient(135deg, #091320 0%, #0D2A42 40%, #1B4F72 100%);
    border-radius: 16px; padding: 1.6rem 2rem; color: white;
    display: flex; align-items: center; gap: 2rem;
    box-shadow: 0 8px 32px rgba(9,19,32,0.32);
    border: 1px solid rgba(195,155,78,0.22); margin-bottom: 1.5rem;
}}
.trust-score-ring {{
    min-width: 80px; text-align: center;
}}
.trust-score-num {{
    font-size: 2.6rem; font-weight: 900; line-height: 1; color: #E8C96E;
}}
.trust-score-lbl {{
    font-size: 0.60rem; text-transform: uppercase; letter-spacing: 0.8px;
    opacity: 0.65; margin-top: 3px;
}}
.trust-divider {{
    width: 1px; height: 60px; background: rgba(255,255,255,0.15); flex-shrink: 0;
}}
.trust-meta {{ flex: 1; }}
.trust-meta-title {{ font-size: 1.1rem; font-weight: 800; line-height: 1.2; }}
.trust-meta-sub {{ font-size: 0.82rem; opacity: 0.72; margin-top: 4px; line-height: 1.5; }}
.trust-badges {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
.trust-badge {{
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2);
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.4px;
}}

/* ══ Confidence tier card ═════════════════════════════════════════════════════ */
.confidence-card {{
    background: white; border-radius: 14px; padding: 1.3rem 1.5rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    border-top: 5px solid {_PRIMARY}; margin: 0.4rem 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.confidence-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.13); }}
.confidence-tier {{ font-size: 2rem; font-weight: 900; line-height: 1; }}
.confidence-label {{ font-size: 1.0rem; font-weight: 800; margin-top: 4px; }}
.confidence-score-bar {{
    height: 6px; border-radius: 3px; margin: 8px 0;
    background: linear-gradient(90deg, #EAEAEA, #EAEAEA);
    position: relative; overflow: hidden;
}}
.confidence-score-fill {{
    height: 100%; border-radius: 3px;
    transition: width 0.5s ease;
}}
.confidence-expl {{ font-size: 0.82rem; color: #555; line-height: 1.6; margin-top: 6px; }}

/* ══ Driver insight card ══════════════════════════════════════════════════════ */
.driver-card {{
    background: white; border-radius: 10px; padding: 0.85rem 1.1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.065); margin: 0.4rem 0;
    display: flex; align-items: flex-start; gap: 0.75rem;
    border: 1px solid rgba(27,79,114,0.07);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}}
.driver-card:hover {{ transform: translateX(3px); box-shadow: 0 4px 18px rgba(0,0,0,0.1); }}
.driver-rank {{
    min-width: 28px; height: 28px; border-radius: 50%;
    background: {_PRIMARY}; color: white;
    font-size: 0.75rem; font-weight: 800;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    margin-top: 2px;
}}
.driver-body {{ flex: 1; }}
.driver-label {{ font-weight: 700; font-size: 0.88rem; color: {_PRIMARY}; }}
.driver-pct {{
    display: inline-block; font-size: 0.68rem; font-weight: 700;
    padding: 1px 7px; border-radius: 10px;
    background: rgba(27,79,114,0.1); color: {_PRIMARY}; margin-left: 6px;
}}
.driver-dir-pos {{ color: {_SUCCESS}; font-size: 0.78rem; font-weight: 700; }}
.driver-dir-neg {{ color: {_DANGER};  font-size: 0.78rem; font-weight: 700; }}
.driver-dir-neu {{ color: {_WARNING}; font-size: 0.78rem; font-weight: 700; }}
.driver-expl {{ font-size: 0.79rem; color: #666; line-height: 1.5; margin-top: 3px; }}

/* ══ Transparency section cards ══════════════════════════════════════════════ */
.transparency-card {{
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    box-shadow: 0 3px 14px rgba(0,0,0,0.07); margin: 0.5rem 0;
    border-left: 5px solid {_PRIMARY}; line-height: 1.65;
    transition: box-shadow 0.2s ease;
}}
.transparency-card:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,0.12); }}
.transparency-card-title {{
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.9px;
    font-weight: 700; color: {_GOLD}; margin-bottom: 0.5rem;
}}
.transparency-card-body {{ font-size: 0.88rem; color: #333; }}

/* ══ Forecast caveat banner ═══════════════════════════════════════════════════ */
.caveat-strip {{
    background: rgba(195,155,78,0.08); border-radius: 8px;
    padding: 0.6rem 1.1rem; font-size: 0.79rem; color: #6B5100;
    border-left: 4px solid {_GOLD}; margin: 0.5rem 0; line-height: 1.5;
}}
.caveat-strip strong {{ color: #4A3800; }}

/* ══ Model quality badge row ═════════════════════════════════════════════════ */
.model-quality-panel {{
    background: white; border-radius: 14px; padding: 1.3rem 1.6rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08); margin: 0.5rem 0;
    border-left: 6px solid {_PRIMARY};
}}
.model-grade-badge {{
    display: inline-block; width: 44px; height: 44px; border-radius: 50%;
    font-size: 1.2rem; font-weight: 900; text-align: center; line-height: 44px;
    color: white; margin-right: 12px; flex-shrink: 0;
}}
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

    st.markdown("""
    <div style="background:rgba(195,155,78,0.08);border:1px solid rgba(195,155,78,0.22);
                border-radius:10px;padding:0.7rem 0.9rem;margin:0.6rem 0;font-size:0.69rem;
                line-height:1.7;color:rgba(255,255,255,0.75);">
        <div style="font-weight:700;font-size:0.65rem;text-transform:uppercase;
                    letter-spacing:0.8px;color:#E8C96E;margin-bottom:6px;">
            📋 Demo Flow
        </div>
        <div>1 · Regional overview &amp; KPIs</div>
        <div>2 · Country deep-dive</div>
        <div>3 · Run AI forecast</div>
        <div>4 · Read AI intelligence</div>
        <div>5 · Simulate scenarios</div>
        <div>6 · Review explainability</div>
    </div>
    """, unsafe_allow_html=True)

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
        '<div style="font-size:0.62rem; opacity:0.42; padding-top:0.9rem; text-align:center; line-height:1.6;">'
        '<strong style="color:#E8C96E;opacity:0.7;">GCC AI Intelligence Platform</strong><br>'
        'World Bank Open Data · 6 Nations · 5 Indicators<br>'
        '<span style="opacity:0.6;">AI-assisted policy analytics for GCC decision-makers</span>'
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
        if y is None or len(y) < 12:
            raise ValueError(
                f"Monthly data for {country} — {indicator} is insufficient for forecasting. "
                "Switch to Annual frequency or choose a different indicator."
            )
    else:
        y = gcc_data.get_series(country, indicator)
        if y is None or len(y) < 5:
            raise ValueError(
                f"Annual data for {country} — {indicator} has fewer than 5 observations. "
                "Use 'Refresh Data' to fetch the latest World Bank dataset."
            )

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


@st.cache_data(show_spinner=False)
def _cached_intelligence_report(
    country: str, indicator: str,
    y_json: str, fc_json: str, lo_json: str, hi_json: str,
    model_name: str, model_smape: float, gcc_avg_json: str,
):
    """Cache AI report generation — avoids regenerating on every Streamlit rerun."""
    y  = pd.read_json(io.StringIO(y_json),  typ="series")
    fc = pd.read_json(io.StringIO(fc_json), typ="series")
    lo = pd.read_json(io.StringIO(lo_json), typ="series")
    hi = pd.read_json(io.StringIO(hi_json), typ="series")
    gcc_avg = pd.read_json(io.StringIO(gcc_avg_json), typ="series") if gcc_avg_json else None
    return intel_module.generate_intelligence_report(
        country=country, indicator=indicator,
        historical=y, forecast=fc, lower=lo, upper=hi,
        model_name=model_name, model_smape=model_smape,
        gcc_average=gcc_avg,
    )


@st.cache_data(show_spinner=False)
def _cached_trend_stats(indicator: str) -> dict:
    """Cache trend stats for all countries — recomputed only on data refresh."""
    return {c: gcc_data.get_trend_stats(c, indicator) for c in gcc_data.COUNTRIES}


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


def _scenario_section(title: str, body: str, border_color: str = "#1B4F72") -> str:
    return (
        f'<div class="scenario-section" style="border-left-color:{border_color};">'
        f'<div class="scenario-section-title">{title}</div>'
        f'{body}'
        f'</div>'
    )


def _next_step_cta(page_label: str, hint: str) -> str:
    return (
        f'<div class="next-step-cta">'
        f'<div>'
        f'<div class="next-step-label">Next Step</div>'
        f'<div class="next-step-title">{page_label} →</div>'
        f'<div style="font-size:0.78rem;opacity:0.72;margin-top:2px;">{hint}</div>'
        f'</div>'
        f'<div class="next-step-arrow">›</div>'
        f'</div>'
    )


def _empty_state_card(icon: str, title: str, body: str, tip: str) -> str:
    return (
        f'<div class="demo-guide-card">'
        f'<div style="font-size:2.5rem;line-height:1;margin-bottom:0.6rem;">{icon}</div>'
        f'<div class="demo-guide-title">{title}</div>'
        f'<div class="demo-guide-sub">{body}</div>'
        f'<div style="background:rgba(27,79,114,0.07);border-radius:8px;padding:0.65rem 0.9rem;'
        f'font-size:0.80rem;color:{_PRIMARY};font-weight:600;">'
        f'💡 {tip}'
        f'</div>'
        f'</div>'
    )


def _trust_header(score: int, conf_label: str, conf_color: str,
                  model_name: str, smape: float, tier: str) -> str:
    """Full-width trust intelligence header for the explainability page."""
    return (
        f'<div class="trust-header">'
        f'<div class="trust-score-ring">'
        f'<div class="trust-score-num">{score}</div>'
        f'<div class="trust-score-lbl">TRUST SCORE</div>'
        f'</div>'
        f'<div class="trust-divider"></div>'
        f'<div class="trust-meta">'
        f'<div class="trust-meta-title" style="color:{conf_color};">{conf_label}</div>'
        f'<div class="trust-meta-sub">'
        f'Best model: <strong>{model_name}</strong> &nbsp;·&nbsp; '
        f'Accuracy: <strong>sMAPE {smape:.1f}%</strong> &nbsp;·&nbsp; '
        f'Quality tier: <strong>{tier}</strong>'
        f'</div>'
        f'<div class="trust-badges">'
        f'<span class="trust-badge">🌍 World Bank Open Data</span>'
        f'<span class="trust-badge">🔬 Expanding-Window CV</span>'
        f'<span class="trust-badge">📊 6-Model Ensemble</span>'
        f'<span class="trust-badge">🤝 Evidence-Based</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def _confidence_card(label: str, tier: str, score: int, color: str, explanation: str) -> str:
    fill_pct = score
    return (
        f'<div class="confidence-card" style="border-top-color:{color};">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div class="confidence-tier" style="color:{color};">{tier}</div>'
        f'<div>'
        f'<div class="confidence-label" style="color:{color};">{label}</div>'
        f'<div style="font-size:0.72rem;color:#888;">Trust score: {score}/100</div>'
        f'</div>'
        f'</div>'
        f'<div class="confidence-score-bar" style="background:#EEF2F7;">'
        f'<div class="confidence-score-fill" style="width:{fill_pct}%;background:{color};height:6px;border-radius:3px;"></div>'
        f'</div>'
        f'<div class="confidence-expl">{explanation}</div>'
        f'</div>'
    )


def _driver_card(insight) -> str:
    dir_cls = {"positive": "driver-dir-pos", "negative": "driver-dir-neg"}.get(insight.direction, "driver-dir-neu")
    dir_icon = {"positive": "▲ Positive influence", "negative": "▼ Negative influence"}.get(insight.direction, "► Neutral")
    return (
        f'<div class="driver-card">'
        f'<div class="driver-rank">{insight.rank}</div>'
        f'<div class="driver-body">'
        f'<div class="driver-label">{insight.label_en}'
        f'<span class="driver-pct">{insight.influence_pct:.1f}%</span>'
        f'&nbsp;<span class="{dir_cls}">{dir_icon}</span>'
        f'</div>'
        f'<div class="driver-expl">{insight.explanation_en}</div>'
        f'</div>'
        f'</div>'
    )


def _transparency_card(title: str, body: str, border_color: str = "#1B4F72") -> str:
    return (
        f'<div class="transparency-card" style="border-left-color:{border_color};">'
        f'<div class="transparency-card-title">{title}</div>'
        f'<div class="transparency-card-body">{body}</div>'
        f'</div>'
    )


def _caveat_strip(text: str) -> str:
    return f'<div class="caveat-strip">⚠ <strong>Forecast Caveat:</strong> {text}</div>'


def _model_quality_panel(quality: dict, smape: float) -> str:
    color = quality["color"]
    badge = quality["badge"]
    tier = quality["tier"]
    rationale = quality["rationale_en"]
    stability = quality["stability_en"]
    return (
        f'<div class="model-quality-panel" style="border-left-color:{color};">'
        f'<div style="display:flex;align-items:center;margin-bottom:8px;">'
        f'<div class="model-grade-badge" style="background:{color};">{badge}</div>'
        f'<div>'
        f'<div style="font-weight:800;font-size:1.05rem;color:{color};">{tier} Model Performance</div>'
        f'<div style="font-size:0.75rem;color:#777;">sMAPE: {smape:.2f}%</div>'
        f'</div>'
        f'</div>'
        f'<div style="font-size:0.87rem;line-height:1.65;margin-bottom:6px;">{rationale}</div>'
        f'<div style="font-size:0.80rem;color:#555;font-style:italic;">{stability}</div>'
        f'</div>'
    )


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
    _hero_stats = _cached_trend_stats(_hero_ind)
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

    # ── Platform story intro ─────────────────────────────────────────────────
    st.markdown(
        f'<div class="story-panel">'
        f'<div class="story-panel-title">PLATFORM OVERVIEW — WHAT THIS PLATFORM DOES</div>'
        f'<div style="font-size:0.88rem;color:#333;line-height:1.7;">'
        f'This platform delivers <strong>AI-powered strategic intelligence</strong> for GCC youth labour-market '
        f'policy planning. It combines <strong>real World Bank data</strong>, '
        f'<strong>multi-model time-series forecasting</strong>, and <strong>AI-generated bilingual insights</strong> '
        f'to help policymakers answer: <em>Where are we? Where are we heading? What should we do?</em>'
        f'</div>'
        f'<div class="impact-stat-row">'
        f'<div class="impact-stat"><div class="impact-stat-num">6</div><div class="impact-stat-lbl">GCC Nations</div></div>'
        f'<div class="impact-stat"><div class="impact-stat-num">5</div><div class="impact-stat-lbl">WB Indicators</div></div>'
        f'<div class="impact-stat"><div class="impact-stat-num">14+</div><div class="impact-stat-lbl">Years of Data</div></div>'
        f'<div class="impact-stat"><div class="impact-stat-num">6</div><div class="impact-stat-lbl">AI Models</div></div>'
        f'<div class="impact-stat"><div class="impact-stat-num">8</div><div class="impact-stat-lbl">Scenarios</div></div>'
        f'<div class="impact-stat"><div class="impact-stat-num">2</div><div class="impact-stat-lbl">Languages</div></div>'
        f'</div>'
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
    stats = _cached_trend_stats(ind)
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        _next_step_cta(
            "🔍 Country Explorer",
            "Select a GCC nation for deep-dive historical analysis, all-indicators snapshot, and AI intelligence assessment."
        ),
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        _next_step_cta(
            "📈 Forecast Center",
            f"Run an AI forecast for {country} to generate predictive intelligence and model confidence scores."
        ),
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

    # ── Quick demo shortcut ────────────────────────────────────────────────
    st.markdown(
        '<div class="quick-demo-bar">'
        '<div style="font-size:1.1rem;">⚡</div>'
        '<div style="flex:1;">'
        '<div style="font-weight:700;font-size:0.85rem;color:#1A7A4A;">Quick Demo</div>'
        '<div style="font-size:0.77rem;color:#555;">Pre-configured: Saudi Arabia · Youth Unemployment · 3-year forecast</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    demo_col, _ = st.columns([1, 4])
    if demo_col.button("▶ Run Demo Forecast", type="primary", use_container_width=True):
        st.session_state["fc_country"] = "Saudi Arabia"
        st.session_state["fc_ind"] = "youth_unemployment_rate"
        st.session_state["fc_freq"] = "Annual"
        st.session_state["fc_horizon"] = 3
        st.session_state["fc_conf"] = 0.80
        st.session_state["_run_demo"] = True
        st.rerun()

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

    # Auto-run triggered by demo button
    run_demo = st.session_state.pop("_run_demo", False)
    trigger_run = run or run_demo

    if trigger_run or "fc_results" in st.session_state:
        if trigger_run:
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

        # Compute confidence classification for this forecast
        widths_fc = (hi - lo).values
        vol_pct = float(y.std() / y.mean() * 100) if y.mean() != 0 else 0.0
        conf_cls = intel_module.compute_confidence_classification(
            smape=backtest.best_model_smape,
            interval_width_mean=float(widths_fc.mean()),
            volatility=vol_pct,
            horizon=horizon,
        )
        quality = intel_module.compute_model_quality_tier(backtest.best_model_smape, backtest.best_model_name)
        smape_color = _SUCCESS if backtest.best_model_smape < 5 else (_WARNING if backtest.best_model_smape < 12 else _DANGER)

        fc_col1, fc_col2 = st.columns([3, 2])
        with fc_col1:
            st.markdown(
                _exec_card(
                    "🏆 MODEL SELECTION RESULT — EXPANDING-WINDOW CROSS-VALIDATION",
                    f'<strong>Best Model:</strong> {backtest.best_model_name} &nbsp;|&nbsp; '
                    f'sMAPE: <strong style="color:{smape_color}">{backtest.best_model_smape:.2f}%</strong> '
                    f'(<em>{quality["tier"]}</em>) &nbsp;|&nbsp; '
                    f'RMSE: <strong>{backtest.best_model_rmse:.3f}</strong>',
                ),
                unsafe_allow_html=True,
            )
        with fc_col2:
            st.markdown(
                _confidence_card(
                    conf_cls.label, conf_cls.tier, conf_cls.score,
                    conf_cls.color, conf_cls.explanation_en,
                ),
                unsafe_allow_html=True,
            )

        st.markdown(
            _caveat_strip(
                "Forecasts are scenario-dependent and are designed to support — not replace — "
                "evidence-based strategic decision-making. Long-term projections carry elevated "
                "uncertainty under volatile macroeconomic conditions."
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
            dl_col1, dl_col2 = st.columns(2)
            csv = fc_df.to_csv(index=False).encode()
            dl_col1.download_button(
                "⬇ Download Forecast CSV", csv,
                f"{country}_{ind}_forecast.csv", "text/csv",
                use_container_width=True,
            )
            # Executive summary text export
            exec_txt = (
                f"GCC AI Intelligence Platform — Forecast Export\n"
                f"{'='*55}\n"
                f"Country: {country}\n"
                f"Indicator: {meta['name']}\n"
                f"Best Model: {backtest.best_model_name}  |  sMAPE: {backtest.best_model_smape:.2f}%\n"
                f"Horizon: {horizon} periods  |  Confidence: {confidence*100:.0f}%\n"
                f"{'='*55}\n\n"
                f"Forecast Values:\n"
                + fc_df.to_string(index=False)
                + f"\n\n{'='*55}\n"
                f"Source: World Bank Open Data  |  Generated: GCC Intelligence Platform\n"
                f"Caveat: Forecasts support — not replace — strategic decision-making.\n"
            )
            dl_col2.download_button(
                "⬇ Download Executive Brief (TXT)", exec_txt.encode(),
                f"{country}_{ind}_executive_brief.txt", "text/plain",
                use_container_width=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            _next_step_cta(
                "🤖 AI Insights",
                f"Generate AI strategic intelligence — risk classification, bilingual analysis, and policy recommendations for {country}."
            ),
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 4 – AI Insights
# ──────────────────────────────────────────────────────────────────────────────

def page_ai_insights():
    _banner(
        "🤖 AI Decision Intelligence",
        "Ministry-grade bilingual analysis · Strategic risk engine · Policy recommendations · Comparative GCC intelligence",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.markdown(
            _empty_state_card(
                "🤖",
                "AI Decision Intelligence — Run a Forecast First",
                "This page generates ministry-grade bilingual intelligence reports including "
                "risk classification, strategic alerts, causal driver analysis, comparative GCC "
                "benchmarking, and policy recommendations — all driven by your forecast results.",
                "Navigate to 📈 Forecast Center, run a forecast, then return here for the full AI intelligence briefing.",
            ),
            unsafe_allow_html=True,
        )
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    gcc_avg = gcc_data.get_gcc_average(ind)

    with st.spinner("Generating AI intelligence report…"):
        # Serialize series to JSON strings so @st.cache_data can hash them
        report = _cached_intelligence_report(
            country=country, indicator=ind,
            y_json=y.to_json(), fc_json=fc.to_json(),
            lo_json=lo.to_json(), hi_json=hi.to_json(),
            model_name=backtest.best_model_name,
            model_smape=backtest.best_model_smape,
            gcc_avg_json=gcc_avg.to_json() if gcc_avg is not None else "",
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
        dl_a1, dl_a2 = st.columns(2)
        dl_a1.download_button(
            "⬇ تحميل التقرير العربي الكامل",
            ar_report_text.encode("utf-8"),
            f"{country}_{ind}_executive_report_ar.txt",
            "text/plain",
            use_container_width=True,
        )
        # English executive report download
        en_report = (
            f"GCC AI Intelligence Platform — Executive Intelligence Report\n"
            f"{'='*60}\n"
            f"Country: {country}  |  Indicator: {report.indicator_name}\n"
            f"Risk Profile: {report.risk_profile.label}  |  Trend: {report.trend_label}\n"
            f"Model: {report.model_name}  |  sMAPE: {report.model_smape:.2f}%\n"
            f"{'='*60}\n\n"
            f"EXECUTIVE SUMMARY\n{'-'*40}\n{report.executive_summary}\n\n"
            f"KEY INSIGHTS\n{'-'*40}\n"
            + "\n".join(f"• {i}" for i in report.key_insights)
            + f"\n\nRISK ASSESSMENT\n{'-'*40}\n"
            + "\n".join(f"• {r}" for r in report.risk_assessment)
            + f"\n\nGCC COMPARISON\n{'-'*40}\n{report.gcc_comparison}\n\n"
            f"CAUSAL INTERPRETATION\n{'-'*40}\n{report.causal_interpretation}\n\n"
            f"STRATEGIC RECOMMENDATIONS\n{'-'*40}\n"
            + "\n".join(f"• {r}" for r in report.policy_recommendations)
            + f"\n\nFORECAST OUTLOOK\n{'-'*40}\n{report.forecast_outlook}\n\n"
            f"{'='*60}\n"
            f"Source: World Bank Open Data  |  GCC AI Intelligence Platform\n"
            f"Caveat: AI-assisted analysis supports — not replaces — strategic decision-making.\n"
        )
        dl_a2.download_button(
            "⬇ Download Executive Report (EN)",
            en_report.encode("utf-8"),
            f"{country}_{ind}_executive_report_en.txt",
            "text/plain",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        _next_step_cta(
            "⚙️ Scenario Simulator",
            f"Model policy scenarios and simulate alternative futures for {country} using AI-powered impact analysis."
        ),
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 5 – Scenario Simulator
# ──────────────────────────────────────────────────────────────────────────────

def page_scenario_simulator():
    _banner(
        "⚙️ AI Strategic Planning Engine",
        "Scenario simulation · Elasticity-based impact modelling · Ministry-grade bilingual intelligence · GCC comparative analysis",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.markdown(
            _empty_state_card(
                "⚙️",
                "AI Strategic Planning Engine — Run a Forecast First",
                "The scenario simulator lets you model 8 curated strategic scenarios — from Digital "
                "Acceleration to Economic Slowdown — and see projected impacts across all 6 GCC nations. "
                "Each scenario generates a bilingual Executive Intelligence Report with risk classification, "
                "GCC rank shifts, and ministry-grade policy recommendations.",
                "Navigate to 📈 Forecast Center, run a forecast, then return here to simulate strategic scenarios.",
            ),
            unsafe_allow_html=True,
        )
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    meta = gcc_data.INDICATORS[ind]
    lib = meta["lower_is_better"]
    flag = gcc_data.COUNTRIES[country]["flag"]

    # ── Apply pending preset (must run before any widgets render) ────────────
    if "apply_preset" in st.session_state:
        pk = st.session_state.pop("apply_preset")
        if pk in scenario_module.SCENARIO_PRESETS:
            for k, v in scenario_module.SCENARIO_PRESETS[pk]["params"].items():
                st.session_state[f"scenario_{k}"] = float(v)
        st.session_state["active_preset"] = pk
        st.rerun()

    active_preset = st.session_state.get("active_preset", "")

    # ── Config strip ─────────────────────────────────────────────────────────
    st.markdown(
        _exec_card(
            "SIMULATION CONFIGURATION",
            f'{flag} <strong>{country}</strong> &nbsp;|&nbsp; '
            f'<strong>{meta["name"]}</strong> &nbsp;|&nbsp; '
            f'Model: <strong>{backtest.best_model_name}</strong> &nbsp;|&nbsp; '
            f'Horizon: <strong>{horizon} period(s)</strong> &nbsp;|&nbsp; '
            f'Confidence: <strong>{confidence*100:.0f}%</strong>',
        ),
        unsafe_allow_html=True,
    )

    # ── Scenario presets ─────────────────────────────────────────────────────
    _section("Strategic Scenario Presets")
    st.markdown(
        '<div class="data-source-strip">'
        '📋 Select a preset to instantly configure all policy levers — or adjust manually below.'
        '</div>',
        unsafe_allow_html=True,
    )

    presets_list = list(scenario_module.SCENARIO_PRESETS.items())
    for row_items in [presets_list[:4], presets_list[4:]]:
        preset_cols = st.columns(4)
        for (pk, pv), col in zip(row_items, preset_cols):
            with col:
                is_active = (pk == active_preset)
                active_cls = " active" if is_active else ""
                active_border = f'style="border-color:{pv["color"]}; background: linear-gradient(135deg, white 0%, {pv["color"]}18 100%);"' if is_active else ""
                col.markdown(
                    f'<div class="preset-card{active_cls}" {active_border}>'
                    f'<div class="preset-icon">{pv["icon"]}</div>'
                    f'<div class="preset-name">{pv["name"]}</div>'
                    f'<div class="preset-desc">{pv["description"][:55]}{"…" if len(pv["description"]) > 55 else ""}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if col.button(
                    "Apply ›" if not is_active else "✓ Active",
                    key=f"preset_btn_{pk}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["apply_preset"] = pk
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main layout: levers | results ────────────────────────────────────────
    col_params, col_results = st.columns([1, 2])

    with col_params:
        _section("Policy Levers")
        st.markdown(
            '<div style="font-size:0.76rem;color:#666;margin-bottom:0.8rem;line-height:1.5;">'
            'Adjust levers from baseline (0). Each unit = +1 percentage-point shift in that driver.'
            '</div>',
            unsafe_allow_html=True,
        )
        param_configs = scenario_module.get_param_config()
        params: dict = {}
        for p in param_configs:
            val = st.slider(
                p["label"],
                min_value=float(p["min"]),
                max_value=float(p["max"]),
                value=float(st.session_state.get(f"scenario_{p['key']}", p["default"])),
                step=float(p["step"]),
                key=f"scenario_{p['key']}",
                help=f"العربية: {p['label_ar']}",
            )
            params[p["key"]] = val

        st.markdown("<br>", unsafe_allow_html=True)
        if any(abs(v) > 0.01 for v in params.values()):
            if st.button("↺ Reset to Baseline", use_container_width=True):
                st.session_state["apply_preset"] = "baseline"
                st.rerun()

    # ── Compute scenario result & intelligence ────────────────────────────────
    result = scenario_module.apply_scenario(
        baseline_forecast=fc, baseline_lower=lo, baseline_upper=hi,
        params=params, indicator=ind, country=country,
    )
    intel = scenario_module.generate_scenario_intelligence(
        country=country, indicator=ind,
        result=result, params=params,
        preset_name=active_preset,
    )

    with col_results:
        # ── Scenario classification banner ───────────────────────────────────
        sev = intel.severity
        sev_icons = {
            "opportunity": "✅", "risk": "🚨", "warning": "⚠️",
            "pressure": "📊", "neutral": "📋",
        }
        rank_text = ""
        if intel.gcc_ranking_shift > 0:
            rank_text = f" &nbsp;|&nbsp; 📈 GCC Rank +{intel.gcc_ranking_shift}"
        elif intel.gcc_ranking_shift < 0:
            rank_text = f" &nbsp;|&nbsp; 📉 GCC Rank {intel.gcc_ranking_shift}"
        st.markdown(
            f'<div class="scenario-intel-banner {sev}">'
            f'<div class="scenario-intel-icon">{sev_icons.get(sev, "📋")}</div>'
            f'<div>'
            f'<div class="scenario-intel-label" style="color:{intel.badge_color};">'
            f'{intel.scenario_label}</div>'
            f'<div class="scenario-intel-sub">'
            f'{intel.scenario_label_ar}{rank_text}'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── 4 impact KPI cards ───────────────────────────────────────────────
        impact_good = result.optimistic
        arrow = "↓" if result.total_impact_pp < 0 else "↑"
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(_kpi_card(
            "Baseline (End)",
            f"{result.baseline_forecast.iloc[-1]:.2f}%",
        ), unsafe_allow_html=True)
        m2.markdown(_kpi_card(
            "Scenario (End)",
            f"{result.scenario_forecast.iloc[-1]:.2f}%",
            f"{arrow} {abs(result.total_impact_pp):.2f}pp", impact_good,
        ), unsafe_allow_html=True)
        m3.markdown(_kpi_card(
            "Delta (pp)",
            f"{result.total_impact_pp:+.2f}pp",
            "Favourable" if impact_good else "Adverse", impact_good,
        ), unsafe_allow_html=True)
        m4.markdown(_kpi_card(
            "Relative Change",
            f"{result.total_impact_pct:+.1f}%",
            "vs Baseline", impact_good,
        ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Full-width: chart + waterfall side by side ────────────────────────────
    chart_col, waterfall_col = st.columns([3, 2])

    with chart_col:
        _section("Baseline vs Scenario Forecast")
        sc_color = _SUCCESS if impact_good else _DANGER
        fig = go.Figure(layout=_plotly_base(f"{flag} {country} — {meta['name']} Scenario"))
        fig.add_trace(go.Scatter(
            x=y.index, y=y.values, name="Historical",
            line=dict(color=_COUNTRY_COLORS.get(country, _PRIMARY), width=2.2),
            mode="lines+markers", marker=dict(size=4),
        ))
        fig.add_trace(go.Scatter(
            x=result.baseline_forecast.index, y=result.baseline_forecast.values,
            name="Baseline",
            line=dict(color="#9E9E9E", width=2, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=list(result.baseline_upper.index) + list(result.baseline_lower.index[::-1]),
            y=list(result.baseline_upper.values) + list(result.baseline_lower.values[::-1]),
            fill="toself", fillcolor="rgba(150,150,150,0.10)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=result.scenario_forecast.index, y=result.scenario_forecast.values,
            name="Scenario",
            line=dict(color=sc_color, width=2.8),
            mode="lines+markers", marker=dict(size=7, symbol="diamond"),
        ))
        fig.add_trace(go.Scatter(
            x=list(result.scenario_upper.index) + list(result.scenario_lower.index[::-1]),
            y=list(result.scenario_upper.values) + list(result.scenario_lower.values[::-1]),
            fill="toself",
            fillcolor=f"rgba({'26,122,74' if impact_good else '169,50,38'},0.12)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        ))
        fig.add_vline(x=str(y.index[-1]), line_dash="dot", line_color="#AAAAAA", opacity=0.6)
        fig.update_layout(
            yaxis_title=f"{meta['name']} ({meta['unit']})",
            hovermode="x unified", height=380,
            legend=dict(orientation="h", y=-0.15, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with waterfall_col:
        _section("Driver Contribution Breakdown")
        active_drivers = {k: v for k, v in result.driver_contributions.items() if abs(v) > 1e-4}
        if active_drivers:
            d_labels = [scenario_module._PARAM_LABELS.get(k, k) for k in active_drivers]
            d_vals = list(active_drivers.values())
            d_colors = [
                _SUCCESS if ((v < 0 and lib) or (v > 0 and not lib)) else _DANGER
                for v in d_vals
            ]
            fig_d = go.Figure(layout=_plotly_base())
            fig_d.add_trace(go.Bar(
                x=d_vals, y=d_labels,
                orientation="h",
                marker_color=d_colors,
                text=[f"{v:+.3f}pp" for v in d_vals],
                textposition="outside",
            ))
            fig_d.add_vline(x=0, line_color="gray", line_width=1)
            fig_d.update_layout(
                xaxis_title="Impact (pp)", height=380,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=140, r=60, t=20, b=40),
            )
            st.plotly_chart(fig_d, use_container_width=True)
        else:
            st.markdown(
                _alert_card("No Active Drivers", "All policy levers are at baseline (0pp).", "info"),
                unsafe_allow_html=True,
            )

    # ── Executive Intelligence Report ─────────────────────────────────────────
    _section("Executive Scenario Intelligence Report")
    tab_en, tab_ar = st.tabs(["🇬🇧 Strategic Intelligence Report", "🇸🇦 التقرير الاستراتيجي"])

    with tab_en:
        s_badge = _badge(intel.scenario_label, intel.severity)
        opt_badge = _badge("Favourable Outcome" if impact_good else "Adverse Outcome",
                           "low" if impact_good else "high")
        st.markdown(f"{s_badge} {opt_badge}", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        en_c1, en_c2 = st.columns(2)
        with en_c1:
            st.markdown(
                _scenario_section(
                    "STRATEGIC OUTLOOK",
                    intel.strategic_outlook_en,
                    border_color=intel.badge_color,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                _scenario_section(
                    "LABOR MARKET IMPLICATIONS",
                    intel.labor_implications_en,
                    border_color=_SUCCESS if impact_good else _DANGER,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                _scenario_section(
                    "GCC COMPARATIVE ANALYSIS",
                    intel.gcc_comparative_en,
                    border_color=_PRIMARY,
                ),
                unsafe_allow_html=True,
            )
        with en_c2:
            st.markdown(
                _scenario_section(
                    "KEY ECONOMIC IMPACT",
                    intel.key_impact_en,
                    border_color=_GOLD,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                _scenario_section(
                    "RISK ASSESSMENT",
                    intel.risk_assessment_en,
                    border_color=_WARNING if impact_good else _DANGER,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                _scenario_section(
                    "RECOMMENDED STRATEGIC ACTIONS",
                    "<br>".join(f"✦ {r}" for r in intel.recommended_actions_en),
                    border_color=_SUCCESS,
                ),
                unsafe_allow_html=True,
            )

    with tab_ar:
        s_badge_ar = _badge(intel.scenario_label_ar, intel.severity)
        st.markdown(s_badge_ar, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        ar_c1, ar_c2 = st.columns(2)
        def _ar_sc(title_ar, body_ar, color="#1B4F72"):
            st.markdown(
                f'<div class="arabic-block" style="border-right-color:{color}; margin:0.45rem 0;">'
                f'<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.7px;'
                f'color:#C39B4E;font-weight:700;margin-bottom:0.4rem;">{title_ar}</div>'
                f'{body_ar}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with ar_c1:
            _ar_sc("النظرة الاستراتيجية", intel.strategic_outlook_ar, intel.badge_color)
            _ar_sc("الانعكاسات على سوق العمل", intel.labor_implications_ar,
                   _SUCCESS if impact_good else _DANGER)
            _ar_sc("المقارنة الخليجية", intel.gcc_comparative_ar, _PRIMARY)
        with ar_c2:
            _ar_sc("الأثر الاقتصادي الرئيسي", intel.key_impact_ar, _GOLD)
            _ar_sc("تقييم المخاطر", intel.risk_assessment_ar,
                   _WARNING if impact_good else _DANGER)
            _ar_sc(
                "التوصيات الاستراتيجية",
                "<br>".join(f"✦ {r}" for r in intel.recommended_actions_ar),
                _SUCCESS,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        _next_step_cta(
            "🔬 AI Transparency Center",
            "Understand how the AI generates forecasts — model reliability, driver intelligence, and responsible AI methodology."
        ),
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 6 – Explainability
# ──────────────────────────────────────────────────────────────────────────────

def page_explainability():
    _banner(
        "🔬 AI Transparency & Explainability Center",
        "Trustworthy AI · Transparent forecasting · Model reliability · Driver intelligence · Responsible decision support",
    )

    if "fc_results" not in st.session_state or "fc_meta" not in st.session_state:
        st.markdown(
            _empty_state_card(
                "🔬",
                "AI Transparency Center — Run a Forecast First",
                "This centre provides: Trust Score (0–100), Forecast Confidence Classification, "
                "Ranked Driver Intelligence, Model Quality Assessment, Time-Series Decomposition, "
                "and a complete Responsible AI Methodology guide.",
                "Navigate to 📈 Forecast Center, run a forecast, then return here for full AI explainability diagnostics.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        _section("AI Transparency — Always Available")
        _section("AI Transparency — Always Available")
        _render_ai_transparency_tab()
        return

    y, fc, lo, hi, backtest, best_model = st.session_state["fc_results"]
    country, ind, freq_code, horizon, confidence = st.session_state["fc_meta"]
    meta = gcc_data.INDICATORS[ind]

    # ── Pre-compute shared intelligence objects ────────────────────────────────
    widths = (hi - lo).values
    vol_pct = float(y.std() / y.mean() * 100) if y.mean() != 0 else 0.0
    conf_cls = intel_module.compute_confidence_classification(
        smape=backtest.best_model_smape,
        interval_width_mean=float(widths.mean()),
        volatility=vol_pct,
        horizon=horizon,
    )
    quality = intel_module.compute_model_quality_tier(backtest.best_model_smape, backtest.best_model_name)

    slope = float(np.polyfit(range(len(y)), y.values, 1)[0])
    lib = meta.get("lower_is_better", True)
    improving = (slope < 0) if lib else (slope > 0)

    # ── Trust header ──────────────────────────────────────────────────────────
    st.markdown(
        _trust_header(
            score=conf_cls.score,
            conf_label=conf_cls.label,
            conf_color=conf_cls.color,
            model_name=backtest.best_model_name,
            smape=backtest.best_model_smape,
            tier=quality["tier"],
        ),
        unsafe_allow_html=True,
    )

    tab_model, tab_driver, tab_conf, tab_decomp, tab_transparency = st.tabs([
        "📊 Model Reliability",
        "🔑 Driver Intelligence",
        "🔭 Forecast Confidence",
        "📉 Decomposition",
        "🛡️ AI Transparency",
    ])

    # ── Tab 1: Model Reliability ──────────────────────────────────────────────
    with tab_model:
        _section("Model Quality Assessment")
        st.markdown(_model_quality_panel(quality, backtest.best_model_smape), unsafe_allow_html=True)

        st.markdown(
            _exec_card(
                "SELECTION METHODOLOGY — EXPANDING-WINDOW CROSS-VALIDATION",
                "Six candidate models (Naïve, Seasonal Naïve, Moving Average, Drift, SARIMAX, LightGBM) were evaluated "
                "using <strong>expanding-window cross-validation</strong>. Each fold adds historical data while holding out "
                "a fixed future period for testing. <strong>sMAPE</strong> (Symmetric Mean Absolute Percentage Error) "
                "is the primary selection metric — it is robust to near-zero values and symmetric around errors. "
                "The model with the lowest sMAPE is selected as the best model for this configuration.",
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
            fig = go.Figure(layout=_plotly_base("Model Comparison — sMAPE (lower = better)"))
            bar_c = [_GOLD if m == backtest.best_model_name else "#AABBCC" for m in comp["model"]]
            fig.add_trace(go.Bar(
                x=comp["model"], y=comp["smape"],
                marker_color=bar_c,
                text=[f"{v:.2f}%" for v in comp["smape"]],
                textposition="outside",
            ))
            fig.update_layout(yaxis_title="sMAPE (%)", height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _section("Metric Definitions")
        m1, m2, m3, m4 = st.columns(4)
        for col, name, desc in [
            (m1, "MAE", "Mean absolute difference between forecast and actual values. Easy to interpret but sensitive to scale."),
            (m2, "RMSE", "Root mean squared error — penalises large errors more heavily. Good for detecting outlier sensitivity."),
            (m3, "MAPE", "Mean absolute percentage error — intuitive but undefined near zero values."),
            (m4, "sMAPE", "Symmetric MAPE — the primary competition-grade metric. Robust to near-zero values and directional errors."),
        ]:
            col.markdown(
                f'<div class="insight-card"><strong>{name}</strong><br>'
                f'<span style="font-size:0.80rem;color:#555;">{desc}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            _caveat_strip(
                f"Model accuracy (sMAPE {backtest.best_model_smape:.1f}%) was measured on historical holdout data. "
                "Future performance may differ under structural breaks, geopolitical shocks, or unprecedented macroeconomic shifts."
            ),
            unsafe_allow_html=True,
        )

    # ── Tab 2: Driver Intelligence ─────────────────────────────────────────────
    with tab_driver:
        _section("Feature Driver Intelligence")
        if hasattr(best_model, "get_feature_importance"):
            try:
                fi_raw = best_model.get_feature_importance()
                driver_insights = intel_module.interpret_feature_importance(fi_raw, ind, improving)

                if driver_insights:
                    st.markdown(
                        _exec_card(
                            "EXECUTIVE DRIVER SUMMARY",
                            f"The <strong>{backtest.best_model_name}</strong> model's predictions for "
                            f"<strong>{country} — {meta['name']}</strong> are driven by the following ranked factors. "
                            f"The dominant driver accounts for "
                            f"<strong>{driver_insights[0].influence_pct:.1f}%</strong> of predictive influence. "
                            f"{'Autocorrelation signals dominate, reflecting strong historical persistence.' if 'lag' in driver_insights[0].feature_name else 'Trend momentum features dominate, reflecting sustained structural shifts.'}"
                        ),
                        unsafe_allow_html=True,
                    )

                    # Ranked driver cards
                    col_left, col_right = st.columns(2)
                    for i, insight in enumerate(driver_insights):
                        target_col = col_left if i % 2 == 0 else col_right
                        target_col.markdown(_driver_card(insight), unsafe_allow_html=True)

                    # Importance chart alongside
                    st.markdown("<br>", unsafe_allow_html=True)
                    _section("Feature Importance Chart")
                    fi_top = fi_raw.head(12)
                    total_imp = fi_top.sum()
                    pct_vals = (fi_top / total_imp * 100).values[::-1] if total_imp > 0 else fi_top.values[::-1]
                    feat_labels = fi_top.index.tolist()[::-1]

                    # Map raw names to readable labels
                    readable = []
                    for fn in feat_labels:
                        narr = intel_module._FEATURE_NARRATIVE.get(fn)
                        readable.append(narr[0] if narr else fn.replace("_", " ").title())

                    colors_fi = [_GOLD if "lag_1" in fn or "roll_mean" in fn else _PRIMARY for fn in feat_labels]
                    fig_fi = go.Figure(layout=_plotly_base("Ranked Feature Drivers (% of predictive influence)"))
                    fig_fi.add_trace(go.Bar(
                        x=pct_vals, y=readable,
                        orientation="h", marker_color=colors_fi,
                        text=[f"{v:.1f}%" for v in pct_vals],
                        textposition="outside",
                    ))
                    fig_fi.update_layout(xaxis_title="Influence (%)", height=max(300, len(fi_top) * 28 + 60))
                    st.plotly_chart(fig_fi, use_container_width=True)

                else:
                    st.info("Feature importance details not available for this model configuration.")

            except Exception as e:
                st.info(f"Driver intelligence requires the LightGBM model to be selected. Current model: **{best_model.name}**.")
        else:
            st.markdown(
                _exec_card(
                    "DRIVER INTELLIGENCE — MODEL NOTE",
                    f"Detailed feature driver intelligence is available when <strong>LightGBM</strong> is selected as the best model. "
                    f"The current best model is <strong>{best_model.name}</strong>. "
                    "For driver-level interpretability, re-run the forecast on a dataset where LightGBM achieves the lowest sMAPE.",
                ),
                unsafe_allow_html=True,
            )
            # Show macro driver context instead
            _section("Macro-Economic Driver Context")
            from src.intelligence import _COUNTRY_CONTEXT
            ctx = _COUNTRY_CONTEXT.get(country, {})
            drivers_en = ctx.get("causal_drivers_en", [])
            if drivers_en:
                for driver in drivers_en:
                    st.markdown(_insight_html(driver), unsafe_allow_html=True)

    # ── Tab 3: Forecast Confidence ─────────────────────────────────────────────
    with tab_conf:
        _section("Forecast Confidence Classification")

        c_left, c_right = st.columns([2, 3])
        with c_left:
            st.markdown(
                _confidence_card(
                    conf_cls.label, conf_cls.tier, conf_cls.score,
                    conf_cls.color, conf_cls.explanation_en,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="arabic-block" style="font-size:0.88rem;">'
                f'<strong>تصنيف الثقة:</strong> {conf_cls.label_ar}<br><br>'
                f'{conf_cls.explanation_ar}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_right:
            _section("Prediction Interval Analysis")
            horizon_labels = [f"H+{i+1}" for i in range(len(widths))]
            colors_ci = [conf_cls.color] * len(widths)
            fig_ci = go.Figure(layout=_plotly_base("Prediction Interval Width by Forecast Horizon"))
            fig_ci.add_trace(go.Bar(
                x=horizon_labels, y=widths,
                marker_color=colors_ci,
                text=[f"{w:.2f}pp" for w in widths],
                textposition="outside",
            ))
            fig_ci.update_layout(yaxis_title="Interval Width (pp)", height=300)
            st.plotly_chart(fig_ci, use_container_width=True)

            st.markdown(
                _exec_card(
                    "🔭 UNCERTAINTY INTERPRETATION",
                    f'The <strong>{confidence*100:.0f}% prediction interval</strong> means that if model assumptions hold, '
                    f'{confidence*100:.0f}% of actual future values should fall within the shaded band. '
                    f'Wider intervals at longer horizons reflect <strong>compounding uncertainty</strong> — a fundamental '
                    f'property of all time-series forecasting. Average interval width: '
                    f'<strong>{widths.mean():.2f} percentage points</strong>. '
                    f'{"Intervals are narrow, indicating high forecast precision." if widths.mean() < 2 else "Intervals suggest meaningful uncertainty — scenarios should be evaluated in parallel."}'
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        _section("Confidence Tier Guide")
        tier_cols = st.columns(5)
        tier_guide = [
            ("A", "High Confidence",     "#1A7A4A", "sMAPE < 5%"),
            ("B", "Moderate Confidence", "#1B4F72", "sMAPE 5–12%"),
            ("C", "Elevated Uncertainty","#C07820",  "sMAPE 12–20%"),
            ("D", "Volatile Outlook",    "#A93226",  "sMAPE 20–30%"),
            ("E", "Unstable Forecast",   "#7B241C",  "sMAPE > 30%"),
        ]
        for col_t, (t, lbl, clr, crit) in zip(tier_cols, tier_guide):
            active = "font-weight:900;box-shadow:0 0 0 2px " + clr if t == conf_cls.tier else "opacity:0.55"
            col_t.markdown(
                f'<div style="text-align:center;padding:0.7rem;background:white;border-radius:10px;'
                f'border:2px solid {clr};{active};">'
                f'<div style="font-size:1.6rem;font-weight:900;color:{clr};">{t}</div>'
                f'<div style="font-size:0.75rem;font-weight:700;color:{clr};margin:3px 0;">{lbl}</div>'
                f'<div style="font-size:0.67rem;color:#888;">{crit}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            _caveat_strip(
                "Confidence classification is based on cross-validation accuracy, prediction interval width, "
                "data volatility, and forecast horizon. It is a statistical signal — not a guarantee of future accuracy."
            ),
            unsafe_allow_html=True,
        )

    # ── Tab 4: Decomposition ───────────────────────────────────────────────────
    with tab_decomp:
        _section("Time-Series Decomposition")
        st.markdown(
            _exec_card(
                "WHAT IS DECOMPOSITION?",
                "Time-series decomposition separates the observed data into three interpretable components: "
                "<strong>Trend</strong> (the long-run direction), <strong>Seasonal</strong> (recurring patterns "
                "within each year), and <strong>Residual</strong> (unexplained variation). "
                "Understanding these components helps policymakers distinguish between structural shifts and cyclical noise.",
            ),
            unsafe_allow_html=True,
        )
        from src.explain import decompose_series
        with st.spinner("Decomposing series…"):
            try:
                decomp = decompose_series(y, freq=freq_code)
                d1, d2, d3 = st.columns(3)
                d1.metric("Trend Direction", decomp.trend_direction.capitalize())
                d2.metric("Seasonality Strength", f"{decomp.seasonality_strength:.0%}")
                d3.metric("Data Points", len(y))

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

                # Decomposition narrative
                trend_narrative = (
                    "The trend component shows a clear long-run trajectory — this is the primary signal "
                    "for strategic planning purposes."
                    if abs(slope) > 0.2 else
                    "The trend component is broadly flat, indicating structural stability in the medium term."
                )
                st.markdown(
                    _exec_card("DECOMPOSITION INTERPRETATION", trend_narrative),
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.warning(f"Decomposition not available: {e}")

    # ── Tab 5: AI Transparency ────────────────────────────────────────────────
    with tab_transparency:
        _render_ai_transparency_tab(
            country=country, ind=ind, meta=meta,
            model_name=backtest.best_model_name,
            smape=backtest.best_model_smape,
            horizon=horizon,
            conf_label=conf_cls.label,
        )


def _render_ai_transparency_tab(
    country: str = "", ind: str = "", meta: dict = None,
    model_name: str = "", smape: float = 0.0,
    horizon: int = 0, conf_label: str = "",
) -> None:
    """Render the Responsible AI & Transparency section."""
    _section("Responsible AI & Methodology")

    t1, t2 = st.columns(2)
    with t1:
        st.markdown(
            _transparency_card(
                "DATA SOURCES & PROVENANCE",
                "<strong>Primary Source:</strong> World Bank Open Data API v2 (data.worldbank.org)<br>"
                "<strong>Coverage:</strong> 6 GCC nations · 5 labour-market indicators · 2010–2024<br>"
                "<strong>Indicators:</strong> Youth Unemployment Rate, GDP Growth, Inflation, "
                "Population Growth, Internet Usage<br>"
                "<strong>Update Frequency:</strong> Annual (World Bank publication cycle)<br>"
                "<strong>Data Integrity:</strong> Missing values handled via linear interpolation; "
                "outliers preserved to maintain structural integrity.",
                "#1B4F72",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _transparency_card(
                "FORECASTING METHODOLOGY",
                "<strong>Approach:</strong> Multi-model ensemble selection via expanding-window cross-validation<br>"
                "<strong>Candidate Models:</strong> Naïve, Seasonal Naïve, Moving Average, Drift, "
                "SARIMAX (auto-order), LightGBM (gradient boosting)<br>"
                "<strong>Selection Criterion:</strong> Lowest sMAPE on holdout folds<br>"
                "<strong>Prediction Intervals:</strong> Computed from model residual standard deviation, "
                f"adjusted to the selected confidence level ({int(confidence * 100) if confidence else 80}%)<br>"
                "<strong>Elasticity Scenarios:</strong> Applied as linear ramps over the forecast horizon.",
                "#1A7A4A",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _transparency_card(
                "AI INTERPRETATION GUIDANCE",
                "This platform generates <strong>AI-assisted intelligence narratives</strong> — "
                "structured, template-based interpretations grounded in statistical evidence and "
                "GCC domain knowledge. They are designed to <em>support</em> policymaker judgment, "
                "not replace it.<br><br>"
                "Risk classifications, strategic alerts, and scenario intelligence are derived from "
                "data patterns and contextual heuristics. They represent probabilistic assessments, "
                "not deterministic predictions.",
                "#C07820",
            ),
            unsafe_allow_html=True,
        )

    with t2:
        st.markdown(
            _transparency_card(
                "FORECAST LIMITATIONS",
                "<ul style='margin:0;padding-left:1.2rem;font-size:0.86rem;line-height:1.8;'>"
                "<li>Forecasts are <strong>scenario-dependent</strong> — they reflect statistical patterns in historical data.</li>"
                "<li>Long-term projections (≥3 years) carry <strong>elevated uncertainty</strong> under volatile macroeconomic conditions.</li>"
                "<li>External shocks — geopolitical disruptions, oil price crises, pandemics — are <strong>not modelled</strong> and may significantly alter outcomes.</li>"
                "<li>Annual data series (2010–2024) limit the number of training observations, which may affect model precision.</li>"
                "<li>Structural breaks (e.g., post-2020 COVID recovery) may reduce the predictive validity of historical patterns.</li>"
                "<li>Country-level results should be interpreted alongside <strong>national policy context</strong> and expert judgement.</li>"
                "</ul>",
                "#A93226",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _transparency_card(
                "RESPONSIBLE DECISION SUPPORT",
                "This platform is designed in accordance with principles of <strong>responsible AI for public-sector use</strong>:<br><br>"
                "<strong>Transparency:</strong> All modelling choices and data sources are documented and accessible.<br>"
                "<strong>Interpretability:</strong> Forecasts include confidence classifications, driver narratives, "
                "and plain-language explanations accessible to non-technical policymakers.<br>"
                "<strong>Accountability:</strong> Forecast limitations are prominently communicated. "
                "The platform encourages scenario testing and sensitivity analysis.<br>"
                "<strong>Human Oversight:</strong> AI narratives are advisory. Strategic decisions must remain "
                "the responsibility of qualified domain experts and government officials.<br>"
                "<strong>Evidence-Based:</strong> All intelligence is grounded in verified World Bank statistical data.",
                "#6C3483",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _transparency_card(
                "BILINGUAL REPORTING STANDARD",
                "Executive reports are generated in both <strong>English</strong> and <strong>Arabic</strong> "
                "to serve GCC multilingual policy environments. Arabic narratives follow RTL formatting standards "
                "and use formal Modern Standard Arabic (MSA) appropriate for government and ministerial audiences.<br><br>"
                "Translations are <strong>template-based and data-driven</strong>, ensuring consistency "
                "between the English and Arabic intelligence outputs.",
                "#1B4F72",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _section("Forecast Caveats")
    caveats = [
        "Forecasts are scenario-dependent and are designed to <strong>support — not replace</strong> evidence-based strategic decision-making.",
        "Long-term projections contain <strong>elevated uncertainty</strong> under volatile macroeconomic or geopolitical conditions.",
        "External shocks (oil price volatility, regional conflicts, global recessions) are not captured by the statistical models.",
        "Confidence intervals represent <strong>statistical bounds</strong>, not guaranteed outcome ranges.",
        "Model performance is measured on historical data; future structural changes may reduce forecast accuracy.",
        "GCC comparative analysis uses the most recent available World Bank data, which may not reflect the latest policy changes.",
    ]
    for caveat in caveats:
        st.markdown(_caveat_strip(caveat), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:rgba(27,79,114,0.06);border-radius:12px;padding:1.2rem 1.5rem;'
        f'border:1px solid rgba(27,79,114,0.12);font-size:0.80rem;color:#444;line-height:1.7;">'
        f'<strong style="color:{_PRIMARY};">Platform Governance Statement</strong><br>'
        f'The GCC Youth Employment Intelligence Platform was developed to support evidence-based policymaking '
        f'through transparent and interpretable AI-assisted analytics. All outputs are grounded in verified '
        f'World Bank Open Data and are subject to the limitations inherent in time-series statistical modelling. '
        f'This platform does not constitute financial, legal, or policy advice. Strategic decisions should '
        f'incorporate additional expert judgment, domain knowledge, and current-events intelligence beyond '
        f'what historical data patterns can capture.'
        f'</div>',
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

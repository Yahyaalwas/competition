# GCC AI Intelligence Platform

> **An AI-powered strategic intelligence platform for GCC youth employment policy planning — delivering real-time forecasting, bilingual executive reports, and scenario simulation for Gulf decision-makers.**

---

## What This Platform Does

The GCC AI Intelligence Platform transforms World Bank employment data into actionable policy intelligence for Gulf Cooperation Council governments. It answers three fundamental questions for policymakers:

- **Where are we?** — Real-time GCC regional dashboard with AI risk classification
- **Where are we heading?** — Multi-model AI forecasting with confidence scoring
- **What should we do?** — Scenario simulation + bilingual ministerial recommendations

---

## Platform Capabilities

| Capability | Description |
|---|---|
| 🌍 **GCC Regional Intelligence** | Six-country comparative dashboard, YoY heatmaps, AI risk badges |
| 🔍 **Country Deep-Dive** | Per-nation historical analysis, all-indicators snapshot, strategic alerts |
| 📈 **AI Forecast Engine** | 6-model ensemble with expanding-window cross-validation, prediction intervals |
| 🤖 **AI Decision Intelligence** | Bilingual (EN/AR) executive reports — risk, recommendations, outlook |
| ⚙️ **Scenario Simulator** | 8 curated policy scenarios with GCC-wide impact and rank analysis |
| 🔬 **Explainability Center** | Trust scoring, driver intelligence, confidence tiers, responsible AI |

**Data:** World Bank Open Data API v2 · 6 GCC nations · 5 indicators · 2010–2024  
**Languages:** English + Arabic (RTL formatted, ministry-grade)  
**Models:** Naïve · Seasonal Naïve · Moving Average · Drift · SARIMAX · LightGBM

---

## Quickstart

### Prerequisites

- Python 3.10, 3.11, or 3.12
- pip (comes with Python)

### Option A — One-Click Launch

```bash
# macOS / Linux
./run_app.sh

# Windows
run_app.bat
```

### Option B — Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Validate setup (optional but recommended before demos)
python scripts/validate_setup.py

# 3. Launch
streamlit run app.py
```

The platform opens at **http://localhost:8501** and works fully offline — no internet required after first run.

---

## Demo Flow (Recommended for Judges)

Follow this 6-step path for the most impactful demonstration:

```
Step 1  🌍 GCC Overview          Regional intelligence hero + AI risk classification
Step 2  🔍 Country Explorer      Saudi Arabia deep-dive: KPIs, trends, strategic alerts
Step 3  📈 Forecast Center       ▶ Run Demo Forecast (one click) — watch 6-model AI selection
Step 4  🤖 AI Insights           Read the bilingual executive intelligence report
Step 5  ⚙️ Scenario Simulator    Apply "Reform Expansion" preset — see GCC rank impact
Step 6  🔬 Explainability        View trust score, driver intelligence, AI transparency
```

> **Tip:** Use the "▶ Run Demo Forecast" button in the Forecast Center for a pre-configured Saudi Arabia demonstration that requires zero setup.

---

## Dashboard Pages

### 🌍 GCC Overview
Six-country regional intelligence hub. Displays live KPI cards, multi-country trend chart, country rankings, YoY change heatmap, and an AI Regional Intelligence Snapshot with real-time risk badges for every GCC nation.

### 🔍 Country Explorer
Single-country deep-dive. Historical trend vs GCC average, all-indicators snapshot table, YoY change analysis, and a full AI Intelligence Assessment panel with risk classification and strategic alerts.

### 📈 AI Forecast Center
Multi-model forecasting with automatic selection. Choose country, indicator, frequency (Annual/Monthly), and horizon. The engine runs expanding-window cross-validation across 6 models, selects the best by sMAPE, and produces probabilistic prediction intervals. A **Quick Demo** shortcut pre-configures Saudi Arabia + Youth Unemployment in one click.

### 🤖 AI Decision Intelligence
AI-generated bilingual executive reports driven by forecast outputs. Covers: strategic risk profile, executive summary, key insights, GCC comparative analysis, causal driver interpretation, risk assessment, policy recommendations, and forecast outlook. Download as English or Arabic executive reports.

### ⚙️ AI Strategic Planning Engine
8 curated strategic scenario presets (Baseline, Digital Acceleration, Economic Slowdown, Inflation Stress, Reform Expansion, Youth Employment Recovery, Population Surge, High Growth GCC). Each scenario generates a bilingual Executive Intelligence Report with GCC-wide rank simulation.

### 🔬 AI Transparency & Explainability Center
Trust Intelligence Header with 0–100 trust score. Five tabs: Model Reliability (quality tier + CV comparison), Driver Intelligence (ranked feature narratives), Forecast Confidence (5-tier classification + interval analysis), Decomposition (trend/seasonal/residual), and AI Transparency (full responsible AI methodology guide).

---

## AI Indicators

| Indicator | World Bank Code | Direction |
|---|---|---|
| Youth Unemployment Rate (%) | SL.UEM.1524.ZS | Lower = Better |
| GDP Growth Rate (%) | NY.GDP.MKTP.KD.ZG | Higher = Better |
| Inflation Rate — CPI (%) | FP.CPI.TOTL.ZG | Lower = Better |
| Population Growth Rate (%) | SP.POP.GROW | Context-dependent |
| Internet Users (% of Population) | IT.NET.USER.ZS | Higher = Better |

---

## Forecast Confidence System

| Tier | Label | sMAPE Range | Meaning |
|---|---|---|---|
| **A** | High Confidence | < 5% | Suitable for strategic planning |
| **B** | Moderate Confidence | 5–12% | Directionally reliable |
| **C** | Elevated Uncertainty | 12–20% | Use with scenario analysis |
| **D** | Volatile Outlook | 20–30% | Indicative only |
| **E** | Unstable Forecast | > 30% | Validate against domain expertise |

---

## Scenario Presets

| Preset | Type | Description |
|---|---|---|
| 📊 Baseline Outlook | Neutral | No policy changes applied |
| ⚡ Digital Acceleration | Opportunity | High digital + GDP growth |
| 📉 Economic Slowdown | Risk | GDP contraction scenario |
| 🔥 Inflation Stress Test | Warning | Inflation surge + GDP drag |
| 🏗 Reform Expansion | Opportunity | Labour reform + education investment |
| 🌱 Youth Employment Recovery | Opportunity | Targeted youth employment programme |
| 👥 Population Surge | Pressure | Demographic pressure without growth |
| 🚀 High Growth GCC | Opportunity | Full acceleration scenario |

---

## Export Capabilities

| Export | Format | Available From |
|---|---|---|
| Forecast Data | CSV | Forecast Center → Forecast Table |
| Executive Brief (EN) | TXT | Forecast Center → Forecast Table |
| AI Intelligence Report (EN) | TXT | AI Insights → Arabic tab |
| AI Intelligence Report (AR) | TXT | AI Insights → Arabic tab |

All exports use descriptive filenames (`{country}_{indicator}_{type}.{ext}`).

---

## Architecture

```
competition/
├── app.py                      # Streamlit dashboard (6 pages, ~2,700 lines)
├── requirements.txt            # Python dependencies
├── run_app.sh                  # macOS/Linux one-click launcher
├── run_app.bat                 # Windows one-click launcher
├── config.yaml                 # Model pipeline configuration
├── .streamlit/
│   └── config.toml             # Theme and server settings
├── src/
│   ├── gcc_data.py             # GCC dataset & World Bank integration
│   ├── intelligence.py         # AI intelligence engine (bilingual EN/AR)
│   ├── scenario.py             # Elasticity-based scenario simulation
│   ├── evaluate.py             # Expanding-window cross-validation
│   ├── explain.py              # Decomposition & explainability
│   ├── data.py                 # Data loading & cleaning
│   ├── wb_data.py              # World Bank API client
│   ├── main.py                 # CLI pipeline entry point
│   └── models/
│       ├── baselines.py        # Naïve, Seasonal Naïve, Moving Average, Drift
│       ├── arima_model.py      # SARIMAX with AIC auto-order selection
│       └── ml_model.py         # LightGBM with quantile regression
├── data/
│   └── processed/              # Pre-seeded World Bank cache (offline-ready)
│       ├── youth_unemployment_rate.csv
│       ├── gdp_growth.csv
│       ├── inflation.csv
│       ├── population_growth.csv
│       ├── internet_usage.csv
│       └── metadata.json
└── scripts/
    ├── validate_setup.py       # Pre-demo setup validation
    └── seed_cache.py           # Re-seed the data cache
```

---

## Responsible AI

This platform is built on transparent, accountable AI principles:

- **Transparency** — All modelling choices and data sources are documented and visible in the Explainability Center
- **Interpretability** — Every forecast includes a confidence classification, driver narratives, and plain-language explanations accessible to non-technical policymakers
- **Accountability** — Forecast limitations are prominently communicated throughout the platform
- **Human Oversight** — AI narratives are advisory. Strategic decisions must remain the responsibility of qualified domain experts
- **Evidence-Based** — All intelligence is grounded in verified World Bank Open Data

> Forecasts are designed to **support — not replace** evidence-based strategic decision-making.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| App won't start | Run `python scripts/validate_setup.py` to identify missing dependencies |
| No data shown | Click **🔄 Refresh Data** in the sidebar to fetch from World Bank API |
| Forecast error | Switch frequency to **Annual** — Monthly requires more data points |
| Slow forecast | Annual frequency is fastest; LightGBM selects automatically |
| Arabic text not rendering | Ensure your browser supports Arabic Unicode (all modern browsers do) |
| Port 8501 busy | Run `streamlit run app.py --server.port 8502` |

---

## Societal Impact

Youth unemployment is one of the GCC's most pressing structural challenges. This platform equips policymakers with:

- **Evidence-based forecasts** grounded in rigorous statistical validation
- **Scenario planning** to test policy interventions before implementation
- **Transparent AI** with explainability built in — suitable for public-sector governance
- **Arabic-first reporting** aligned with the language of government decision-making
- **Comparative intelligence** enabling GCC nations to learn from each other's trajectories

---

## Data Sources

- **World Bank Open Data** — https://data.worldbank.org
- **ILO Labour Statistics** (via World Bank indicators)
- **ITU ICT Data** (via World Bank — internet usage)
- Coverage: 2010–2024 · Annual frequency · 6 GCC countries

---

*GCC AI Intelligence Platform · World Bank Open Data · Responsible AI for Gulf Policy Planning*

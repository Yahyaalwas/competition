# GCC Youth Employment Intelligence Platform

> **An AI-powered statistical intelligence and decision-support platform for forecasting youth employment trends and supporting Gulf policy planning.**

Built for GCC policymakers, statistical agencies, and government strategists who need explainable AI forecasting, bilingual executive reporting, and interactive scenario simulation — all in one platform.

---

## Platform Overview

The platform transforms raw employment indicators into actionable intelligence, combining rigorous time-series forecasting with AI-generated narrative analysis and interactive policy simulation.

**Target countries:** Oman · Saudi Arabia · UAE · Qatar · Kuwait · Bahrain

**Primary indicators:**
- Youth Unemployment Rate (%)
- Youth Labour Force Participation Rate (%)
- Graduate Employment Rate (%)
- Private Sector Employment Share (%)
- Digital Sector Employment Growth (%)

---

## Key Capabilities

### 🤖 AI Decision Intelligence
Automatically generates bilingual (English + Arabic) executive reports from forecast outputs — including executive summaries, risk assessments, influencing factors, strategic recommendations, and forward-looking outlooks. Tone and framing are calibrated for government and ministerial audiences.

### 📈 Multi-Model Forecasting Engine
Rigorous expanding-window cross-validation selects the best-performing model from:
- **Baseline models:** Naive, Seasonal Naive, Moving Average, Drift
- **Statistical:** ARIMA / SARIMAX with automatic order selection (AIC)
- **Machine learning:** LightGBM with quantile regression (80% prediction intervals)

### ⚙️ Policy Scenario Simulator
Interactive what-if modelling: adjust GDP growth, digital economy investment, education investment, labour market reform intensity, and population growth — and instantly see how the forecast changes with AI-generated impact interpretation.

### 🔬 Explainability Center
Transparent AI suitable for public-sector adoption:
- Model performance comparison across all cross-validation folds
- LightGBM feature importance rankings
- Trend/seasonality decomposition
- Prediction interval width analysis

### 🌍 GCC Regional Intelligence
- Six-country comparative dashboard with interactive heatmaps
- Country rankings and GCC average benchmarking
- Year-on-year change visualisation

### 📝 Arabic Executive Reporting
Downloadable Arabic reports with professional sections:
- الملخص التنفيذي — Executive Summary
- أبرز المؤشرات والرؤى — Key Insights
- تحليل المخاطر — Risk Analysis
- التوصيات الاستراتيجية — Strategic Recommendations
- النظرة المستقبلية — Forecast Outlook

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the dashboard

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501).

The platform loads instantly with built-in GCC data — no CSV upload required.

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 🌍 GCC Overview | Six-country comparative dashboard with heatmaps and rankings |
| 🔍 Country Explorer | Deep-dive into a single country across all indicators |
| 📈 Forecast Center | Run AI forecasts with model selection and confidence intervals |
| 🤖 AI Insights | Bilingual executive intelligence report with policy recommendations |
| ⚙️ Scenario Simulator | Interactive policy lever simulation with elasticity-based impact modelling |
| 🔬 Explainability | Model diagnostics, feature importance, decomposition |

---

## CLI Pipeline (Optional)

For batch processing or integration into automated workflows:

```bash
# Generate sample datasets
python scripts/make_sample_data.py

# Train models and select best via backtesting
python -m src.main train --data data/population_monthly.csv --freq M --horizon 12

# Generate forecast
python -m src.main forecast --data data/population_monthly.csv --freq M --horizon 12

# Full pipeline with Arabic report
python -m src.main report --data data/population_monthly.csv --freq M --horizon 12
```

---

## Architecture

```
├── app.py                  # Streamlit dashboard (6 pages)
├── config.yaml             # Model and pipeline configuration
├── requirements.txt
├── src/
│   ├── gcc_data.py         # Built-in GCC dataset (2015–2024, 5 indicators × 6 countries)
│   ├── intelligence.py     # AI decision intelligence & bilingual narrative engine
│   ├── scenario.py         # Elasticity-based scenario simulation
│   ├── data.py             # Data loading, cleaning, validation
│   ├── evaluate.py         # Expanding-window cross-validation backtesting
│   ├── explain.py          # Decomposition and explainability utilities
│   ├── plotting.py         # Matplotlib plotting helpers (CLI pipeline)
│   ├── main.py             # Click CLI entry point
│   └── models/
│       ├── baselines.py    # Naive, Seasonal Naive, Moving Average, Drift
│       ├── arima_model.py  # ARIMA/SARIMAX with AIC-based auto order selection
│       └── ml_model.py     # LightGBM with quantile regression
└── scripts/
    └── make_sample_data.py # Sample data generator
```

---

## Societal Impact

Youth unemployment is one of the GCC's most pressing structural challenges. This platform equips policymakers with:

- **Evidence-based forecasts** grounded in rigorous statistical validation
- **Scenario planning** to test the impact of policy interventions before implementation
- **Transparent AI** with explainability built in — suitable for public-sector governance requirements
- **Arabic-first reporting** aligned with the language of government decision-making

---

## License

MIT License

# GCC AI Intelligence Platform
## Architecture & System Diagrams — Specification Guide

> Use these specifications to recreate diagrams in PowerPoint, draw.io, Miro, Figma, or Lucidchart.  
> Style: Clean · Minimal · Executive-grade · Deep navy + gold brand

---

## Diagram A — Full System Architecture

**Layout:** Left-to-right horizontal flow, 5 columns

**Title:** GCC AI Intelligence Platform — System Architecture

---

### Boxes (left to right)

#### Box 1: Data Source
- **Label:** WORLD BANK  
  OPEN DATA API v2
- **Sub-label:** data.worldbank.org
- **Icon:** 🌐
- **Color:** `#1A7A4A` (green — external trusted source)
- **Contents list:**
  - SL.UEM.1524.ZS
  - NY.GDP.MKTP.KD.ZG
  - FP.CPI.TOTL.ZG
  - SP.POP.GROW
  - IT.NET.USER.ZS
- **Bottom strip:** 6 GCC nations · 2010–2024

#### Arrow 1
- Label: "REST API / CSV Cache"
- Style: Solid navy arrow, right-pointing

#### Box 2: Data Pipeline
- **Label:** DATA LAYER
- **Icon:** 🗄️
- **Color:** `#1B4F72` (navy)
- **Contents:**
  - src/wb_data.py
  - src/gcc_data.py
  - data/processed/
  - Offline cache ✓
- **Sub-note:** Interpolation · Validation · Metadata

#### Arrow 2
- Label: "pd.Series (annual / monthly)"
- Style: Solid navy arrow

#### Box 3: Forecasting Engine
- **Label:** 6-MODEL  
  AI ENGINE
- **Icon:** 🤖
- **Color:** `#2874A6` (medium blue)
- **Contents (stacked):**
  - Naïve · Seasonal Naïve
  - Moving Average · Drift
  - SARIMAX (auto-order AIC)
  - LightGBM (quantile regression)
- **Sub-note:** Expanding-window CV · sMAPE selection

#### Arrow 3
- Label: "BacktestResult + ScenarioResult"
- Style: Solid navy arrow

#### Box 4: Intelligence Layer
- **Label:** AI INTELLIGENCE  
  & TRUST LAYER
- **Icon:** ✨
- **Color:** `#C39B4E` (gold)
- **Text color:** `#091320` (dark, for contrast)
- **Contents:**
  - Risk classification (8 labels)
  - Strategic alerts (4 types)
  - Bilingual narratives EN/AR
  - Trust score (0–100)
  - Driver intelligence
  - Confidence classification

#### Arrow 4
- Label: "IntelligenceReport"
- Style: Solid navy arrow

#### Box 5: Dashboard
- **Label:** STREAMLIT  
  DASHBOARD
- **Icon:** 📊
- **Color:** `#091320` (near-black — premium)
- **Text color:** white
- **Contents:**
  - 6 pages
  - Plotly charts
  - Bilingual UI
  - Export system
  - Demo flow guide

---

### Footer strip (full width, below all boxes)
**Color:** `rgba(27,79,114,0.08)` light blue-grey
**Content:** 
World Bank Open Data · 6 GCC Nations · 5 Indicators · 15 Years · 6 Models · EN + AR · Offline-Capable

---

### Placement Notes
- All boxes: rounded corners (12px), 1px border in lighter shade, subtle drop shadow
- Arrows: 2.5pt weight, navy `#1B4F72`
- Arrow labels: 9pt, italic, grey
- Diagram overall: white background or very light `#F8FAFD`

---

## Diagram B — Forecasting Pipeline

**Layout:** Vertical flow, top-to-bottom, single column with branches

**Title:** AI Forecast Pipeline — Expanding-Window Cross-Validation

---

```
┌─────────────────────────────────────────────┐
│           INPUT CONFIGURATION               │  ← Blue box
│  Country · Indicator · Frequency · Horizon  │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│           WORLD BANK DATA FETCH             │  ← Green box
│  API v2 / Offline cache · Clean · Validate  │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│       EXPANDING-WINDOW CROSS-VALIDATION     │  ← Gold box
│                                             │
│  Fold 1: Train [t₀…tₙ]  → Test [h periods] │
│  Fold 2: Train [t₀…tₙ₊₁]→ Test [h periods] │
│  Fold 3: Train [t₀…tₙ₊₂]→ Test [h periods] │
│                                             │
│         ┌─────────────────────────┐         │
│         │  Evaluate 6 models on  │         │
│         │  each fold → sMAPE     │         │
│         └─────────────────────────┘         │
└────────────────────┬────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐         ┌──────────────────┐
    │ BEST     │         │ ALL MODEL        │
    │ MODEL    │         │ COMPARISON       │
    │ (lowest  │         │ TABLE            │
    │  sMAPE)  │         │ (MAE/RMSE/sMAPE) │
    └────┬─────┘         └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│           FORECAST GENERATION               │  ← Navy box
│  Point forecast + Prediction interval       │
│  (alpha/2, 1-alpha/2 quantiles or residuals)│
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│        CONFIDENCE CLASSIFICATION            │  ← Trust gold box
│  sMAPE + Interval width + Volatility +      │
│  Horizon → Trust Score (0–100) → Tier A–E   │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              OUTPUT                         │  ← Green box
│  Forecast chart · Model comparison          │
│  Confidence card · Forecast table · Export  │
└─────────────────────────────────────────────┘
```

---

## Diagram C — AI Decision Intelligence Flow

**Layout:** Hub-and-spoke from central AI Intelligence Engine

**Title:** AI Intelligence Engine — Input/Output Architecture

---

**Central hub:** 
```
  ┌─────────────────────────────┐
  │                             │
  │   AI INTELLIGENCE ENGINE    │
  │    src/intelligence.py      │
  │                             │
  └─────────────────────────────┘
```
(Gold circle/hexagon, large, center of diagram)

**Inputs (left side, 4 arrows pointing INTO hub):**

1. **Historical Series** (World Bank data, pd.Series)
2. **Forecast + Intervals** (from forecasting engine)
3. **Model Performance** (sMAPE, model name)
4. **GCC Average** (regional benchmark series)

**Outputs (right side, 6 arrows pointing OUT of hub):**

1. **Risk Profile** → Risk label + severity + Arabic label + rationale
2. **Strategic Alerts** → Up to 4 contextual alerts (critical / warning / success / info)
3. **Executive Summary** → EN + AR narrative paragraph
4. **GCC Comparison** → Peer benchmarking narrative EN + AR
5. **Causal Interpretation** → Structural driver narrative EN + AR
6. **Policy Recommendations** → 4–5 actionable recommendations EN + AR

**Bottom note:**
> 8 risk profile labels · 4 alert types · 8 intelligence report sections · Bilingual EN/AR · Downloadable

---

## Diagram D — Scenario Simulation Engine

**Layout:** Linear pipeline with branching at GCC comparison step

**Title:** Scenario Simulation — Elasticity-Based Policy Modelling

---

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCENARIO PRESET SELECTION                     │
│  📊 Baseline · ⚡ Digital Acceleration · 📉 Economic Slowdown   │
│  🔥 Inflation Stress · 🏗 Reform Expansion · 🌱 Youth Recovery │
│  👥 Population Surge · 🚀 High Growth GCC                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ params: {gdp_growth, digital_investment,
                             │          education_investment, labor_reforms,
                             │          population_growth}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              ELASTICITY MODEL (src/scenario.py)                  │
│                                                                  │
│  total_shift = Σ(elasticity_i × delta_i)                        │
│                                                                  │
│  Scenario[t] = Baseline[t] + total_shift × (t/horizon)          │
│                           ↑ linear ramp over forecast horizon    │
└──────────────────┬──────────────────────────┬───────────────────┘
                   │                          │
                   ▼                          ▼
    ┌──────────────────────┐    ┌──────────────────────────────────┐
    │  FOCAL COUNTRY       │    │  GCC COMPARATIVE SIMULATION      │
    │  SCENARIO RESULT     │    │  (all 6 nations simultaneously)  │
    │                      │    │                                  │
    │  Baseline end value  │    │  SAU: 11.3% · UAE: 4.1%         │
    │  Scenario end value  │    │  QAT: 2.8% · KWT: 16.2%        │
    │  Delta (pp)          │    │  BHR: 12.5% · OMN: 18.4%       │
    │  Relative change     │    │                                  │
    └──────────┬───────────┘    │  → Rank table                   │
               │                │  → Rank shift (+/−)             │
               └────────────────┘──────────────────────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────────┐
                        │   SCENARIO INTELLIGENCE CLASSIFICATION   │
                        │                                          │
                        │  10 label types:                         │
                        │  Recovery Opportunity · Digital Growth  │
                        │  Reform-Driven · Growth Acceleration    │
                        │  Strategic Stabilization · Elevated Vol │
                        │  Structural Labor Pressure · Inflation   │
                        │  Demographic Pressure · Neutral          │
                        └─────────────────────────────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────────┐
                        │    BILINGUAL SCENARIO INTEL REPORT      │
                        │                                          │
                        │  6 sections × EN + AR                   │
                        │  Strategic Outlook · Key Impact         │
                        │  Labour Implications · Risk Assessment  │
                        │  GCC Comparative · Recommendations      │
                        └─────────────────────────────────────────┘
```

---

## Diagram E — Explainability & Trust Layer

**Layout:** Three-layer vertical stack

**Title:** Explainability Architecture — Trust at Every Level

---

**Layer 1 (Top) — Model Selection Transparency**
```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL SELECTION LAYER                     │  ← Blue
│                                                              │
│  6 models evaluated on holdout folds                         │
│  Selection criterion: lowest sMAPE                           │
│  Output: BacktestResult (model name + MAE + RMSE + sMAPE)   │
│                                                              │
│  Quality Tier: A+ (<5%) · B (5–12%) · C (12–25%) · D (>25%) │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

**Layer 2 (Middle) — Prediction Uncertainty**
```
┌─────────────────────────────────────────────────────────────┐
│                  UNCERTAINTY COMMUNICATION                    │  ← Gold
│                                                              │
│  Prediction intervals at user-selected confidence (70–95%)   │
│  Interval width plotted by horizon (H+1 through H+n)        │
│                                                              │
│  Trust Score = f(sMAPE, interval_width, volatility, horizon) │
│  Score: 0–100 → Confidence Tier: A (High) through E (Unstable)│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

**Layer 3 (Bottom) — Driver Intelligence**
```
┌─────────────────────────────────────────────────────────────┐
│                    DRIVER INTELLIGENCE                        │  ← Teal
│                                                              │
│  LightGBM feature importances → Policy narratives            │
│                                                              │
│  14 feature name patterns:                                   │
│  lag_* → "Historical momentum"                              │
│  roll_mean_* → "Trend momentum (3/6/12 period)"             │
│  roll_std_* → "Volatility signal"                           │
│  year_idx → "Structural time drift"                         │
│  month/quarter → "Seasonal employment cycle"                │
│                                                              │
│  Output: Ranked driver cards (EN + AR) with directional      │
│          influence (▲ positive / ▼ negative / ► neutral)    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

**Foundation (Bottom bar)**
```
┌─────────────────────────────────────────────────────────────┐
│              RESPONSIBLE AI TRANSPARENCY CENTRE              │  ← Dark navy
│                                                              │
│  Data Provenance · Methodology · Interpretation Guidance    │
│  6 Forecast Caveats · Responsible Decision Support          │
│  Platform Governance Statement                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Diagram Styling Cheatsheet

### Colors
| Element | Hex | Use |
|---|---|---|
| External system | `#1A7A4A` | World Bank, data sources |
| Core platform (navy) | `#1B4F72` | Main processing boxes |
| AI/Intelligence | `#C39B4E` | Gold — intelligence engine |
| ML/Models | `#2874A6` | Medium blue — model boxes |
| Trust/Explainability | `#148F77` | Teal — trust layer |
| Background | `#EEF2F7` | Diagram canvas |
| Dark accent | `#091320` | Headers, dark boxes |
| Arrow color | `#1B4F72` | All connecting arrows |

### Box Styles
- Corner radius: 10–14px
- Border: 1.5px, slightly darker than fill
- Shadow: `0 4px 16px rgba(0,0,0,0.12)`
- Padding: 12–16px
- Font: Sans-serif, 11–13pt

### Arrow Styles
- Weight: 2.5pt
- Color: `#1B4F72`
- Labels: 9pt italic, grey `#666`
- Arrowhead: filled triangle

### Text Hierarchy
- Box title: 12pt, Bold (700), Uppercase, tracking 0.5px
- Box content: 10pt, Regular (400)
- Diagram title: 18pt, Bold (800), navy
- Sub-labels: 8pt, italic, `#888`

---

## Screenshot Capture Plan

The following screenshots should be captured in the live platform for use in the PowerPoint slides and technical report.

| # | Page | Required State | Screenshot Purpose |
|---|---|---|---|
| 1 | GCC Overview — Hero | Youth Unemployment selected, all 6 countries populated | Platform hero shot (Slide 4) |
| 2 | GCC Overview — KPI row | Any indicator | Six-country live data |
| 3 | GCC Overview — AI Risk Snapshot | Youth unemployment | AI risk badge row close-up |
| 4 | GCC Overview — Heatmap | Any indicator, 2015–2024 | Year-on-year change (Slide 6) |
| 5 | Country Explorer | Saudi Arabia + Youth Unemployment | Deep-dive view |
| 6 | Country Explorer — AI Panel | Saudi Arabia, alerts visible | Strategic alerts close-up |
| 7 | Forecast Center — post-forecast | Saudi Arabia, LightGBM selected, confidence card visible | Confidence classification (Slide 7) |
| 8 | Forecast Center — chart | Saudi Arabia, 3yr forecast | Forecast with prediction intervals |
| 9 | AI Insights — English tab | Saudi Arabia, report generated | Executive intelligence report (Slide 8) |
| 10 | AI Insights — Arabic tab | Saudi Arabia | Arabic bilingual output (Slide 8) |
| 11 | Scenario Simulator — presets | All 8 visible, Reform Expansion active | Preset grid (Slide 9) |
| 12 | Scenario Simulator — banner | "Reform-Driven Improvement" visible | Scenario classification |
| 13 | Scenario Simulator — KPIs | Delta cards visible | Impact quantification |
| 14 | Explainability — Trust Header | Score visible, Saudi Arabia | Trust score (Slide 10) |
| 15 | Explainability — Driver Intel | Top 8 drivers ranked | Driver narrative cards |
| 16 | Explainability — AI Transparency | Full tab visible | Responsible AI documentation |

### Capture Checklist
- [ ] Browser zoom: 100% (not zoomed in or out)
- [ ] Window: maximised, minimum 1440px wide
- [ ] Data: All charts populated (no empty states)
- [ ] Platform: Dark sidebar visible in screenshots
- [ ] Format: PNG, minimum 1920×1080
- [ ] Tool: Browser built-in screenshot or Snagit for full-page

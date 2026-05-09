# GCC AI Intelligence Platform
## Screenshot Integration Guide — PowerPoint Finalization

> After capturing screenshots from the live platform, insert them into the designated
> placeholder areas in `GCC_AI_Intelligence_Platform.pptx` to replace the grey placeholder boxes.
>
> Capture tool: Browser built-in screenshot (F12 → Device toolbar → 1920×1080)  
> Format: PNG · Zoom: 100% · Window: maximized (min 1440px wide)

---

## Pre-Capture Setup

1. Run `python scripts/validate_setup.py` — ensure 20/20 checks pass
2. Launch: `streamlit run app.py`
3. Open: `http://localhost:8501`
4. Navigate to each page as specified below
5. Ensure all data is populated (no empty states) before capturing

---

## Screenshots by Slide

### Slide 2 — Problem Statement
*No screenshot needed — data-driven layout is self-contained.*

---

### Slide 4 — Platform Overview
**Screenshot: GCC Overview Hero**

| Setting | Value |
|---|---|
| Page | 🌍 GCC Overview |
| Indicator | Youth Unemployment Rate |
| State | All 6 countries populated · KPI cards visible · AI risk badge row visible |
| Capture area | Full page (scroll to show KPI row + AI Regional Intelligence Snapshot) |
| Placement | Replace grey box: "GCC Overview — Hero" |
| Sizing | Fill full right half of slide · maintain aspect ratio |

**What to show:**
- Six navy KPI cards at top with live values and YoY deltas
- The AI Regional Intelligence Snapshot row at bottom showing risk badges (Stable, Moderate Risk, High Risk)
- Sidebar visible with demo flow numbering

---

### Slide 5 — System Architecture
*No screenshot needed — the pipeline diagram is generated from shapes.*

---

### Slide 6 — Data & Forecasting Pipeline
**Screenshot: YoY Change Heatmap**

| Setting | Value |
|---|---|
| Page | 🌍 GCC Overview |
| Indicator | Youth Unemployment Rate |
| Section | Year-on-Year Change Heatmap |
| Capture area | Heatmap chart only (crop tightly around the chart) |
| Placement | Replace grey box on left column bottom area |
| Sizing | Full width of left panel · preserve color fidelity |

**What to show:**
- All 6 countries on Y-axis
- 2015–2024 on X-axis
- Green/red gradient cells showing year-on-year change
- Caption: "Real World Bank data — not synthetic"

---

### Slide 7 — AI Strategic Intelligence
**Screenshot: AI Insights — English Report**

| Setting | Value |
|---|---|
| Page | 🤖 AI Insights |
| Country | Saudi Arabia |
| Indicator | Youth Unemployment Rate |
| Prerequisite | Run forecast first (Forecast Center → Run Demo Forecast) |
| State | English tab · risk panel visible · executive summary visible |
| Capture area | Risk classification panel + executive summary section |
| Placement | Insert as large visual on right half of slide |

**What to show:**
- Risk profile badge (Moderate Risk — orange)
- Three strategic alerts visible
- Executive summary paragraph text
- Bilingual output visible (Arabic tab present)

**Screenshot: AI Insights — Arabic Tab**

| Setting | Value |
|---|---|
| Page | 🤖 AI Insights |
| Tab | Arabic (العربية) |
| Capture area | Full Arabic report (first 2–3 sections visible) |
| Placement | Optional: insert as inset thumbnail showing bilingual capability |

---

### Slide 8 — Scenario Simulation
**Screenshot: Scenario Classification Banner**

| Setting | Value |
|---|---|
| Page | ⚙️ Scenario Simulator |
| Preset | Reform Expansion (active) |
| State | Post-apply · classification banner visible · KPI delta cards visible |
| Capture area | Banner + 4 KPI delta cards |
| Placement | Replace or supplement the hardcoded values on slide |

**What to show:**
- "Reform-Driven Improvement — Opportunity" banner in green
- Four delta cards: Baseline 13.8% · Scenario 11.3% · Delta −2.5pp · Rank #4→#2
- GCC comparative rank table below

---

### Slide 9 — Explainability & Trust
**Screenshot: Trust Intelligence Header**

| Setting | Value |
|---|---|
| Page | 🔬 Explainability |
| Country | Saudi Arabia |
| Indicator | Youth Unemployment Rate |
| Prerequisite | Forecast must have been run |
| State | Trust header fully rendered · score visible |
| Capture area | Trust header only (top dark navy strip with score badge) |
| Placement | Insert above the four trust pillar cards · full width |

**Screenshot: Driver Intelligence Tab**

| Setting | Value |
|---|---|
| Page | 🔬 Explainability |
| Tab | Driver Intelligence |
| State | Top 8 drivers ranked · importance bars visible |
| Capture area | Top 5–6 driver cards |
| Placement | Insert as right-column visual on slide 9 |

---

### Slide 10 — Dashboard & Executive UX
**Screenshot: GCC Overview Hero (full page)**

| Setting | Value |
|---|---|
| Page | 🌍 GCC Overview |
| Indicator | Youth Unemployment Rate |
| State | Hero banner visible · all KPI cards populated |
| Capture area | Full page above fold |
| Placement | Replace grey placeholder on right half of slide |

**Tip:** This is the strongest single hero screenshot. Make it full-width on slide 10 for maximum impact.

---

### Slide 11 — Societal Impact
*No screenshot needed — content is designed as clean infographic.*

---

### Slide 12 — Conclusion
*No screenshot needed — closing statement slide.*

---

## "Wow Moment" Priority Screenshots

If time is limited, capture these 5 in priority order:

| Priority | Screenshot | Slide | Why |
|---|---|---|---|
| 1 | AI Insights — Risk panel + 3 alerts | 7 | Most distinctive AI output |
| 2 | Trust Intelligence Header (score 74/100) | 9 | Trust score is unexpected and compelling |
| 3 | AI Insights — Arabic tab | 7 | Judges rarely see ministry-grade Arabic AI |
| 4 | Scenario Simulator — Reform Expansion active | 8 | "#4 to #2" is concrete and memorable |
| 5 | GCC Overview — KPI cards + AI risk badges | 4/10 | Immediate platform credibility |

---

## Screenshot Insertion Instructions (PowerPoint)

1. Open `GCC_AI_Intelligence_Platform.pptx` in PowerPoint or Google Slides
2. Navigate to the target slide
3. Delete the grey placeholder rectangle and text
4. Insert → Picture → From File → select your PNG
5. Resize to fill the placeholder area (hold Shift to maintain aspect ratio)
6. Apply: Format → Picture Border → Navy `#1B4F72`, 1.5pt
7. Optional: Format → Shadow → Outer, Offset Bottom, 4pt, 12% opacity
8. Send to back if it overlaps other elements: Arrange → Send Backward

---

## Capture Quality Checklist

- [ ] Browser zoom: exactly 100%
- [ ] Window: maximized, minimum 1440px wide
- [ ] All charts fully loaded (no spinners)
- [ ] Dark sidebar visible in screenshots
- [ ] Format: PNG (not JPEG — preserves text sharpness)
- [ ] Minimum resolution: 1920×1080
- [ ] No browser UI chrome visible in crop

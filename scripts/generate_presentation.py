#!/usr/bin/env python3
"""
GCC AI Intelligence Platform — Competition Presentation Generator
Produces a professional 12-slide PowerPoint deck.

Usage:
    python scripts/generate_presentation.py
Output:
    presentation/GCC_AI_Intelligence_Platform.pptx
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree

# ── Brand colors ─────────────────────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1B, 0x4F, 0x72)
GOLD   = RGBColor(0xC3, 0x9B, 0x4E)
DARK   = RGBColor(0x09, 0x13, 0x20)
GREEN  = RGBColor(0x1A, 0x7A, 0x4A)
BLUE   = RGBColor(0x28, 0x74, 0xA6)
RED    = RGBColor(0xA9, 0x32, 0x26)
BG     = RGBColor(0xEE, 0xF2, 0xF7)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
AMBER  = RGBColor(0xC0, 0x78, 0x20)
TEAL   = RGBColor(0x14, 0x8F, 0x77)
LGRAY  = RGBColor(0xF4, 0xF6, 0xF9)
MGRAY  = RGBColor(0x77, 0x77, 0x77)
NAVY2  = RGBColor(0x0D, 0x2A, 0x42)
GOLD2  = RGBColor(0xA0, 0x7C, 0x38)

SW = Inches(13.33)
SH = Inches(7.5)
MSO_RECT = 1


def _new_prs():
    prs = Presentation()
    prs.slide_width  = SW
    prs.slide_height = SH
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _rect(slide, l, t, w, h, fill=None, line_color=None, line_w=Pt(0.5)):
    sp = slide.shapes.add_shape(MSO_RECT, l, t, w, h)
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    else:
        sp.fill.background()
    if line_color:
        sp.line.color.rgb = line_color
        sp.line.width = line_w
    else:
        sp.line.fill.background()
    return sp


def _tb(slide, text, l, t, w, h,
        size=Pt(11), bold=False, color=WHITE,
        align=PP_ALIGN.LEFT, italic=False, wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return tb


def _ml(slide, lines, l, t, w, h,
        default_size=Pt(11), default_color=WHITE,
        align=PP_ALIGN.LEFT, spacing=None):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in lines:
        if isinstance(item, str):
            item = (item, False, default_size, default_color)
        text, bold, sz, col = item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        if spacing:
            p.line_spacing = spacing
        r = p.add_run()
        r.text = text
        r.font.size = sz
        r.font.bold = bold
        r.font.color.rgb = col
    return tb


def _header_bar(slide, title, subtitle=None):
    _rect(slide, Inches(0), Inches(0), SW, Inches(1.15), fill=DARK)
    _rect(slide, Inches(0), Inches(1.15), SW, Inches(0.05), fill=GOLD)
    _tb(slide, title,
        Inches(0.5), Inches(0.18), Inches(10), Inches(0.65),
        size=Pt(26), bold=True, color=WHITE)
    if subtitle:
        _tb(slide, subtitle,
            Inches(0.5), Inches(0.72), Inches(11), Inches(0.38),
            size=Pt(12), color=GOLD, italic=True)


def _footer(slide, text, dark_bg=False):
    col = WHITE if dark_bg else MGRAY
    if dark_bg:
        _rect(slide, Inches(0), Inches(7.18), SW, Inches(0.32), fill=DARK)
    _tb(slide, text,
        Inches(0.5), Inches(7.2), Inches(12.5), Inches(0.28),
        size=Pt(8.5), color=col, align=PP_ALIGN.CENTER, italic=True)


def _card(slide, l, t, w, h, fill=LGRAY, border=NAVY,
          title=None, title_color=DARK, body_lines=None,
          title_size=Pt(11), body_size=Pt(9.5)):
    _rect(slide, l, t, w, h, fill=fill, line_color=border, line_w=Pt(1.2))
    y = t + Inches(0.12)
    if title:
        _tb(slide, title, l + Inches(0.15), y, w - Inches(0.3), Inches(0.3),
            size=title_size, bold=True, color=title_color)
        y += Inches(0.32)
    if body_lines:
        tb = slide.shapes.add_textbox(l + Inches(0.15), y,
                                       w - Inches(0.3), h - (y - t) - Inches(0.1))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for ln in body_lines:
            if isinstance(ln, str):
                ln = (ln, False, body_size, DARK)
            txt, bold, sz, col = ln
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = txt
            r.font.size = sz
            r.font.bold = bold
            r.font.color.rgb = col


def _chip(slide, text, l, t, w, h, fill=NAVY, text_color=WHITE, size=Pt(9)):
    _rect(slide, l, t, w, h, fill=fill)
    _tb(slide, text, l, t, w, h, size=size, bold=True,
        color=text_color, align=PP_ALIGN.CENTER)


def _bullet_box(slide, title, bullets, l, t, w, h,
                title_color=NAVY, bullet_color=DARK,
                title_size=Pt(12), bullet_size=Pt(10),
                fill=None, border=None):
    if fill or border:
        _rect(slide, l, t, w, h, fill=fill, line_color=border, line_w=Pt(1))
    _tb(slide, title, l + Inches(0.1), t + Inches(0.1),
        w - Inches(0.2), Inches(0.35),
        size=title_size, bold=True, color=title_color)
    tb = slide.shapes.add_textbox(l + Inches(0.18), t + Inches(0.48),
                                   w - Inches(0.3), h - Inches(0.6))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for b in bullets:
        if isinstance(b, str):
            b = (b, False, bullet_size, bullet_color)
        txt, bold, sz, col = b
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = "  " + txt
        r.font.size = sz
        r.font.bold = bold
        r.font.color.rgb = col


def slide_01_title(prs):
    s = _blank(prs)
    _bg(s, DARK)
    _rect(s, Inches(0), Inches(0), Inches(0.18), SH, fill=GOLD)
    _rect(s, Inches(0.18), Inches(0), SW - Inches(0.18), SH, fill=NAVY2)
    _rect(s, Inches(0.6), Inches(0.5), Inches(0.9), Inches(0.9), fill=GOLD)
    _tb(s, "🌍", Inches(0.6), Inches(0.52), Inches(0.9), Inches(0.9),
        size=Pt(30), align=PP_ALIGN.CENTER)
    _tb(s, "GCC AI Intelligence Platform",
        Inches(0.5), Inches(1.65), Inches(12.3), Inches(1.1),
        size=Pt(44), bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    _rect(s, Inches(0.5), Inches(2.85), Inches(6.5), Inches(0.055), fill=GOLD)
    _tb(s,
        "AI-Powered Youth Employment Forecasting\n& Policy Decision Support for the Gulf Cooperation Council",
        Inches(0.5), Inches(3.0), Inches(11.5), Inches(1.1),
        size=Pt(20), color=GOLD, italic=False)
    _rect(s, Inches(0.18), Inches(6.6), SW - Inches(0.18), Inches(0.9), fill=DARK)
    strip = "World Bank Open Data  ·  6 GCC Nations  ·  5 Indicators  ·  2010–2024  ·  6 AI Models  ·  Bilingual EN + AR  ·  Offline-Capable"
    _tb(s, strip, Inches(0.5), Inches(6.72), Inches(12.5), Inches(0.4),
        size=Pt(10), color=GOLD, align=PP_ALIGN.CENTER)
    _tb(s, "Where are we?  ·  Where are we heading?  ·  What should we do?",
        Inches(0.5), Inches(4.3), Inches(11), Inches(0.5),
        size=Pt(13.5), color=WHITE, italic=True, align=PP_ALIGN.LEFT)
    _tb(s, "COMPETITION SUBMISSION  ·  GCC AI INNOVATION CHALLENGE",
        Inches(0.5), Inches(5.1), Inches(10), Inches(0.35),
        size=Pt(9), color=GOLD, bold=True)
    for i, (val, lbl) in enumerate([("6", "NATIONS"), ("6", "AI MODELS"), ("15", "YEARS DATA"), ("EN+AR", "BILINGUAL")]):
        bx = Inches(11.3)
        by = Inches(1.4 + i * 1.18)
        _rect(s, bx, by, Inches(1.68), Inches(0.95), fill=NAVY, line_color=GOLD, line_w=Pt(1))
        _tb(s, val, bx, by + Inches(0.05), Inches(1.68), Inches(0.5),
            size=Pt(22), bold=True, color=GOLD, align=PP_ALIGN.CENTER)
        _tb(s, lbl, bx, by + Inches(0.52), Inches(1.68), Inches(0.3),
            size=Pt(7.5), bold=True, color=WHITE, align=PP_ALIGN.CENTER)


def slide_02_problem(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "A Structural Challenge Requiring Strategic Intelligence",
                subtitle="GCC Youth Employment — The Policy Intelligence Gap")
    _rect(s, Inches(0.35), Inches(1.35), Inches(5.5), Inches(5.7),
          fill=DARK, line_color=GOLD, line_w=Pt(1.5))
    _tb(s, "THE NUMBERS", Inches(0.55), Inches(1.5), Inches(5), Inches(0.4),
        size=Pt(10), bold=True, color=GOLD)
    stats = [
        ("3.5% – 30%+", "Youth unemployment range across GCC"),
        ("60 million", "People in GCC workforce ecosystem"),
        ("Largest ever", "Youth cohort in GCC history"),
        ("Divergent", "Trajectories across 6 nations"),
        ("Decades-long", "Skills mismatch unresolved"),
    ]
    for i, (val, desc) in enumerate(stats):
        y = Inches(2.05 + i * 0.9)
        _rect(s, Inches(0.55), y, Inches(5.1), Inches(0.72),
              fill=NAVY, line_color=GOLD2, line_w=Pt(0.8))
        _tb(s, val, Inches(0.7), y + Inches(0.05), Inches(4.7), Inches(0.35),
            size=Pt(16), bold=True, color=GOLD)
        _tb(s, desc, Inches(0.7), y + Inches(0.38), Inches(4.7), Inches(0.28),
            size=Pt(9), color=WHITE)
    _rect(s, Inches(6.15), Inches(1.35), Inches(6.85), Inches(5.7),
          fill=WHITE, line_color=NAVY, line_w=Pt(1))
    _tb(s, "THE INTELLIGENCE GAP", Inches(6.35), Inches(1.5), Inches(6.4), Inches(0.4),
        size=Pt(10), bold=True, color=NAVY)
    gaps = [
        ("Fragmented Data",
         "Statistics scattered across national agencies, World Bank, ILO & OECD — no unified view"),
        ("No Regional Benchmark",
         "Governments lack a real-time GCC peer comparison platform"),
        ("No Forward Intelligence",
         "All reporting is retrospective — strategic planning lacks AI-powered predictive signals"),
        ("No Scenario Modelling",
         "Policymakers cannot model employment impact before committing to interventions"),
        ("No Bilingual Executive Layer",
         "Insights generated in English are inaccessible to Arabic-speaking ministry audiences"),
    ]
    for i, (title, desc) in enumerate(gaps):
        y = Inches(2.05 + i * 0.95)
        _rect(s, Inches(6.25), y, Inches(0.42), Inches(0.42), fill=RED)
        _tb(s, "✕", Inches(6.25), y, Inches(0.42), Inches(0.42),
            size=Pt(13), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _tb(s, title, Inches(6.78), y + Inches(0.0), Inches(5.8), Inches(0.28),
            size=Pt(10.5), bold=True, color=DARK)
        _tb(s, desc, Inches(6.78), y + Inches(0.3), Inches(5.8), Inches(0.55),
            size=Pt(9), color=MGRAY, wrap=True)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_03_why(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Youth Employment Is a Strategic Priority for the GCC",
                subtitle="Policy · Economic · Social — Three Dimensions of Impact")
    pillars = [
        (NAVY, "🏛", "POLICY IMPACT",
         ["Evidence-based labour market decisions",
          "Aligned with Vision 2030, UAE Centennial 2071, QNV 2030",
          "Replaces fragmented data with unified intelligence",
          "Enables early warning before crises emerge",
          "Supports national workforce strategy planning"]),
        (GREEN, "📊", "ECONOMIC IMPACT",
         ["Youth employment drives GDP multiplier effects",
          "Reduces dependency on public-sector hiring",
          "Strengthens private-sector depth and resilience",
          "Delays economic diversification when unresolved",
          "Productive youth = sustainable fiscal position"]),
        (AMBER, "🤝", "SOCIAL IMPACT",
         ["Youth unemployment drives social instability",
          "Brain drain accelerates when opportunities are absent",
          "Public-sector cost escalation under unresolved pressure",
          "AI-assisted forecasting enables structured early action",
          "60 million people — the workforce future of the Gulf"]),
    ]
    for i, (col, icon, title, bullets) in enumerate(pillars):
        x = Inches(0.35 + i * 4.32)
        _rect(s, x, Inches(1.35), Inches(4.1), Inches(1.05), fill=col)
        _tb(s, icon, x + Inches(0.1), Inches(1.38), Inches(0.8), Inches(0.8),
            size=Pt(26), align=PP_ALIGN.CENTER)
        _tb(s, title, x + Inches(0.95), Inches(1.5), Inches(3.0), Inches(0.55),
            size=Pt(13), bold=True, color=WHITE)
        _rect(s, x, Inches(2.42), Inches(4.1), Inches(4.35),
              fill=WHITE, line_color=col, line_w=Pt(2.5))
        tb = s.shapes.add_textbox(x + Inches(0.2), Inches(2.58), Inches(3.7), Inches(4.0))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = "▸  " + b
            r.font.size = Pt(10.5)
            r.font.color.rgb = DARK
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_04_platform(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "One Platform. Six Nations. Full Intelligence Cycle.",
                subtitle="End-to-End AI Decision Support — From Raw Data to Ministerial Briefing")
    cards = [
        (NAVY, "🌍", "GCC REGIONAL INTELLIGENCE",
         "Six-country live dashboard · AI risk badges · YoY heatmap · GCC average benchmarking"),
        (BLUE, "🔍", "COUNTRY DEEP-DIVE",
         "Per-nation KPIs · 10-year trend analysis · AI strategic alerts · Historical comparison"),
        (GOLD, "📈", "AI FORECASTING ENGINE",
         "6-model ensemble · Auto-selection via sMAPE CV · Prediction intervals · Trust score"),
        (DARK, "🤖", "AI INTELLIGENCE REPORTS",
         "Bilingual EN/AR executive briefs · 8 risk profiles · Strategic alerts · Policy recommendations"),
        (GREEN, "⚙️", "SCENARIO SIMULATION",
         "8 policy presets · Elasticity-based impact · GCC-wide rank simulation · Bilingual intel report"),
        (TEAL, "🔬", "EXPLAINABILITY & TRUST",
         "Trust score 0–100 · Driver intelligence · Confidence tiers A–E · Responsible AI centre"),
    ]
    for i, (col, icon, title, desc) in enumerate(cards):
        row, col_idx = divmod(i, 3)
        x = Inches(0.35 + col_idx * 4.32)
        y = Inches(1.42 + row * 2.72)
        _rect(s, x, y, Inches(4.1), Inches(0.7), fill=col)
        _tb(s, icon + "  " + title,
            x + Inches(0.12), y + Inches(0.12), Inches(3.8), Inches(0.5),
            size=Pt(10.5), bold=True, color=WHITE)
        _rect(s, x, y + Inches(0.7), Inches(4.1), Inches(1.7),
              fill=WHITE, line_color=col, line_w=Pt(1.8))
        _tb(s, desc, x + Inches(0.15), y + Inches(0.82),
            Inches(3.8), Inches(1.45), size=Pt(9.5), color=DARK, wrap=True)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_05_architecture(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Production-Grade AI Architecture",
                subtitle="Five-Layer Data-to-Intelligence Pipeline · Offline-Capable · Bilingual")
    boxes = [
        (GREEN, "🌐", "WORLD BANK\nOPEN DATA API v2",
         ["5 official indicators", "6 GCC nations", "2010–2024", "REST API + CSV cache"]),
        (NAVY, "🗄", "DATA LAYER",
         ["src/wb_data.py", "src/gcc_data.py", "Interpolation", "Offline cache ✓"]),
        (BLUE, "🤖", "6-MODEL AI ENGINE",
         ["Naïve · Seasonal Naïve", "Moving Average · Drift", "SARIMAX (AIC auto)", "LightGBM (quantile)"]),
        (GOLD, "✨", "AI INTELLIGENCE\n& TRUST LAYER",
         ["8 risk profiles", "4 alert types", "Trust score 0–100", "Driver intelligence"]),
        (DARK, "📊", "STREAMLIT\nDASHBOARD",
         ["6 pages · Plotly", "Bilingual UI", "Export system", "Demo flow guide"]),
    ]
    box_w = Inches(2.22)
    box_h = Inches(4.3)
    arrow_w = Inches(0.3)
    total_w = len(boxes) * box_w + (len(boxes) - 1) * arrow_w
    start_x = (SW - total_w) / 2
    for i, (col, icon, title, items) in enumerate(boxes):
        x = start_x + i * (box_w + arrow_w)
        y = Inches(1.45)
        _rect(s, x, y, box_w, Inches(0.95), fill=col)
        _tb(s, icon + " " + title,
            x + Inches(0.1), y + Inches(0.08), box_w - Inches(0.2), Inches(0.8),
            size=Pt(9.5), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _rect(s, x, y + Inches(0.95), box_w, box_h - Inches(0.95),
              fill=WHITE, line_color=col, line_w=Pt(1.5))
        tb = s.shapes.add_textbox(x + Inches(0.12), y + Inches(1.08),
                                   box_w - Inches(0.24), box_h - Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for item in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = "▸ " + item
            r.font.size = Pt(9)
            r.font.color.rgb = DARK
        if i < len(boxes) - 1:
            ax = x + box_w + Inches(0.02)
            ay = y + Inches(2.0)
            _tb(s, "→", ax, ay, arrow_w, Inches(0.4),
                size=Pt(18), bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    labels = ["REST API\nCSV Cache", "pd.Series\nannual/monthly",
              "BacktestResult\nScenarioResult", "IntelligenceReport"]
    for i, lbl in enumerate(labels):
        ax = start_x + i * (box_w + arrow_w) + box_w + Inches(0.02)
        _tb(s, lbl, ax - Inches(0.05), Inches(3.65), arrow_w + Inches(0.1), Inches(0.5),
            size=Pt(6.5), color=MGRAY, align=PP_ALIGN.CENTER, italic=True)
    _rect(s, Inches(0), Inches(6.02), SW, Inches(1.48), fill=DARK)
    ticks = [
        "✅  Offline-capable (pre-seeded World Bank cache)",
        "✅  Automatic model selection via sMAPE cross-validation",
        "✅  Bilingual output generated in parallel — not translated",
        "✅  Explainability built in from day one",
        "✅  Production-ready — one-click launch",
    ]
    for i, t in enumerate(ticks):
        x = Inches(0.4 + i * 2.58)
        _tb(s, t, x, Inches(6.14), Inches(2.5), Inches(1.2),
            size=Pt(8.5), color=WHITE, wrap=True)


def slide_06_data_forecast(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Grounded in Real Data · Powered by Six AI Models",
                subtitle="World Bank Open Data API v2 · Expanding-Window Cross-Validation · Automatic Model Selection")
    _rect(s, Inches(0.35), Inches(1.35), Inches(5.7), Inches(5.7),
          fill=WHITE, line_color=NAVY, line_w=Pt(1.2))
    _rect(s, Inches(0.35), Inches(1.35), Inches(5.7), Inches(0.5), fill=NAVY)
    _tb(s, "REAL WORLD BANK DATA",
        Inches(0.5), Inches(1.4), Inches(5.4), Inches(0.4),
        size=Pt(10), bold=True, color=WHITE)
    indicators = [
        ("SL.UEM.1524.ZS", "Youth Unemployment Rate (%)", GREEN),
        ("NY.GDP.MKTP.KD.ZG", "GDP Growth Rate (%)", BLUE),
        ("FP.CPI.TOTL.ZG", "Inflation — CPI (%)", AMBER),
        ("SP.POP.GROW", "Population Growth Rate (%)", TEAL),
        ("IT.NET.USER.ZS", "Internet Users (% of Population)", NAVY),
    ]
    for i, (code, name, col) in enumerate(indicators):
        y = Inches(1.98 + i * 0.62)
        _rect(s, Inches(0.45), y, Inches(0.08), Inches(0.4), fill=col)
        _tb(s, code, Inches(0.6), y + Inches(0.0), Inches(2.4), Inches(0.25),
            size=Pt(8), bold=True, color=col)
        _tb(s, name, Inches(0.6), y + Inches(0.22), Inches(5.1), Inches(0.25),
            size=Pt(8.5), color=DARK)
    _rect(s, Inches(0.45), Inches(5.18), Inches(5.5), Inches(0.35), fill=NAVY)
    _tb(s, "6 GCC NATIONS  ·  SAU · UAE · QAT · KWT · BHR · OMN",
        Inches(0.5), Inches(5.22), Inches(5.3), Inches(0.28),
        size=Pt(8.5), bold=True, color=WHITE)
    _rect(s, Inches(0.45), Inches(5.6), Inches(5.5), Inches(0.35), fill=GREEN)
    _tb(s, "2010–2024  ·  15 annual observations  ·  Offline cache ✓",
        Inches(0.5), Inches(5.64), Inches(5.3), Inches(0.28),
        size=Pt(8.5), bold=True, color=WHITE)
    _rect(s, Inches(0.45), Inches(6.05), Inches(5.5), Inches(0.82), fill=LGRAY, line_color=MGRAY)
    _tb(s, "[ SCREENSHOT: GCC Overview Heatmap — Year-on-Year Change ]",
        Inches(0.55), Inches(6.18), Inches(5.2), Inches(0.55),
        size=Pt(8), color=MGRAY, align=PP_ALIGN.CENTER, italic=True)
    _rect(s, Inches(6.35), Inches(1.35), Inches(6.65), Inches(5.7),
          fill=WHITE, line_color=NAVY, line_w=Pt(1.2))
    _rect(s, Inches(6.35), Inches(1.35), Inches(6.65), Inches(0.5), fill=NAVY)
    _tb(s, "SIX-MODEL AI ENSEMBLE",
        Inches(6.5), Inches(1.4), Inches(6.3), Inches(0.4),
        size=Pt(10), bold=True, color=WHITE)
    models = [
        (MGRAY, "BASELINE", "Naïve", "Last-value persistence benchmark"),
        (MGRAY, "BASELINE", "Seasonal Naïve", "Seasonal pattern replication"),
        (MGRAY, "BASELINE", "Moving Average", "3-period local smoothing"),
        (MGRAY, "BASELINE", "Drift", "Linear trend extrapolation"),
        (BLUE, "STATISTICAL", "SARIMAX", "Seasonal autoregression · AIC order selection"),
        (GOLD, "MACHINE LEARNING", "LightGBM ★",
         "Gradient boosting · lag/rolling/calendar features · quantile intervals"),
    ]
    for i, (col, typ, name, desc) in enumerate(models):
        y = Inches(2.0 + i * 0.77)
        _rect(s, Inches(6.45), y, Inches(0.95), Inches(0.55), fill=col)
        _tb(s, typ, Inches(6.45), y + Inches(0.05), Inches(0.95), Inches(0.4),
            size=Pt(6.5), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _tb(s, name, Inches(7.5), y + Inches(0.03), Inches(2.4), Inches(0.28),
            size=Pt(10.5), bold=True, color=DARK)
        _tb(s, desc, Inches(7.5), y + Inches(0.3), Inches(5.3), Inches(0.28),
            size=Pt(8.5), color=MGRAY)
    _rect(s, Inches(6.45), Inches(6.1), Inches(6.35), Inches(0.65), fill=GREEN)
    _tb(s, "★  Automatic selection: lowest sMAPE on expanding-window holdout folds",
        Inches(6.6), Inches(6.14), Inches(6.0), Inches(0.4),
        size=Pt(9.5), bold=True, color=WHITE)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_07_intelligence(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Ministry-Grade AI Intelligence — English & Arabic",
                subtitle="Bilingual Executive Reports · Risk Classification · Strategic Alerts · Policy Recommendations")
    _rect(s, Inches(0.35), Inches(1.35), SW - Inches(0.7), Inches(0.72), fill=GOLD)
    _tb(s, "AI INTELLIGENCE ENGINE  ·  src/intelligence.py  ·  Generates complete executive intelligence in < 60 seconds",
        Inches(0.6), Inches(1.45), Inches(12.5), Inches(0.5),
        size=Pt(11), bold=True, color=DARK, align=PP_ALIGN.CENTER)
    outputs = [
        (NAVY, "🎯", "RISK CLASSIFICATION",
         "8 dynamic labels assigned per country/indicator",
         ["Stable  ·  Growth Opportunity", "Moderate Risk  ·  High Risk",
          "Recovery Phase  ·  Structural Pressure", "Inflationary Pressure  ·  Labour Volatility"],
         "Based on: trend slope · volatility · target range · recovery pattern"),
        (RED, "⚡", "STRATEGIC ALERTS",
         "Up to 4 contextual alerts per forecast — automatic",
         ["Critical Level Alert (threshold breach)", "YoY Signal Alert (>1.5pp shift detected)",
          "GCC Divergence Alert (>2.5pp from average)", "Target Range Alert (outside optimal band)"],
         "Generated without user prompting — the AI surfaces what matters"),
        (GREEN, "📝", "EXECUTIVE SUMMARY",
         "Full bilingual narrative — not bullet points",
         ["EN: Policy-language analytical narrative", "AR: Formal Modern Standard Arabic (MSA)",
          "RTL formatted for ministerial audiences", "8 sections including causal drivers + recommendations"],
         "Ready to download in 60 seconds — suitable for cabinet briefings"),
        (TEAL, "🔮", "GCC COMPARATIVE INTELLIGENCE",
         "Regional peer benchmarking — automatically generated",
         ["Country vs GCC average analysis", "Regional rank position",
          "Convergence / divergence narrative", "Policy learning across nations"],
         "Bilingual EN + AR · Identifies which countries lead on each indicator"),
    ]
    for i, (col, icon, title, subtitle, bullets, note) in enumerate(outputs):
        row, ci = divmod(i, 2)
        x = Inches(0.35 + ci * 6.5)
        y = Inches(2.22 + row * 2.5)
        _rect(s, x, y, Inches(6.18), Inches(2.3), fill=WHITE, line_color=col, line_w=Pt(2))
        _rect(s, x, y, Inches(0.1), Inches(2.3), fill=col)
        _tb(s, icon + "  " + title, x + Inches(0.22), y + Inches(0.08), Inches(5.7), Inches(0.32),
            size=Pt(11), bold=True, color=col)
        _tb(s, subtitle, x + Inches(0.22), y + Inches(0.38), Inches(5.7), Inches(0.25),
            size=Pt(8.5), color=MGRAY, italic=True)
        tb = s.shapes.add_textbox(x + Inches(0.22), y + Inches(0.66), Inches(5.7), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = "▸  " + b
            r.font.size = Pt(8.5)
            r.font.color.rgb = DARK
        _tb(s, "★  " + note, x + Inches(0.22), y + Inches(1.72), Inches(5.7), Inches(0.42),
            size=Pt(8), color=MGRAY, italic=True)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_08_scenario(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Model the Future Before Committing to It",
                subtitle="Eight Strategic Presets · Elasticity-Based Policy Impact · GCC-Wide Comparative Simulation")
    _rect(s, Inches(0.35), Inches(1.35), SW - Inches(0.7), Inches(0.62), fill=DARK)
    _tb(s,
        "Scenario[t] = Baseline[t] + Σ(elasticity_i × delta_i) × (t / horizon)   ←  linear policy ramp over forecast horizon",
        Inches(0.55), Inches(1.44), Inches(12.5), Inches(0.45),
        size=Pt(10), color=GOLD, align=PP_ALIGN.CENTER, italic=True)
    presets = [
        ("📊", "BASELINE", BG, DARK),
        ("⚡", "DIGITAL ACCELERATION", BLUE, WHITE),
        ("📉", "ECONOMIC SLOWDOWN", RED, WHITE),
        ("🔥", "INFLATION STRESS", AMBER, WHITE),
        ("🏗", "REFORM EXPANSION", GREEN, WHITE),
        ("🌱", "YOUTH RECOVERY", TEAL, WHITE),
        ("👥", "POPULATION SURGE", MGRAY, WHITE),
        ("🚀", "HIGH GROWTH GCC", NAVY, WHITE),
    ]
    chip_w = Inches(3.05)
    chip_h = Inches(0.58)
    for i, (icon, label, col, tcol) in enumerate(presets):
        row, ci = divmod(i, 4)
        x = Inches(0.35 + ci * (chip_w + Inches(0.1)))
        y = Inches(2.12 + row * (chip_h + Inches(0.12)))
        bg_col = GREEN if label == "REFORM EXPANSION" else col
        _rect(s, x, y, chip_w, chip_h, fill=bg_col,
              line_color=GOLD if label == "REFORM EXPANSION" else None, line_w=Pt(2))
        _tb(s, icon + "  " + label, x + Inches(0.1), y, chip_w - Inches(0.1), chip_h,
            size=Pt(9.5), bold=True, color=GOLD if label == "REFORM EXPANSION" else tcol)
    _rect(s, Inches(0.35), Inches(3.58), SW - Inches(0.7), Inches(0.38), fill=GREEN)
    _tb(s, "❆  ACTIVE SCENARIO: Reform Expansion — Labour market reform + education investment + GDP growth",
        Inches(0.55), Inches(3.62), Inches(12.5), Inches(0.3),
        size=Pt(9.5), bold=True, color=WHITE)
    kpis = [
        ("BASELINE END", "13.8%", "Youth unemployment 2027\nno intervention", MGRAY),
        ("SCENARIO END", "11.3%", "Under Reform Expansion\nforecast endpoint", GREEN),
        ("IMPROVEMENT", "−2.5pp", "Percentage point delta\nfrom baseline path", TEAL),
        ("GCC RANK SHIFT", "#4 → #2", "Saudi Arabia rises\namong GCC peers", GOLD),
    ]
    for i, (lbl, val, desc, col) in enumerate(kpis):
        x = Inches(0.35 + i * 3.17)
        y = Inches(4.1)
        _rect(s, x, y, Inches(3.0), Inches(2.78), fill=WHITE, line_color=col, line_w=Pt(2.5))
        _rect(s, x, y, Inches(3.0), Inches(0.38), fill=col)
        _tb(s, lbl, x + Inches(0.1), y + Inches(0.06), Inches(2.8), Inches(0.28),
            size=Pt(8.5), bold=True, color=WHITE)
        _tb(s, val, x, y + Inches(0.55), Inches(3.0), Inches(1.0),
            size=Pt(32), bold=True, color=col, align=PP_ALIGN.CENTER)
        _tb(s, desc, x + Inches(0.12), y + Inches(1.62), Inches(2.75), Inches(0.85),
            size=Pt(8.5), color=MGRAY, wrap=True)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_09_explainability(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "AI That Earns Institutional Trust",
                subtitle="Trust Score · Driver Intelligence · Confidence Classification · Responsible AI Centre")
    _rect(s, Inches(0.35), Inches(1.35), SW - Inches(0.7), Inches(1.1), fill=DARK)
    _rect(s, Inches(0.35), Inches(1.35), Inches(0.12), Inches(1.1), fill=GOLD)
    _tb(s, "TRUST INTELLIGENCE HEADER",
        Inches(0.65), Inches(1.38), Inches(4), Inches(0.35),
        size=Pt(8), bold=True, color=GOLD)
    _rect(s, Inches(0.65), Inches(1.72), Inches(1.2), Inches(0.62), fill=AMBER)
    _tb(s, "74", Inches(0.65), Inches(1.72), Inches(1.2), Inches(0.62),
        size=Pt(32), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _tb(s, "/ 100", Inches(1.9), Inches(1.88), Inches(0.9), Inches(0.3),
        size=Pt(13), color=WHITE)
    _tb(s, "MODERATE CONFIDENCE  ·  LightGBM  ·  sMAPE 6.2%  ·  Saudi Arabia  ·  Youth Unemployment  ·  3-Year Horizon",
        Inches(2.95), Inches(1.84), Inches(10), Inches(0.42), size=Pt(9.5), color=WHITE)
    pillars = [
        (GOLD, "🎯", "TRUST SCORE  0–100",
         ["Composite from sMAPE + interval width + volatility + horizon",
          "sMAPE < 5% → +20pts  ·  > 20% → −22pts",
          "Short horizon ≤ 2yr → +10pts bonus",
          "Policymakers see a single reliable signal"]),
        (BLUE, "🔑", "DRIVER INTELLIGENCE",
         ["LightGBM feature importances → policy narratives",
          "Rank 1: Recent Historical Level (34% influence)",
          "Rank 2: Short-Term Trend Momentum (21%)",
          "14 feature patterns mapped to bilingual explanations"]),
        (NAVY, "📐", "CONFIDENCE TIERS A–E",
         ["A (≥85): High Confidence — strategic planning",
          "B (≥70): Moderate Confidence — directionally reliable",
          "C (≥55): Elevated Uncertainty — use with scenarios",
          "D/E (<55/40): Volatile — indicative only"]),
        (TEAL, "🛡", "RESPONSIBLE AI CENTRE",
         ["Data Sources & Provenance documentation",
          "6 structured Forecast Limitation caveats",
          "Responsible Decision Support principles",
          "Platform Governance Statement — audit-ready"]),
    ]
    for i, (col, icon, title, bullets) in enumerate(pillars):
        row, ci = divmod(i, 2)
        x = Inches(0.35 + ci * 6.5)
        y = Inches(2.6 + row * 2.35)
        _rect(s, x, y, Inches(6.18), Inches(2.18), fill=WHITE, line_color=col, line_w=Pt(2))
        _rect(s, x, y, Inches(6.18), Inches(0.46), fill=col)
        _tb(s, icon + "  " + title, x + Inches(0.18), y + Inches(0.08), Inches(5.8), Inches(0.33),
            size=Pt(10.5), bold=True, color=WHITE)
        tb = s.shapes.add_textbox(x + Inches(0.2), y + Inches(0.56), Inches(5.8), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = "▸  " + b
            r.font.size = Pt(9)
            r.font.color.rgb = DARK
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_10_ux(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Designed for Decision-Makers, Not Data Scientists",
                subtitle="Six-Page Executive Dashboard · Guided Demo Flow · Bilingual UI · Four Export Formats")
    _rect(s, Inches(0.35), Inches(1.38), SW - Inches(0.7), Inches(0.5), fill=NAVY)
    _tb(s, "SIX-STEP STRATEGIC INTELLIGENCE FLOW",
        Inches(0.55), Inches(1.44), Inches(12.5), Inches(0.35),
        size=Pt(9.5), bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    pages = [
        ("1", "🌍 GCC OVERVIEW", "Regional intelligence\nAI risk badges\nHeatmap"),
        ("2", "🔍 COUNTRY EXPLORER", "Deep-dive KPIs\nTrend analysis\nAI alerts"),
        ("3", "📈 FORECAST CENTER", "6-model AI\nTrust score\nConfidence card"),
        ("4", "🤖 AI INSIGHTS", "Executive brief\nEN + AR report\nDownload"),
        ("5", "⚙️ SCENARIO SIM", "8 policy presets\nGCC rank shift\nImpact report"),
        ("6", "🔬 EXPLAINABILITY", "Driver intel\nTransparency\nResponsible AI"),
    ]
    for i, (num, name, desc) in enumerate(pages):
        x = Inches(0.35 + i * 2.17)
        y = Inches(1.95)
        _rect(s, x, y, Inches(2.0), Inches(0.46), fill=GOLD)
        _tb(s, num, x, y, Inches(0.4), Inches(0.46),
            size=Pt(16), bold=True, color=DARK, align=PP_ALIGN.CENTER)
        _tb(s, name, x + Inches(0.42), y + Inches(0.08), Inches(1.55), Inches(0.32),
            size=Pt(7.5), bold=True, color=DARK)
        _rect(s, x, y + Inches(0.46), Inches(2.0), Inches(1.35),
              fill=WHITE, line_color=GOLD, line_w=Pt(1.5))
        _tb(s, desc, x + Inches(0.1), y + Inches(0.55), Inches(1.82), Inches(1.15),
            size=Pt(8.5), color=DARK, wrap=True)
        if i < len(pages) - 1:
            _tb(s, "→", x + Inches(2.02), y + Inches(0.6), Inches(0.14), Inches(0.35),
                size=Pt(12), bold=True, color=NAVY)
    _rect(s, Inches(0.35), Inches(3.95), Inches(8.3), Inches(3.12),
          fill=WHITE, line_color=NAVY, line_w=Pt(1))
    _rect(s, Inches(0.35), Inches(3.95), Inches(8.3), Inches(0.4), fill=NAVY)
    _tb(s, "UX DESIGN PRINCIPLES", Inches(0.55), Inches(4.0), Inches(7.8), Inches(0.3),
        size=Pt(9), bold=True, color=WHITE)
    principles = [
        ("🎯", "Clarity over density", "Strategic narrative over raw metrics — every KPI is contextualised"),
        ("📊", "Premium visual system", "Navy/gold brand · KPI cards · Alert cards · Executive summaries"),
        ("🌐", "Bilingual first-class", "Arabic RTL not an afterthought — a core design requirement"),
        ("📍", "Guided navigation", "Next-step CTAs guide judges through the platform without instruction"),
        ("📥", "Instant exports", "EN brief · EN intel report · AR intel report · Forecast CSV"),
    ]
    for i, (icon, title, desc) in enumerate(principles):
        y = Inches(4.45 + i * 0.51)
        _tb(s, icon, Inches(0.5), y, Inches(0.4), Inches(0.42), size=Pt(14))
        _tb(s, title, Inches(0.98), y, Inches(2.2), Inches(0.25),
            size=Pt(9.5), bold=True, color=DARK)
        _tb(s, desc, Inches(0.98), y + Inches(0.24), Inches(7.5), Inches(0.25),
            size=Pt(8.5), color=MGRAY)
    _rect(s, Inches(8.85), Inches(3.95), Inches(4.15), Inches(3.12),
          fill=LGRAY, line_color=NAVY, line_w=Pt(1))
    _tb(s, "[ SCREENSHOT ]", Inches(8.95), Inches(4.1), Inches(3.95), Inches(0.35),
        size=Pt(8.5), bold=True, color=MGRAY, align=PP_ALIGN.CENTER)
    _tb(s, "GCC Overview — Hero\nAll 6 countries populated\nYouth unemployment selected\nAI risk badges visible",
        Inches(8.95), Inches(4.55), Inches(3.95), Inches(1.8),
        size=Pt(8), color=MGRAY, align=PP_ALIGN.CENTER, italic=True)
    _tb(s, "Replace with platform screenshot for maximum impact",
        Inches(8.95), Inches(6.62), Inches(3.95), Inches(0.3),
        size=Pt(7.5), color=GOLD, align=PP_ALIGN.CENTER, italic=True)
    _footer(s, "GCC AI Intelligence Platform  ·  Competition Submission")


def slide_11_impact(prs):
    s = _blank(prs)
    _bg(s, BG)
    _header_bar(s, "Strategic Value for GCC Decision-Makers",
                subtitle="Immediate · Regional · Long-Term — Three Layers of Societal Impact")
    groups = [
        (NAVY, "🏛", "MINISTRY PLANNERS",
         "GCC Ministries of Labour, Human Resources Development, National Planning",
         ["Evidence-based forecasting replacing intuition",
          "Scenario testing before budget commitment",
          "Bilingual intelligence reports ready for cabinet briefings",
          "Aligned with Vision 2030, UAE Centennial, QNV 2030",
          "Strategic alerts surface issues before they escalate"]),
        (BLUE, "📊", "STATISTICAL AGENCIES",
         "National Statistical Centres, GCC-STAT, Labour Market Observatories",
         ["Unified regional data aggregation platform",
          "Cross-country benchmarking with GCC averages",
          "Exportable validated data tables (CSV)",
          "World Bank certified indicator codes",
          "Offline-capable for field and low-connectivity use"]),
        (TEAL, "🌍", "GCC SECRETARIAT",
         "Regional Policy Coordination, Arab Monetary Fund, Multilateral Bodies",
         ["Six-nation intelligence in one platform",
          "Comparative scenario analysis across all GCC states",
          "Regional convergence / divergence tracking",
          "Policy learning: which countries lead, which lag",
          "Institutional AI governance documentation"]),
    ]
    for i, (col, icon, title, org, bullets) in enumerate(groups):
        x = Inches(0.35 + i * 4.32)
        _rect(s, x, Inches(1.42), Inches(4.1), Inches(0.52), fill=col)
        _tb(s, icon + "  " + title,
            x + Inches(0.12), Inches(1.48), Inches(3.85), Inches(0.4),
            size=Pt(10.5), bold=True, color=WHITE)
        _rect(s, x, Inches(1.96), Inches(4.1), Inches(0.42), fill=LGRAY)
        _tb(s, org, x + Inches(0.12), Inches(1.99), Inches(3.85), Inches(0.36),
            size=Pt(7.5), color=MGRAY, italic=True)
        _rect(s, x, Inches(2.4), Inches(4.1), Inches(4.02),
              fill=WHITE, line_color=col, line_w=Pt(2))
        tb = s.shapes.add_textbox(x + Inches(0.18), Inches(2.55), Inches(3.75), Inches(3.7))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            r = p.add_run()
            r.text = "▸  " + b
            r.font.size = Pt(10)
            r.font.color.rgb = DARK
    _rect(s, Inches(0), Inches(6.55), SW, Inches(0.95), fill=DARK)
    metrics = [("6","Nations"),("5","Indicators"),("15","Years Data"),("6","AI Models"),
               ("8","Scenarios"),("2","Languages"),("4","Exports"),("1","Platform")]
    for i, (val, lbl) in enumerate(metrics):
        x = Inches(0.7 + i * 1.62)
        _tb(s, val, x, Inches(6.6), Inches(1.4), Inches(0.42),
            size=Pt(22), bold=True, color=GOLD, align=PP_ALIGN.CENTER)
        _tb(s, lbl, x, Inches(6.98), Inches(1.4), Inches(0.25),
            size=Pt(8), color=WHITE, align=PP_ALIGN.CENTER)


def slide_12_conclusion(prs):
    s = _blank(prs)
    _bg(s, DARK)
    _rect(s, Inches(0), Inches(0), Inches(0.18), SH, fill=GOLD)
    _rect(s, Inches(0.18), Inches(0), SW - Inches(0.18), Inches(1.35), fill=NAVY2)
    _tb(s, "Production-Ready  ·  Policy-Relevant  ·  Regionally Scalable",
        Inches(0.45), Inches(0.2), Inches(12.5), Inches(0.65),
        size=Pt(26), bold=True, color=WHITE)
    _rect(s, Inches(0.45), Inches(0.9), Inches(8.5), Inches(0.05), fill=GOLD)
    _tb(s, "GCC AI Intelligence Platform  ·  Competition Submission",
        Inches(0.45), Inches(1.0), Inches(12.5), Inches(0.32),
        size=Pt(10), color=GOLD, bold=True)
    _rect(s, Inches(0.35), Inches(1.45), Inches(5.55), Inches(4.55), fill=NAVY)
    _tb(s, "WHAT WE BUILT", Inches(0.55), Inches(1.55), Inches(5.1), Inches(0.4),
        size=Pt(11), bold=True, color=GOLD)
    built = [
        "✅  Real World Bank data pipeline (5 indicators · 6 nations · 15 years)",
        "✅  6-model AI forecasting engine with automatic sMAPE selection",
        "✅  Bilingual executive intelligence — English & Arabic in parallel",
        "✅  8 strategic scenario presets with GCC-wide rank simulation",
        "✅  Trust scoring (0–100) + confidence classification (A–E tiers)",
        "✅  LightGBM driver intelligence → bilingual policy narratives",
        "✅  Responsible AI centre — caveats, governance, transparency",
        "✅  One-click deployment · offline-capable · production-ready",
    ]
    tb = s.shapes.add_textbox(Inches(0.55), Inches(2.05), Inches(5.1), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for b in built:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = b
        r.font.size = Pt(9.5)
        r.font.color.rgb = WHITE
    _rect(s, Inches(6.18), Inches(1.45), Inches(6.8), Inches(4.55), fill=NAVY2)
    _tb(s, "WHAT COMES NEXT", Inches(6.38), Inches(1.55), Inches(6.4), Inches(0.4),
        size=Pt(11), bold=True, color=GOLD)
    next_items = [
        ("🔜  HIGH", "LLM-powered adaptive narratives — Arabic/English policy AI"),
        ("🔜  HIGH", "Quarterly data frequency via IMF/OECD integration"),
        ("🔜  HIGH", "Econometrically-estimated GCC-panel elasticities (VAR/ARDL)"),
        ("🔜  MED",  "PDF export with Ministry-branded layouts (ReportLab)"),
        ("🔜  MED",  "REST API layer for GCC government data portal integration"),
        ("🔜  MED",  "Real-time push alerts when World Bank data triggers changes"),
        ("🔜  LOW",  "MENA-wide coverage extension (15+ countries)"),
    ]
    tb = s.shapes.add_textbox(Inches(6.38), Inches(2.05), Inches(6.4), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for pri, txt in next_items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = pri + "  "
        r.font.size = Pt(8)
        r.font.color.rgb = GOLD
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(9)
        r.font.color.rgb = WHITE
    _rect(s, Inches(0.35), Inches(6.1), SW - Inches(0.7), Inches(1.05), fill=GOLD)
    _tb(s,
        '"An AI-powered GCC strategic intelligence platform for youth employment forecasting and evidence-based policy planning —\n'
        'transparent, bilingual, and institutionally ready for the people shaping the workforce future of 60 million people across the Gulf."',
        Inches(0.6), Inches(6.18), SW - Inches(1.0), Inches(0.9),
        size=Pt(11.5), bold=True, color=DARK, italic=True, align=PP_ALIGN.CENTER)


def build():
    prs = _new_prs()
    print("Building slides...")
    slide_01_title(prs)        ; print("  ✓ Slide  1 — Title & Vision")
    slide_02_problem(prs)      ; print("  ✓ Slide  2 — Problem Statement")
    slide_03_why(prs)          ; print("  ✓ Slide  3 — Why It Matters")
    slide_04_platform(prs)     ; print("  ✓ Slide  4 — Platform Overview")
    slide_05_architecture(prs) ; print("  ✓ Slide  5 — System Architecture")
    slide_06_data_forecast(prs); print("  ✓ Slide  6 — Data & Forecasting")
    slide_07_intelligence(prs) ; print("  ✓ Slide  7 — AI Intelligence")
    slide_08_scenario(prs)     ; print("  ✓ Slide  8 — Scenario Simulation")
    slide_09_explainability(prs);print("  ✓ Slide  9 — Explainability & Trust")
    slide_10_ux(prs)           ; print("  ✓ Slide 10 — Dashboard & UX")
    slide_11_impact(prs)       ; print("  ✓ Slide 11 — Societal Impact")
    slide_12_conclusion(prs)   ; print("  ✓ Slide 12 — Conclusion")
    os.makedirs("presentation", exist_ok=True)
    out = os.path.join("presentation", "GCC_AI_Intelligence_Platform.pptx")
    prs.save(out)
    print(f"\n✅  Saved: {out}")
    return out


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Generate Technical Report PDF using ReportLab."""

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

OUTPUT = "presentation/GCC_AI_Intelligence_Platform_Technical_Report.pdf"

NAVY  = colors.HexColor('#1B4F72')
GOLD  = colors.HexColor('#C39B4E')
DARK  = colors.HexColor('#091320')
WHITE = colors.white
LGRAY = colors.HexColor('#F4F6F9')
MGRAY = colors.HexColor('#777777')
BGRAY = colors.HexColor('#EEF2F7')

W, H = A4

def make_styles():
    styles = {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=26, textColor=NAVY, spaceAfter=6, alignment=TA_CENTER, leading=32),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica', fontSize=13, textColor=GOLD, spaceAfter=4, alignment=TA_CENTER),
        'meta_value': ParagraphStyle('meta_value', fontName='Helvetica', fontSize=10, textColor=DARK, spaceAfter=2, alignment=TA_CENTER),
        'h1': ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=14, textColor=NAVY, spaceBefore=14, spaceAfter=4),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11.5, textColor=NAVY, spaceBefore=10, spaceAfter=3),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10, textColor=DARK, spaceBefore=2, spaceAfter=4, leading=14, alignment=TA_JUSTIFY),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=10, textColor=DARK, spaceBefore=1, spaceAfter=1, leading=13, leftIndent=18),
        'code': ParagraphStyle('code', fontName='Courier', fontSize=8, textColor=DARK, spaceBefore=4, spaceAfter=4, leading=11, leftIndent=12, backColor=BGRAY, borderPadding=6),
        'footer': ParagraphStyle('footer', fontName='Helvetica-Oblique', fontSize=8, textColor=MGRAY, alignment=TA_CENTER, spaceBefore=4),
        'italic_note': ParagraphStyle('italic_note', fontName='Helvetica-Oblique', fontSize=10, textColor=NAVY, spaceBefore=2, spaceAfter=4),
    }
    return styles

S = make_styles()

def H1(text):
    return KeepTogether([Paragraph(text, S['h1']), HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=4)])
def H2(text): return Paragraph(text, S['h2'])
def Body(text): return Paragraph(text, S['body'])
def Bullet(text, bold_prefix=None):
    if bold_prefix:
        return Paragraph(f'• <b>{bold_prefix}</b>{text}', S['body'])
    return Paragraph(f'• {text}', S['bullet'])
def Code(text): return Paragraph(text.replace('\n','<br/>'), S['code'])
def Gap(h=6): return Spacer(1, h)
def ItalicNote(text): return Paragraph(text, S['italic_note'])

def make_table(headers, rows, col_widths=None, header_bg=NAVY):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [16.5 * cm / len(headers)] * len(headers)
    else:
        col_widths = [w * cm for w in col_widths]
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (1,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (1,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LGRAY, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(style)
    return t

def on_page(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(DARK)
        canvas.rect(0, H - 1.0*cm, W, 1.0*cm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, H - 1.0*cm - 2, W, 2, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawString(1.5*cm, H - 0.7*cm, 'GCC AI Intelligence Platform')
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(W - 1.5*cm, H - 0.7*cm, 'Technical Report — Competition Submission')
        canvas.setFillColor(MGRAY)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(1.5*cm, 0.7*cm, 'World Bank Open Data · Responsible AI for Gulf Policy Planning')
        canvas.drawRightString(W - 1.5*cm, 0.7*cm, f'Page {doc.page}')
        canvas.setFillColor(NAVY)
        canvas.rect(0, 1.1*cm, W, 1, fill=1, stroke=0)
    canvas.restoreState()

def build():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4, leftMargin=2.0*cm, rightMargin=2.0*cm, topMargin=1.8*cm, bottomMargin=1.8*cm)
    story = []
    # Title page
    story.append(HRFlowable(width='100%', thickness=6, color=GOLD, spaceAfter=0))
    story.append(Gap(50))
    story.append(Paragraph('GCC AI Intelligence Platform', S['title']))
    story.append(Gap(4))
    story.append(Paragraph('Technical Report — Competition Submission', S['subtitle']))
    story.append(Gap(20))
    story.append(HRFlowable(width='60%', thickness=1, color=GOLD, spaceAfter=20))
    story.append(Gap(10))
    for label, value in [
        ('Platform', 'GCC AI Strategic Intelligence Platform'),
        ('Focus', 'AI-Powered Youth Employment Forecasting & Policy Decision Support'),
        ('Data Source', 'World Bank Open Data API v2'),
        ('Coverage', '6 GCC Nations · 5 Indicators · 2010–2024'),
        ('Languages', 'English · Arabic (Ministry-Grade Bilingual Output)'),
        ('Participant', 'Yahya Al-washahi'),
    ]:
        story.append(Paragraph(f'<b>{label}:</b>  {value}', S['meta_value']))
        story.append(Gap(2))
    story.append(Gap(80))
    story.append(HRFlowable(width='100%', thickness=4, color=NAVY, spaceAfter=0))
    story.append(PageBreak())
    # Sections
    story += [H1('1. Executive Summary'), Body('The GCC AI Intelligence Platform is an end-to-end AI-powered statistical intelligence system designed to support youth employment forecasting and strategic policy planning across the six Gulf Cooperation Council nations: Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, and Oman.'), Body('The platform combines real World Bank Open Data, a six-model ensemble forecasting engine with automatic model selection, an AI-generated bilingual executive intelligence layer, elasticity-based policy scenario simulation, and a complete explainability and trust framework.'), Body('<b>Key capabilities:</b>')] + [Bullet(b) for b in ['Real-time GCC regional intelligence dashboard with AI risk classification', 'Multi-model time-series forecasting with expanding-window cross-validation', 'Bilingual (English/Arabic) AI-generated ministerial intelligence reports', 'Eight curated strategic policy scenario presets with GCC-wide impact analysis', 'Transparent AI: trust scoring, driver intelligence, confidence classification, and Responsible AI centre', 'Fully offline-capable with pre-seeded World Bank data cache']]
    story += [H1('2. Problem Statement'), H2('2.1 The GCC Youth Employment Challenge'), Body('Youth unemployment across the six GCC member states ranges from under 5% (UAE, Qatar) to over 25% (Saudi Arabia, Oman), driven by skills mismatches, public-sector dependency, demographic pressure, and oil-price volatility.'), H2('2.2 The Policy Intelligence Gap'), Body('GCC policymakers face five critical gaps:')] + [Paragraph(f'• <b>{b}:</b> {d}', S['body']) for b, d in [('Fragmented data', 'Statistics scattered across national agencies, World Bank, ILO, OECD'), ('No regional comparative view', 'No platform for real-time GCC peer benchmarking'), ('No forward-looking intelligence', 'Reporting is retrospective — no AI-powered predictive signals'), ('No scenario modelling', 'Cannot model employment impact of specific interventions'), ('No bilingual executive layer', 'English insights inaccessible to Arabic-speaking ministry audiences')]] + [ItalicNote('This platform was built to close all five gaps simultaneously.')]
    story += [H1('3. Project Objectives'), make_table(['Objective', 'Outcome'], [['Aggregate real GCC labour-market data', 'Live World Bank API pipeline with offline-capable cache'], ['Enable regional comparative intelligence', 'Six-country dashboard with rankings, heatmaps, GCC averages'], ['Deliver AI-powered forward-looking forecasts', 'Six-model ensemble with automatic selection and prediction intervals'], ['Generate interpretable, actionable intelligence', 'AI-written bilingual executive reports with risk classification'], ['Enable policy scenario modelling', 'Eight strategic presets with elasticity-based impact simulation'], ['Build institutional trust', 'Trust scoring, confidence classification, Responsible AI centre'], ['Support Arabic-first reporting', 'RTL-formatted Arabic executive reports']], col_widths=[8.5, 8.0])]
    story += [H1('5. Innovation & Creative Distinction'), H2('5.1 Six-Model AI Ensemble'), make_table(['Model', 'Type', 'Strength'], [['Naïve', 'Baseline', 'Last-value persistence'], ['Seasonal Naïve', 'Baseline', 'Seasonal pattern replication'], ['Moving Average', 'Baseline', 'Local smoothing'], ['Drift', 'Baseline', 'Linear trend extrapolation'], ['SARIMAX', 'Statistical', 'Seasonal autoregression with AIC order selection'], ['LightGBM', 'Machine Learning', 'Gradient boosting with lag/rolling/calendar features']], col_widths=[4.0, 4.0, 8.5]), H2('5.2 AI Intelligence Layer')] + [Paragraph(f'• <b>{b}:</b> {d}', S['body']) for b, d in [('Dynamic Risk Classification', '8 labels per country/indicator based on trend, volatility, target range'), ('Strategic Alert System', 'Up to 4 contextual alerts per forecast — generated automatically'), ('Bilingual Narratives', 'Executive summaries in English and formal Arabic MSA'), ('Explainability', 'Trust score 0–100, confidence tiers A–E, LightGBM driver narratives')]]
    story += [H1('6. GCC Relevance & Societal Impact'), make_table(['Country', 'Vision', 'Platform Alignment'], [['Saudi Arabia', 'Vision 2030', 'Youth employment forecasting, private sector simulation'], ['UAE', 'UAE Centennial 2071', 'Digital acceleration, talent pipeline intelligence'], ['Qatar', 'QNV 2030', 'Post-2022 economic diversification modelling'], ['Kuwait', 'Kuwait Vision 2035', 'Public-private employment balance analysis'], ['Bahrain', 'Economic Vision 2030', 'Labour market reform impact simulation'], ['Oman', 'Oman Vision 2040', 'Youth-to-workforce transition forecasting']], col_widths=[3.0, 4.0, 9.5])]
    story += [H1('8. Data Sources'), make_table(['Indicator', 'World Bank Code', 'Coverage'], [['Youth Unemployment Rate (%)', 'SL.UEM.1524.ZS', '2010–2024'], ['GDP Growth Rate (%)', 'NY.GDP.MKTP.KD.ZG', '2010–2024'], ['Inflation — CPI (%)', 'FP.CPI.TOTL.ZG', '2010–2024'], ['Population Growth Rate (%)', 'SP.POP.GROW', '2010–2024'], ['Internet Users (% of Population)', 'IT.NET.USER.ZS', '2010–2024']], col_widths=[7.0, 5.0, 4.5])]
    story += [H1('11. Scenario Simulation'), H2('Eight Strategic Presets'), make_table(['Preset', 'Type', 'GDP', 'Digital', 'Education', 'Labour', 'Pop'], [['Baseline', 'Neutral', '0', '0', '0', '0', '0'], ['Digital Acceleration', 'Opportunity', '+2.0', '+5.0', '+3.0', '+2.0', '0'], ['Economic Slowdown', 'Risk', '−3.0', '−2.0', '−1.0', '−1.0', '0'], ['Reform Expansion', 'Opportunity', '+1.0', '+2.0', '+5.0', '+4.0', '0'], ['High Growth GCC', 'Opportunity', '+4.0', '+5.0', '+4.0', '+4.0', '+0.5']], col_widths=[4.5, 2.8, 1.5, 1.5, 1.8, 2.0, 2.4])]
    story += [H1('13. Tools & Technologies'), make_table(['Category', 'Technology', 'Purpose'], [['Language', 'Python 3.10+', 'Core application language'], ['Dashboard', 'Streamlit', 'Interactive web dashboard'], ['Data', 'World Bank Open Data API v2', 'Primary official data source'], ['Data Processing', 'pandas, numpy', 'Data manipulation and time-series'], ['Visualisation', 'Plotly Express', 'Interactive charts and maps'], ['Statistical ML', 'statsmodels + LightGBM', 'SARIMAX + gradient boosting'], ['Version Control', 'Git / GitHub', 'Source control'], ['Deployment', 'Streamlit Community Cloud', 'Cloud hosting']], col_widths=[4.0, 5.0, 7.5])]
    story += [H1('14. Conclusion'), Body('The GCC AI Intelligence Platform delivers AI-powered, bilingual, explainable employment intelligence designed specifically for GCC policymakers — production-ready, offline-capable, and institutionally trustworthy.')] + [Bullet(b) for b in ['Real World Bank data · 6 nations · 5 indicators · 15 years', '6-model AI ensemble with automatic selection', 'Bilingual executive intelligence in English and Arabic', '8 strategic scenario presets with GCC-wide rank simulation', 'Trust score 0–100 + confidence tiers A–E + Responsible AI centre']] + [Gap(16), HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=8), Paragraph('GCC AI Intelligence Platform · Yahya Al-washahi · World Bank Open Data · Responsible AI for Gulf Policy Planning', S['footer'])]
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'✅  PDF saved: {OUTPUT}')

if __name__ == '__main__':
    build()

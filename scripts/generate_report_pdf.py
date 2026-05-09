#!/usr/bin/env python3
"""Generate Technical Report PDF using ReportLab — run from project root."""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

OUTPUT = "presentation/GCC_AI_Intelligence_Platform_Technical_Report.pdf"
NAVY=colors.HexColor('#1B4F72'); GOLD=colors.HexColor('#C39B4E'); DARK=colors.HexColor('#091320')
WHITE=colors.white; LGRAY=colors.HexColor('#F4F6F9'); MGRAY=colors.HexColor('#777777'); BGRAY=colors.HexColor('#EEF2F7')
W,H=A4

S={
 'title':ParagraphStyle('t',fontName='Helvetica-Bold',fontSize=26,textColor=NAVY,spaceAfter=6,alignment=TA_CENTER,leading=32),
 'subtitle':ParagraphStyle('s',fontName='Helvetica',fontSize=13,textColor=GOLD,spaceAfter=4,alignment=TA_CENTER),
 'meta':ParagraphStyle('m',fontName='Helvetica',fontSize=10,textColor=DARK,spaceAfter=2,alignment=TA_CENTER),
 'h1':ParagraphStyle('h1',fontName='Helvetica-Bold',fontSize=14,textColor=NAVY,spaceBefore=14,spaceAfter=4),
 'h2':ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=11.5,textColor=NAVY,spaceBefore=10,spaceAfter=3),
 'body':ParagraphStyle('b',fontName='Helvetica',fontSize=10,textColor=DARK,spaceBefore=2,spaceAfter=4,leading=14,alignment=TA_JUSTIFY),
 'bullet':ParagraphStyle('bl',fontName='Helvetica',fontSize=10,textColor=DARK,spaceBefore=1,spaceAfter=1,leading=13,leftIndent=18),
 'code':ParagraphStyle('c',fontName='Courier',fontSize=8,textColor=DARK,spaceBefore=4,spaceAfter=4,leading=11,leftIndent=12,backColor=BGRAY,borderPadding=6),
 'footer':ParagraphStyle('f',fontName='Helvetica-Oblique',fontSize=8,textColor=MGRAY,alignment=TA_CENTER,spaceBefore=4),
 'note':ParagraphStyle('n',fontName='Helvetica-Oblique',fontSize=10,textColor=NAVY,spaceBefore=2,spaceAfter=4),
}

def H1(t): return KeepTogether([Paragraph(t,S['h1']),HRFlowable(width='100%',thickness=1.5,color=GOLD,spaceAfter=4)])
def H2(t): return Paragraph(t,S['h2'])
def Body(t): return Paragraph(t,S['body'])
def Bul(t,b=None): return Paragraph(f'• <b>{b}</b>{t}' if b else f'• {t}',S['body'] if b else S['bullet'])
def Code(t): return Paragraph(t.replace('\n','<br/>'),S['code'])
def Gap(h=6): return Spacer(1,h)
def Note(t): return Paragraph(t,S['note'])

def tbl(headers,rows,widths=None,bg=NAVY):
    data=[headers]+rows
    w=[16.5*cm/len(headers)]*len(headers) if not widths else [x*cm for x in widths]
    t=Table(data,colWidths=w,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),bg),('TEXTCOLOR',(0,0),(-1,0),WHITE),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),9),('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('FONTNAME',(1,1),(-1,-1),'Helvetica'),('FONTSIZE',(1,1),(-1,-1),9),('ROWBACKGROUNDS',(0,1),(-1,-1),[LGRAY,WHITE]),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#CCCCCC')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

def on_page(canvas,doc):
    canvas.saveState()
    if doc.page>1:
        canvas.setFillColor(DARK); canvas.rect(0,H-cm,W,cm,fill=1,stroke=0)
        canvas.setFillColor(GOLD); canvas.rect(0,H-cm-2,W,2,fill=1,stroke=0)
        canvas.setFillColor(WHITE); canvas.setFont('Helvetica-Bold',9); canvas.drawString(1.5*cm,H-0.7*cm,'GCC AI Intelligence Platform')
        canvas.setFont('Helvetica',9); canvas.drawRightString(W-1.5*cm,H-0.7*cm,'Technical Report — Competition Submission')
        canvas.setFillColor(MGRAY); canvas.setFont('Helvetica',8)
        canvas.drawString(1.5*cm,0.7*cm,'World Bank Open Data · Responsible AI for Gulf Policy Planning')
        canvas.drawRightString(W-1.5*cm,0.7*cm,f'Page {doc.page}')
        canvas.setFillColor(NAVY); canvas.rect(0,1.1*cm,W,1,fill=1,stroke=0)
    canvas.restoreState()

def build():
    os.makedirs(os.path.dirname(OUTPUT),exist_ok=True)
    doc=SimpleDocTemplate(OUTPUT,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm)
    s=[HRFlowable(width='100%',thickness=6,color=GOLD),Gap(50),Paragraph('GCC AI Intelligence Platform',S['title']),Gap(4),Paragraph('Technical Report — Competition Submission',S['subtitle']),Gap(20),HRFlowable(width='60%',thickness=1,color=GOLD,spaceAfter=20),Gap(10)]
    for l,v in [('Platform','GCC AI Strategic Intelligence Platform'),('Focus','AI-Powered Youth Employment Forecasting & Policy Decision Support'),('Data Source','World Bank Open Data API v2'),('Coverage','6 GCC Nations · 5 Indicators · 2010–2024'),('Languages','English · Arabic (Ministry-Grade Bilingual Output)'),('Participant','Yahya Al-washahi')]:
        s+=[Paragraph(f'<b>{l}:</b>  {v}',S['meta']),Gap(2)]
    s+=[Gap(60),HRFlowable(width='100%',thickness=4,color=NAVY),PageBreak()]
    s+=[H1('1. Executive Summary'),Body('The GCC AI Intelligence Platform is an end-to-end AI-powered statistical intelligence system designed to support youth employment forecasting and strategic policy planning across the six Gulf Cooperation Council nations: Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, and Oman.'),Body('The platform combines real World Bank Open Data, a six-model ensemble forecasting engine with automatic model selection, an AI-generated bilingual executive intelligence layer, elasticity-based policy scenario simulation, and a complete explainability and trust framework.')]
    s+=[Bul(b) for b in ['Real-time GCC regional intelligence dashboard with AI risk classification','Multi-model time-series forecasting with expanding-window cross-validation','Bilingual (English/Arabic) AI-generated ministerial intelligence reports','Eight curated strategic policy scenario presets with GCC-wide impact analysis','Transparent AI: trust scoring, driver intelligence, confidence classification, Responsible AI centre','Fully offline-capable with pre-seeded World Bank data cache']]
    s+=[H1('2. Problem Statement'),H2('2.1 The GCC Youth Employment Challenge'),Body('Youth unemployment across the six GCC member states ranges from under 5% (UAE, Qatar) to over 25% (Saudi Arabia, Oman), driven by skills mismatches, public-sector dependency, rapid demographic growth, and oil-price volatility.'),H2('2.2 The Policy Intelligence Gap')]
    s+=[Paragraph(f'• <b>{b}:</b> {d}',S['body']) for b,d in [('Fragmented data','Statistics scattered across national agencies, World Bank, ILO, OECD — no unified view'),('No regional comparative view','No platform for real-time GCC peer benchmarking'),('No forward-looking intelligence','All reporting is retrospective — no AI-powered predictive signals'),('No scenario modelling','Cannot model employment impact of specific policy interventions'),('No bilingual executive layer','English insights inaccessible to Arabic-speaking ministry audiences')]]
    s+=[Note('This platform was built to close all five gaps simultaneously.')]
    s+=[H1('3. Project Objectives'),tbl(['Objective','Outcome'],[['Aggregate real GCC labour-market data','Live World Bank API pipeline with offline-capable cache'],['Enable regional comparative intelligence','Six-country dashboard with rankings, heatmaps, GCC averages'],['Deliver AI-powered forward-looking forecasts','Six-model ensemble with automatic selection and prediction intervals'],['Generate interpretable, actionable intelligence','AI-written bilingual executive reports with risk classification'],['Enable policy scenario modelling','Eight strategic presets with elasticity-based impact simulation'],['Build institutional trust through transparency','Trust scoring, confidence classification, Responsible AI centre'],['Support Arabic-first ministry reporting','RTL-formatted Arabic executive reports in standard formats']],widths=[8.5,8.0])]
    s+=[H1('4. Proposed Solution')]+[Paragraph(f'• <b>{t}:</b> {d}',S['body']) for t,d in [('Principle 1 — Real Data, Not Synthetic','All intelligence derived from verified World Bank Open Data API v2. No synthetic data used.'),('Principle 2 — AI That Explains Itself','Every forecast includes confidence classification, driver narrative, model quality assessment, and caveats.'),('Principle 3 — Bilingual from the Ground Up','English and Arabic outputs generated in parallel using formal Modern Standard Arabic for ministerial audiences.'),('Principle 4 — Designed for Decision-Makers','Interface and language optimised for GCC policy planners, not data scientists.'),('Principle 5 — Transparent and Accountable','Model selection, data sources, limitations, and uncertainty prominently communicated.')]]
    s+=[H1('5. Innovation & Creative Distinction'),H2('5.1 Six-Model AI Ensemble with Automatic Selection'),tbl(['Model','Type','Strength'],[['Naïve','Baseline','Last-value persistence'],['Seasonal Naïve','Baseline','Seasonal pattern replication'],['Moving Average','Baseline','Local smoothing'],['Drift','Baseline','Linear trend extrapolation'],['SARIMAX','Statistical','Seasonal autoregression with AIC order selection'],['LightGBM','Machine Learning','Gradient boosting with lag/rolling/calendar features']],widths=[4.0,4.0,8.5]),H2('5.2 AI Strategic Intelligence & Explainability')]
    s+=[Paragraph(f'• <b>{b}:</b> {d}',S['body']) for b,d in [('Dynamic Risk Classification','8 labels per country/indicator: Stable, Moderate Risk, High Risk, Recovery Phase, Structural Pressure, Growth Opportunity, Inflationary Pressure, Labour Volatility'),('Strategic Alert System','Up to 4 contextual alerts per forecast — critical triggers, YoY signals, GCC divergence, target range breach'),('Trust Score 0–100','Composite from sMAPE, interval width, data volatility, and forecast horizon — five confidence tiers A–E'),('Bilingual Driver Intelligence','LightGBM feature importances mapped to policy narratives in English and Arabic')]]
    s+=[H1('6. GCC Relevance & Societal Impact'),tbl(['Country','Vision','Platform Alignment'],[['Saudi Arabia','Vision 2030','Youth employment forecasting, private sector growth simulation'],['UAE','UAE Centennial 2071','Digital acceleration scenario, talent pipeline intelligence'],['Qatar','QNV 2030','Post-2022 economic diversification modelling'],['Kuwait','Kuwait Vision 2035','Public-private employment balance analysis'],['Bahrain','Economic Vision 2030','Labour market reform impact simulation'],['Oman','Oman Vision 2040','Youth-to-workforce transition forecasting']],widths=[3.0,4.0,9.5])]
    s+=[H1('7. System Architecture'),H2('Five-Layer Data-to-Intelligence Pipeline')]+[Bul(b) for b in ['World Bank Open Data API v2 → 5 indicators × 6 GCC nations × 15 years','Data Layer (src/wb_data.py) → API client, CSV caching, offline resilience','Forecasting Engine (src/models/) → 6-model ensemble with expanding-window cross-validation','AI Intelligence Layer (src/intelligence.py) → Risk classification, alerts, bilingual narratives, trust scoring','Streamlit Dashboard (app.py) → 6 pages, Plotly charts, bilingual UI, export system']]
    s+=[H1('8. Data Sources — World Bank Open Data'),tbl(['Indicator','World Bank Code','Coverage'],[['Youth Unemployment Rate (%)','SL.UEM.1524.ZS','2010–2024'],['GDP Growth Rate (%)','NY.GDP.MKTP.KD.ZG','2010–2024'],['Inflation — CPI (%)','FP.CPI.TOTL.ZG','2010–2024'],['Population Growth Rate (%)','SP.POP.GROW','2010–2024'],['Internet Users (% of Population)','IT.NET.USER.ZS','2010–2024']],widths=[7.0,5.0,4.5])]
    s+=[H1('11. Scenario Simulation Engine'),Body('Eight curated scenario presets apply elasticity-based adjustments to baseline forecasts, linearly ramped over the forecast horizon. Each generates a GCC-wide rank table across all 6 nations.'),tbl(['Preset','Type','GDP','Digital','Education','Labour','Pop'],[['Baseline','Neutral','0','0','0','0','0'],['Digital Acceleration','Opportunity','+2.0','+5.0','+3.0','+2.0','0'],['Economic Slowdown','Risk','−3.0','−2.0','−1.0','−1.0','0'],['Inflation Stress','Warning','−1.5','−1.0','−0.5','0','+0.5'],['Reform Expansion','Opportunity','+1.0','+2.0','+5.0','+4.0','0'],['Youth Recovery','Opportunity','+1.0','+1.0','+3.0','+3.0','0'],['Population Surge','Pressure','0','0','0','0','+2.5'],['High Growth GCC','Opportunity','+4.0','+5.0','+4.0','+4.0','+0.5']],widths=[4.5,2.8,1.5,1.5,1.8,2.0,2.4])]
    s+=[H1('12. Results & Outputs'),H2('Sample Intelligence Output — Saudi Arabia Youth Unemployment')]+[Paragraph(f'• <b>{b}:</b> {v}',S['body']) for b,v in [('Risk Profile','Moderate Risk — improving but above target range'),('Trend','Improving (−0.8pp YoY)'),('Strategic Alerts','3 active: YoY Signal, GCC Divergence (−4.9pp), Target Range breach'),('Model Selected','LightGBM, sMAPE 6.2% (Tier B — Moderate Confidence)'),('Trust Score','74 / 100'),('3-Year Forecast','12.8% (80% prediction interval: 10.4%–15.2%)')]]
    s+=[H1('13. Tools & Technologies'),tbl(['Category','Technology','Purpose'],[['Language','Python 3.10+','Core application language'],['Dashboard','Streamlit','Interactive web dashboard framework'],['Data','World Bank Open Data API v2','Primary official data source'],['Data Processing','pandas, numpy','Data manipulation and time-series processing'],['Visualisation','Plotly Express / Graph Objects','Interactive charts and maps'],['Statistical ML','statsmodels (SARIMAX)','Seasonal autoregression'],['Machine Learning','LightGBM','Gradient boosting forecasting engine'],['Version Control','Git / GitHub','Source control and collaboration'],['Deployment','Streamlit Community Cloud','Cloud hosting and demo access']],widths=[4.0,5.0,7.5])]
    s+=[H1('14. Conclusion'),Body('The GCC AI Intelligence Platform delivers AI-powered, bilingual, explainable employment intelligence designed specifically for GCC policymakers — production-ready, offline-capable, and institutionally trustworthy.')]+[Bul(b) for b in ['Real World Bank data · 6 nations · 5 indicators · 15 years','6-model AI ensemble with automatic sMAPE selection','Bilingual executive intelligence in English and Arabic (formal MSA)','8 strategic scenario presets with GCC-wide rank simulation','Trust score 0–100 + confidence tiers A–E + full Responsible AI centre','One-click deployment · offline-capable · production-ready']]+[Gap(16),HRFlowable(width='100%',thickness=1,color=GOLD,spaceAfter=8),Paragraph('GCC AI Intelligence Platform · Yahya Al-washahi · World Bank Open Data · Responsible AI for Gulf Policy Planning',S['footer'])]
    doc.build(s,onFirstPage=on_page,onLaterPages=on_page)
    print(f'✅  PDF saved: {OUTPUT}')

if __name__=='__main__': build()

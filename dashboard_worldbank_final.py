"""
Tableau de Bord Banque Mondiale - Style Professionnel
Dashboard interactif pour les indicateurs de développement - Zone UEMOA
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import os

# Configuration Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Connexion MongoDB
client, db = get_mongo_db()

# Indicateurs clés (KPI selon votre spécification)
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "Taux de croissance du PIB",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    "SI.POV.DDAY": "Taux de pauvreté (1,90 USD/jour)",
    "SH.XPD.GHED.GD.ZS": "Dépenses publiques santé (% PIB)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses publiques éducation (% PIB)",
    "NY.GDP.MKTP.CD": "PIB total (USD)",
    "FP.CPI.TOTL.ZG": "Inflation (CPI %)",
    "GC.DOD.TOTL.GD.ZS": "Dette publique (% PIB)",
    "SP.POP.TOTL": "Population totale",
}

# Pays UEMOA
UEMOA_COUNTRIES = {
    "BEN": "Bénin", "BFA": "Burkina Faso", "CIV": "Côte d'Ivoire",
    "GNB": "Guinée-Bissau", "MLI": "Mali", "NER": "Niger",
    "SEN": "Sénégal", "TGO": "Togo"
}

# Couleurs
COLORS = {
    'background': '#0e1117', 'surface': '#1a1f2e', 'primary': '#4CAF50',
    'secondary': '#2196F3', 'text': '#E0E0E0', 'text_secondary': '#9E9E9E',
    'success': '#4CAF50', 'warning': '#FF9800', 'error': '#F44336', 'grid': '#2a2f3e'
}

def get_wb_data():
    """Récupère données WB depuis MongoDB (curated_observations)"""
    obs = db['curated_observations']
    cursor = obs.find({'source': {'$in': ['worldbank', 'WorldBank']}})
    
    records = []
    for o in cursor:
        try:
            records.append({
                'indicator': o.get('attrs', {}).get('indicator', o.get('dataset')),
                'country': o.get('attrs', {}).get('country'),
                'year': pd.to_datetime(o['ts']).year,
                'value': float(o['value'])
            })
        except: continue
    
    return pd.DataFrame(records)

# Charger données
df_wb = get_wb_data()
print(f"✅ Chargé {len(df_wb)} observations Banque Mondiale")

# Application Dash
app = dash.Dash(__name__)
app.title = "Banque Mondiale - UEMOA"

# Layout
app.layout = html.Div(style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'}, children=[
    # Header
    html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.H1("🌍 BANQUE MONDIALE", 
                style={'color': COLORS['text'], 'marginBottom': '5px', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
        html.P("Indicateurs de développement - Zone UEMOA",
                style={'color': COLORS['text_secondary'], 'fontSize': '1.1rem'})
    ]),
    
    # Filtres
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
            html.Div([
                html.Label("🌍 Sélectionner un pays:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Dropdown(id='country-selector',
                           options=[{'label': name, 'value': code} for code, name in UEMOA_COUNTRIES.items()],
                           value='CIV', clearable=False)
            ]),
            html.Div([
                html.Label("📅 Sélectionner une année:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Dropdown(id='year-selector', clearable=False)
            ])
        ])
    ]),
    
    # KPI Cards
    html.Div(id='kpi-cards', style={'marginBottom': '20px'}),
    
    # Graphiques
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Évolution temporelle des indicateurs", style={'color': COLORS['text'], 'marginBottom': '20px'}),
            dcc.Graph(id='time-chart', style={'height': '400px'})
        ]),
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Classement UEMOA", style={'color': COLORS['text'], 'marginBottom': '20px'}),
            dcc.Graph(id='ranking-chart', style={'height': '400px'})
        ])
    ]),
    
    # Comparaison pays
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.H3("Comparaison multi-pays", style={'color': COLORS['text'], 'marginBottom': '20px'}),
        dcc.Dropdown(id='indicator-selector',
                   options=[{'label': name, 'value': code} for code, name in INDICATORS.items()],
                   value='NY.GDP.MKTP.KD.ZG', clearable=False,
                   style={'marginBottom': '20px'}),
        dcc.Graph(id='comparison-chart', style={'height': '400px'})
    ]),
    
    # Tableau détaillé
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
        html.H3("Données détaillées", style={'color': COLORS['text'], 'marginBottom': '20px'}),
        html.Div(id='data-table')
    ]),
    
    dcc.Store(id='data-store', data=df_wb.to_dict('records')),
    dcc.Interval(id='interval', interval=60000, n_intervals=0)
])

# Callbacks
@app.callback(
    [Output('year-selector', 'options'), Output('year-selector', 'value')],
    Input('data-store', 'data')
)
def update_years(data):
    if not data: return [], None
    df = pd.DataFrame(data)
    years = sorted(df['year'].unique(), reverse=True)
    options = [{'label': str(int(y)), 'value': int(y)} for y in years]
    return options, int(years[0]) if years else None

@app.callback(
    Output('kpi-cards', 'children'),
    [Input('data-store', 'data'), Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_kpi(data, country, year):
    if not data or not year: return html.Div("Chargement...", style={'color': COLORS['text_secondary']})
    
    df = pd.DataFrame(data)
    df_fil = df[(df['country'] == country) & (df['year'] == year)]
    
    def get_val(code):
        row = df_fil[df_fil['indicator'] == code]
        return row['value'].iloc[0] if not row.empty else None
    
    croissance = get_val("NY.GDP.MKTP.KD.ZG")
    rnb = get_val("NY.GNP.PCAP.CD")
    pauvrete = get_val("SI.POV.DDAY")
    sante = get_val("SH.XPD.GHED.GD.ZS")
    education = get_val("SE.XPD.TOTL.GD.ZS")
    
    cards = []
    
    # Croissance PIB
    if croissance is not None:
        cards.append(html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px', 'border': '1px solid #2a2f3e'}, children=[
            html.Div("Taux de croissance du PIB", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            html.Div(f"{'+' if croissance > 0 else ''}{croissance:.1f}%", 
                    style={'color': COLORS['success'] if croissance > 0 else COLORS['error'], 'fontSize': '3rem', 'fontWeight': 'bold'})
        ]))
    
    # RNB
    if rnb is not None:
        cards.append(html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px', 'border': '1px solid #2a2f3e'}, children=[
            html.Div("RNB par habitant (USD)", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            html.Div(f"${rnb:,.0f}", style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold'})
        ]))
    
    # Pauvreté
    if pauvrete is not None:
        cards.append(html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px', 'border': '1px solid #2a2f3e'}, children=[
            html.Div("Taux de pauvreté (1,90 USD/jour)", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            html.Div(f"${pauvrete:,.0f}", style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold'})
        ]))
    
    # Dépenses
    if sante or education:
        cards.append(html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px', 'border': '1px solid #2a2f3e'}, children=[
            html.Div("Dépenses publiques (% du PIB)", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            html.Div(f"{(sante or 0) + (education or 0):.0f}%", style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div([
                html.Div(f"Santé: {sante:.1f}%" if sante else "", style={'color': COLORS['text_secondary'], 'fontSize': '0.85rem'}),
                html.Div(f"Éducation: {education:.1f}%" if education else "", style={'color': COLORS['text_secondary'], 'fontSize': '0.85rem'})
            ])
        ]))
    
    if not cards:
        return html.Div("Données non disponibles", style={'color': COLORS['warning'], 'textAlign': 'center', 'padding': '40px'})
    
    return html.Div(style={'display': 'grid', 'gridTemplateColumns': f'repeat({len(cards)}, 1fr)', 'gap': '20px'}, children=cards)

@app.callback(
    Output('time-chart', 'figure'),
    [Input('data-store', 'data'), Input('country-selector', 'value')]
)
def update_time(data, country):
    if not data: return go.Figure()
    df = pd.DataFrame(data)
    df_country = df[df['country'] == country]
    
    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    
    for i, (code, name) in enumerate(list(INDICATORS.items())[:5]):
        df_ind = df_country[df_country['indicator'] == code].sort_values('year')
        if not df_ind.empty:
            fig.add_trace(go.Scatter(x=df_ind['year'], y=df_ind['value'], 
                                    mode='lines+markers', name=name,
                                    line=dict(width=2, color=colors[i])))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'], paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']}, hovermode='x unified',
        xaxis=dict(gridcolor=COLORS['grid'], showgrid=True),
        yaxis=dict(gridcolor=COLORS['grid'], showgrid=True),
        legend=dict(orientation='h', y=1.1),
        margin=dict(l=50, r=50, t=60, b=50)
    )
    return fig

@app.callback(
    Output('ranking-chart', 'figure'),
    [Input('data-store', 'data'), Input('indicator-selector', 'value'), Input('year-selector', 'value')]
)
def update_ranking(data, indicator, year):
    if not data or not year: return go.Figure()
    df = pd.DataFrame(data)
    df_fil = df[(df['indicator'] == indicator) & (df['year'] == year)]
    df_fil = df_fil.sort_values('value', ascending=True)
    df_fil['country_name'] = df_fil['country'].map(UEMOA_COUNTRIES)
    
    fig = go.Figure(go.Bar(
        y=df_fil['country_name'], x=df_fil['value'], orientation='h',
        marker=dict(color=df_fil['value'], colorscale='RdYlGn'),
        text=df_fil['value'].round(2), textposition='auto'
    ))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'], paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']},
        xaxis=dict(gridcolor=COLORS['grid']), margin=dict(l=150, r=50, t=20, b=50)
    )
    return fig

@app.callback(
    Output('comparison-chart', 'figure'),
    [Input('data-store', 'data'), Input('indicator-selector', 'value')]
)
def update_comparison(data, indicator):
    if not data: return go.Figure()
    df = pd.DataFrame(data)
    df_ind = df[df['indicator'] == indicator].sort_values('year')
    
    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    
    for i, (code, name) in enumerate(UEMOA_COUNTRIES.items()):
        df_c = df_ind[df_ind['country'] == code]
        if not df_c.empty:
            fig.add_trace(go.Scatter(x=df_c['year'], y=df_c['value'],
                                    mode='lines+markers', name=name,
                                    line=dict(width=2, color=colors[i])))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'], paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']}, hovermode='x unified',
        xaxis=dict(gridcolor=COLORS['grid']), yaxis=dict(gridcolor=COLORS['grid']),
        legend=dict(orientation='h', y=1.1), margin=dict(l=50, r=50, t=60, b=50)
    )
    return fig

@app.callback(
    Output('data-table', 'children'),
    [Input('data-store', 'data'), Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_table(data, country, year):
    if not data or not year: return ""
    df = pd.DataFrame(data)
    df_fil = df[(df['country'] == country) & (df['year'] == year)]
    df_fil['indicator_name'] = df_fil['indicator'].map(INDICATORS)
    df_fil = df_fil[['indicator_name', 'value']].sort_values('indicator_name')
    
    rows = [html.Tr([
        html.Th("Indicateur", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': f'1px solid {COLORS["grid"]}'}),
        html.Th("Valeur", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': f'1px solid {COLORS["grid"]}'})
    ])]
    
    for _, row in df_fil.iterrows():
        rows.append(html.Tr([
            html.Td(row['indicator_name'], style={'color': COLORS['text_secondary'], 'padding': '10px', 'borderBottom': f'1px solid {COLORS["grid"]}'}),
            html.Td(f"{row['value']:,.2f}", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': f'1px solid {COLORS["grid"]}'})
        ]))
    
    return html.Table(rows, style={'width': '100%', 'borderCollapse': 'collapse'})

@app.callback(
    Output('data-store', 'data'),
    Input('interval', 'n_intervals')
)
def refresh_data(n):
    df = get_wb_data()
    return df.to_dict('records')

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║         TABLEAU DE BORD BANQUE MONDIALE - UEMOA               ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    
    📊 Données: {} observations
    🌍 Pays: {} pays UEMOA
    📈 Indicateurs: {} KPI
    
    🌐 URL: http://127.0.0.1:8051
    🛑 Arrêter: Ctrl+C
    """.format(len(df_wb), len(UEMOA_COUNTRIES), len(INDICATORS)))
    
    app.run(debug=False, host='127.0.0.1', port=8051)

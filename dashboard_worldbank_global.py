"""
Tableau de Bord Banque Mondiale - Style Premium
Dashboard interactif avec design moderne (fond noir, cyan/bleu)
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

# Indicateurs clés (selon l'image fournie)
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "Taux de croissance du PIB",
    "SI.POV.DDAY": "Taux de pauvreté (1,90 USD/jour)",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    "SH.XPD.GHED.GD.ZS": "Dépenses publiques santé (% PIB)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses publiques éducation (% PIB)",
    "GC.DOD.TOTL.GD.ZS": "Dette publique (% PIB)",
}

# Indicateurs Doing Business (6 dimensions du radar)
DOING_BUSINESS = {
    "IC.BUS.EASE.XQ": "Voix et accontabilité",
    "RL.EST": "Vide du loi",
    "PV.EST": "Stabilité patl politique",
    "CC.EST": "Contrôle de corruption",
    "GE.EST": "Effectivite ducable",
    "RQ.EST": "Efficacinert"
}

# Couleurs premium (fond noir + cyan/bleu)
COLORS = {
    'background': '#0a1929',  # Fond noir-bleu foncé
    'card': '#132f4c',         # Carte bleu foncé
    'primary': '#00d9ff',      # Cyan brillant
    'secondary': '#3d8bfd',    # Bleu
    'text': '#ffffff',         # Blanc
    'text_secondary': '#b0bec5', # Gris clair
    'success': '#00ff88',      # Vert cyan
    'warning': '#ffa726',      # Orange
    'error': '#ff5252',        # Rouge
    'grid': '#1e3a5f'          # Grille bleu foncé
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
print(f"\n{'='*80}")
print(f"✅ Chargé {len(df_wb)} observations Banque Mondiale")
if not df_wb.empty:
    countries = sorted(df_wb['country'].unique())
    print(f"🌍 Pays: {len(countries)} pays dans la base")
    print(f"📊 Indicateurs: {df_wb['indicator'].nunique()} indicateurs")
    print(f"📅 Période: {df_wb['year'].min():.0f} - {df_wb['year'].max():.0f}")
print(f"{'='*80}\n")

# Dictionnaire pays ISO -> Noms (sera enrichi dynamiquement)
COUNTRY_NAMES = {
    "BEN": "Bénin", "BFA": "Burkina Faso", "CIV": "Côte d'Ivoire",
    "GNB": "Guinée-Bissau", "MLI": "Mali", "NER": "Niger",
    "SEN": "Sénégal", "TGO": "Togo", "USA": "États-Unis",
    "CHN": "Chine", "IND": "Inde", "BRA": "Brésil", 
    "FRA": "France", "DEU": "Allemagne", "GBR": "Royaume-Uni",
    "JPN": "Japon", "CAN": "Canada", "AUS": "Australie",
    "ZAF": "Afrique du Sud", "NGA": "Nigeria", "EGY": "Égypte",
    "KEN": "Kenya", "GHA": "Ghana", "ETH": "Éthiopie",
    "MAR": "Maroc", "DZA": "Algérie", "TUN": "Tunisie"
}

# Application Dash
app = dash.Dash(__name__)
app.title = "Banque Mondiale - Tous les Pays"

# Layout
app.layout = html.Div(style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'}, children=[
    # Header
    html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.H1("🌍 BANQUE MONDIALE - DONNÉES MONDIALES", 
                style={'color': COLORS['text'], 'marginBottom': '5px', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
        html.P("Indicateurs de développement - Tous les pays du monde",
                style={'color': COLORS['text_secondary'], 'fontSize': '1.1rem'})
    ]),
    
    # Stats globales
    html.Div(id='global-stats', style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px', 'textAlign': 'center'}),
    
    # Filtres
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '20px'}, children=[
            html.Div([
                html.Label("🌍 Sélectionner un pays:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Dropdown(id='country-selector', clearable=False,
                           placeholder="Sélectionnez un pays...")
            ]),
            html.Div([
                html.Label("📅 Sélectionner une année:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Dropdown(id='year-selector', clearable=False)
            ]),
            html.Div([
                html.Label("🔎 Rechercher un pays:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Input(id='country-search', type='text', placeholder='Tapez pour rechercher...',
                        style={'width': '100%', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #2a2f3e', 'backgroundColor': '#0e1117', 'color': COLORS['text']})
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
            html.H3("Top 10 Pays", style={'color': COLORS['text'], 'marginBottom': '20px'}),
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
    Output('global-stats', 'children'),
    Input('data-store', 'data')
)
def update_global_stats(data):
    if not data:
        return html.Div("Chargement...", style={'color': COLORS['text_secondary']})
    
    df = pd.DataFrame(data)
    n_countries = df['country'].nunique()
    n_indicators = df['indicator'].nunique()
    n_observations = len(df)
    years = f"{df['year'].min():.0f} - {df['year'].max():.0f}"
    
    return html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px'}, children=[
        html.Div([
            html.Div("🌍 Pays", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem'}),
            html.Div(f"{n_countries}", style={'color': COLORS['primary'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ]),
        html.Div([
            html.Div("📊 Indicateurs", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem'}),
            html.Div(f"{n_indicators}", style={'color': COLORS['secondary'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ]),
        html.Div([
            html.Div("📈 Observations", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem'}),
            html.Div(f"{n_observations:,}", style={'color': COLORS['success'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ]),
        html.Div([
            html.Div("📅 Période", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem'}),
            html.Div(years, style={'color': COLORS['text'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ])
    ])

@app.callback(
    [Output('country-selector', 'options'), Output('country-selector', 'value')],
    [Input('data-store', 'data'), Input('country-search', 'value')]
)
def update_country_options(data, search):
    if not data:
        return [], None
    
    df = pd.DataFrame(data)
    countries = sorted(df['country'].unique())
    
    # Filtrer par recherche si fournie
    if search:
        countries = [c for c in countries if search.upper() in c.upper() or 
                    (c in COUNTRY_NAMES and search.lower() in COUNTRY_NAMES[c].lower())]
    
    options = [{'label': f"{c} - {COUNTRY_NAMES.get(c, c)}", 'value': c} for c in countries]
    
    # Valeur par défaut: premier pays ou CIV si existe
    default = 'CIV' if 'CIV' in countries else countries[0] if countries else None
    
    return options, default

@app.callback(
    [Output('year-selector', 'options'), Output('year-selector', 'value')],
    Input('data-store', 'data')
)
def update_years(data):
    if not data:
        return [], None
    df = pd.DataFrame(data)
    years = sorted(df['year'].unique(), reverse=True)
    options = [{'label': str(int(y)), 'value': int(y)} for y in years]
    return options, int(years[0]) if years else None

@app.callback(
    Output('kpi-cards', 'children'),
    [Input('data-store', 'data'), Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_kpi(data, country, year):
    if not data or not year or not country:
        return html.Div("Sélectionnez un pays et une année...", style={'color': COLORS['text_secondary']})
    
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
            html.Div(f"{pauvrete:.1f}%", style={'color': COLORS['warning'], 'fontSize': '3rem', 'fontWeight': 'bold'})
        ]))
    
    # Dépenses
    if sante or education:
        depenses_txt = []
        if sante: depenses_txt.append(f"💊 Santé: {sante:.1f}%")
        if education: depenses_txt.append(f"📚 Éducation: {education:.1f}%")
        
        cards.append(html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px', 'border': '1px solid #2a2f3e'}, children=[
            html.Div("Dépenses publiques (% du PIB)", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            html.Div([html.Div(txt, style={'color': COLORS['text'], 'fontSize': '1.5rem', 'marginBottom': '5px'}) for txt in depenses_txt])
        ]))
    
    if not cards:
        return html.Div(f"Aucune donnée disponible pour {COUNTRY_NAMES.get(country, country)} en {year}", 
                       style={'color': COLORS['text_secondary'], 'textAlign': 'center', 'padding': '20px'})
    
    return html.Div(style={'display': 'grid', 'gridTemplateColumns': f'repeat({min(len(cards), 4)}, 1fr)', 'gap': '20px'}, children=cards)

@app.callback(
    Output('time-chart', 'figure'),
    [Input('data-store', 'data'), Input('country-selector', 'value')]
)
def update_time_chart(data, country):
    if not data or not country:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df_country = df[df['country'] == country]
    
    fig = go.Figure()
    
    for ind_code in ["NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS"]:
        df_ind = df_country[df_country['indicator'] == ind_code].sort_values('year')
        if not df_ind.empty:
            fig.add_trace(go.Scatter(
                x=df_ind['year'], y=df_ind['value'],
                name=INDICATORS.get(ind_code, ind_code),
                mode='lines+markers'
            ))
    
    fig.update_layout(
        template='plotly_dark', paper_bgcolor=COLORS['surface'], plot_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']}, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified'
    )
    
    return fig

@app.callback(
    Output('ranking-chart', 'figure'),
    [Input('data-store', 'data'), Input('year-selector', 'value'), Input('indicator-selector', 'value')]
)
def update_ranking(data, year, indicator):
    if not data or not year or not indicator:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df_fil = df[(df['year'] == year) & (df['indicator'] == indicator)].sort_values('value', ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        x=df_fil['value'], y=[COUNTRY_NAMES.get(c, c) for c in df_fil['country']],
        orientation='h', marker_color=COLORS['primary']
    ))
    
    fig.update_layout(
        template='plotly_dark', paper_bgcolor=COLORS['surface'], plot_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']}, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title=INDICATORS.get(indicator, indicator), yaxis={'autorange': 'reversed'}
    )
    
    return fig

@app.callback(
    Output('comparison-chart', 'figure'),
    [Input('data-store', 'data'), Input('indicator-selector', 'value'), Input('year-selector', 'value')]
)
def update_comparison(data, indicator, year):
    if not data or not indicator or not year:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df_fil = df[(df['indicator'] == indicator) & (df['year'] == year)].sort_values('value', ascending=False).head(20)
    
    fig = px.bar(df_fil, x=[COUNTRY_NAMES.get(c, c) for c in df_fil['country']], y='value',
                title=f"{INDICATORS.get(indicator, indicator)} - {year}")
    
    fig.update_layout(
        template='plotly_dark', paper_bgcolor=COLORS['surface'], plot_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']}, margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title='', yaxis_title=INDICATORS.get(indicator, indicator)
    )
    
    return fig

@app.callback(
    Output('data-table', 'children'),
    [Input('data-store', 'data'), Input('country-selector', 'value'), Input('year-selector', 'value')]
)
def update_table(data, country, year):
    if not data or not country or not year:
        return html.Div("Aucune donnée", style={'color': COLORS['text_secondary']})
    
    df = pd.DataFrame(data)
    df_fil = df[(df['country'] == country) & (df['year'] == year)]
    
    rows = []
    for _, row in df_fil.iterrows():
        ind_name = INDICATORS.get(row['indicator'], row['indicator'])
        rows.append(html.Tr([
            html.Td(ind_name, style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': '1px solid #2a2f3e'}),
            html.Td(f"{row['value']:.2f}", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': '1px solid #2a2f3e', 'textAlign': 'right'})
        ]))
    
    return html.Table([
        html.Thead(html.Tr([
            html.Th("Indicateur", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': '2px solid #2a2f3e'}),
            html.Th("Valeur", style={'color': COLORS['text'], 'padding': '10px', 'borderBottom': '2px solid #2a2f3e', 'textAlign': 'right'})
        ])),
        html.Tbody(rows)
    ], style={'width': '100%', 'borderCollapse': 'collapse'})

if __name__ == '__main__':
    print(f"\n{'='*80}")
    print(f"    ╔════════════════════════════════════════════════════════════════╗")
    print(f"    ║                                                                ║")
    print(f"    ║   TABLEAU DE BORD BANQUE MONDIALE - TOUS LES PAYS DU MONDE    ║")
    print(f"    ║                                                                ║")
    print(f"    ╚════════════════════════════════════════════════════════════════╝")
    print(f"\n    🌍 URL: http://127.0.0.1:8052")
    print(f"    🛑 Arrêter: Ctrl+C\n")
    print(f"{'='*80}\n")
    
    app.run(debug=False, host='127.0.0.1', port=8052)

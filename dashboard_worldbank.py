"""
Tableau de Bord Interactif Banque Mondiale
Dashboard professionnel pour les indicateurs macroéconomiques
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Ajouter le répertoire du projet au path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Connexion MongoDB
client, db = get_mongo_db()

# Indicateurs clés de performance (KPI) - Banque Mondiale
INDICATORS = {
    # Croissance et richesse
    "NY.GDP.MKTP.KD.ZG": "Taux de croissance du PIB",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    
    # Pauvreté
    "SI.POV.DDAY": "Taux de pauvreté (1,90 USD/jour)",
    
    # Dépenses publiques sectorielles
    "SH.XPD.GHED.GD.ZS": "Dépenses publiques santé (% PIB)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses publiques éducation (% PIB)",
    
    # Autres indicateurs importants
    "NY.GDP.MKTP.CD": "PIB (USD courant)",
    "FP.CPI.TOTL.ZG": "Inflation (CPI annuel %)",
    "GC.DOD.TOTL.GD.ZS": "Dette publique (% PIB)",
    "GC.XPN.TOTL.GD.ZS": "Dépenses publiques totales (% PIB)",
    "SP.POP.TOTL": "Population totale",
}

# Mapping des KPI principaux pour l'affichage
KPI_MAPPING = {
    "croissance_pib": "NY.GDP.MKTP.KD.ZG",
    "rnb_habitant": "NY.GNP.PCAP.CD",
    "taux_pauvrete": "SI.POV.DDAY",
    "depenses_sante": "SH.XPD.GHED.GD.ZS",
    "depenses_education": "SE.XPD.TOTL.GD.ZS",
}

# Pays UEMOA
UEMOA_COUNTRIES = {
    "BEN": "Bénin",
    "BFA": "Burkina Faso",
    "CIV": "Côte d'Ivoire",
    "GNB": "Guinée-Bissau",
    "MLI": "Mali",
    "NER": "Niger",
    "SEN": "Sénégal",
    "TGO": "Togo"
}

# Palette de couleurs professionnelles
COLORS = {
    'background': '#0e1117',
    'surface': '#1a1f2e',
    'primary': '#4CAF50',
    'secondary': '#2196F3',
    'accent': '#FF9800',
    'text': '#E0E0E0',
    'text_secondary': '#9E9E9E',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    'grid': '#2a2f3e'
}

def get_wb_data():
    """Récupère les données de la Banque Mondiale depuis MongoDB"""
    # Utiliser curated_observations (collection correcte)
    observations = db['curated_observations']
    
    # Récupérer toutes les observations WorldBank
    cursor = observations.find({
        '$or': [
            {'source': 'worldbank'},
            {'source': 'WorldBank'},
            {'source': 'WORLDBANK'}
        ]
    })
    
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    # Convertir en DataFrame
    records = []
    for obs in data:
        try:
            records.append({
                'indicator': obs.get('attrs', {}).get('indicator', obs.get('dataset')),
                'country': obs.get('attrs', {}).get('country'),
                'year': pd.to_datetime(obs['ts']).year,
                'value': float(obs['value'])
            })
        except Exception:
            continue
    
    return pd.DataFrame(records)

# Récupération initiale des données
df_wb = get_wb_data()
print(f"Chargé {len(df_wb)} observations de la Banque Mondiale")

# Créer l'application Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Tableau de Bord Banque Mondiale"

# Layout
app.layout = html.Div(style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'}, children=[
    # Header
    html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.H1("🌍 BANQUE MONDIALE", 
                style={'color': COLORS['text'], 'marginBottom': '5px', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
        html.P("Indicateurs de développement - Zone UEMOA",
                style={'color': COLORS['text_secondary'], 'fontWeight': '300', 'fontSize': '1.1rem'})
    ]),
    
    # Filtres
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
            # Sélecteur de pays
            html.Div([
                html.Label("🌍 Sélectionner un pays:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block', 'fontSize': '1.1rem'}),
                dcc.Dropdown(
                    id='country-selector',
                    options=[{'label': name, 'value': code} for code, name in UEMOA_COUNTRIES.items()],
                    value='CIV',  # Côte d'Ivoire par défaut
                    style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']},
                    className='custom-dropdown'
                )
            ]),
            
            # Sélecteur d'année
            html.Div([
                html.Label("� Sélectionner une année:", style={'color': COLORS['text'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block', 'fontSize': '1.1rem'}),
                dcc.Dropdown(
                    id='year-selector',
                    options=[],  # Sera rempli dynamiquement
                    value=None,
                    style={'backgroundColor': COLORS['surface'], 'color': COLORS['text']},
                    className='custom-dropdown'
                )
            ])
        ])
    ]),
    
    # KPI Principaux (style carte comme l'image)
    html.Div(id='kpi-cards', style={'marginBottom': '20px'}),
    
    # Section Doing Business et Governance (à implémenter avec données futures)
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        # Doing Business
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Doing Business — Classements globaux", style={'color': COLORS['text'], 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            html.Div(id='doing-business-content', children=[
                html.P("Données en cours de collecte...", style={'color': COLORS['text_secondary'], 'textAlign': 'center', 'padding': '40px'})
            ])
        ]),
        
        # Governance Indicators
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Indicateurs de gouvernance mondiale (WGI)", style={'color': COLORS['text'], 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            dcc.Graph(id='governance-radar', style={'height': '300px'})
        ])
    ]),
    
    # Graphiques d'évolution
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        # Évolution temporelle
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Évolution des indicateurs dans le temps", style={'color': COLORS['text'], 'marginBottom': '20px'}),
            dcc.Graph(id='time-series-chart', style={'height': '400px'})
        ]),
        
        # Comparaison pays
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.H3("Comparaison UEMOA", style={'color': COLORS['text'], 'marginBottom': '20px'}),
            dcc.Graph(id='ranking-chart', style={'height': '400px'})
        ])
    ]),
    
    # Tableau des données détaillées
    html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.H3("Données détaillées", style={'color': COLORS['text'], 'marginBottom': '20px'}),
        html.Div(id='data-table')
    ]),
    
    # Intervalle de mise à jour
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 1 minute
        n_intervals=0
    ),
    
    # Store pour les données
    dcc.Store(id='data-store')
])

# Callbacks
@app.callback(
    Output('year-selector', 'options'),
    Output('year-selector', 'value'),
    Input('data-store', 'data')
)
def update_year_options(data_dict):
    """Met à jour les options d'années disponibles"""
    if not data_dict or not data_dict.get('data'):
        return [], None
    
    df = pd.DataFrame(data_dict['data'])
    years = sorted(df['year'].unique(), reverse=True)
    options = [{'label': str(int(year)), 'value': int(year)} for year in years]
    
    # Sélectionner la dernière année par défaut
    default_year = int(years[0]) if years else None
    
    return options, default_year

@app.callback(
    Output('kpi-cards', 'children'),
    [Input('data-store', 'data'),
     Input('country-selector', 'value'),
     Input('year-selector', 'value')]
)
def update_kpi_cards(data_dict, country, year):
    """Affiche les cartes KPI principales (style image)"""
    if not data_dict or not data_dict.get('data') or not year:
        return html.Div("Sélectionnez un pays et une année", style={'color': COLORS['warning'], 'textAlign': 'center', 'padding': '20px'})
    
    df = pd.DataFrame(data_dict['data'])
    df_filtered = df[(df['country'] == country) & (df['year'] == year)]
    
    if df_filtered.empty:
        return html.Div("Aucune donnée pour cette sélection", style={'color': COLORS['warning'], 'textAlign': 'center', 'padding': '20px'})
    
    # Fonction pour obtenir une valeur d'indicateur
    def get_indicator_value(indicator_code):
        row = df_filtered[df_filtered['indicator'] == indicator_code]
        return row['value'].iloc[0] if not row.empty else None
    
    # Récupérer les valeurs
    croissance_pib = get_indicator_value("NY.GDP.MKTP.KD.ZG")
    rnb_habitant = get_indicator_value("NY.GNP.PCAP.CD")
    taux_pauvrete = get_indicator_value("SI.POV.DDAY")
    depenses_sante = get_indicator_value("SH.XPD.GHED.GD.ZS")
    depenses_education = get_indicator_value("SE.XPD.TOTL.GD.ZS")
    
    # Créer les cartes KPI (style image)
    cards = []
    
    # Carte 1: Taux de croissance du PIB
    if croissance_pib is not None:
        cards.append(
            html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px'}, children=[
                html.Div("Taux de croissance du PIB", style={'color': COLORS['text_secondary'], 'fontSize': '0.95rem', 'marginBottom': '15px'}),
                html.Div([
                    html.Span(f"+{croissance_pib:.1f}" if croissance_pib > 0 else f"{croissance_pib:.1f}", 
                             style={'color': COLORS['primary'] if croissance_pib > 0 else COLORS['error'], 'fontSize': '3rem', 'fontWeight': 'bold'}),
                    html.Span("%", style={'color': COLORS['primary'] if croissance_pib > 0 else COLORS['error'], 'fontSize': '2rem', 'marginLeft': '5px'})
                ]),
                # Mini graphique de tendance (à implémenter)
                html.Div(style={'height': '60px', 'marginTop': '15px'}, children=[
                    dcc.Graph(id=f'mini-chart-pib-{country}', figure=create_mini_chart(df, country, "NY.GDP.MKTP.KD.ZG", year), 
                             config={'displayModeBar': False}, style={'height': '100%'})
                ])
            ])
        )
    
    # Carte 2: RNB par habitant
    if rnb_habitant is not None:
        cards.append(
            html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px'}, children=[
                html.Div("RNB par habitant (USD)", style={'color': COLORS['text_secondary'], 'fontSize': '0.95rem', 'marginBottom': '15px'}),
                html.Div([
                    html.Span("$", style={'color': COLORS['text'], 'fontSize': '2rem', 'marginRight': '5px'}),
                    html.Span(f"{rnb_habitant:,.0f}", style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold'})
                ])
            ])
        )
    
    # Carte 3: Taux de pauvreté
    if taux_pauvrete is not None:
        cards.append(
            html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px'}, children=[
                html.Div("Taux de pauvreté (1,90 USD/jour)", style={'color': COLORS['text_secondary'], 'fontSize': '0.95rem', 'marginBottom': '15px'}),
                html.Div([
                    html.Span("$", style={'color': COLORS['text'], 'fontSize': '2rem', 'marginRight': '5px'}),
                    html.Span(f"{taux_pauvrete:,.0f}", style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold'})
                ])
            ])
        )
    
    # Carte 4: Dépenses publiques
    if depenses_sante is not None or depenses_education is not None:
        depenses_items = []
        if depenses_sante is not None:
            depenses_items.append(html.Div([
                html.Span("Santé: ", style={'color': COLORS['text_secondary']}),
                html.Span(f"{depenses_sante:.1f}%", style={'color': COLORS['text'], 'fontWeight': 'bold'})
            ], style={'marginBottom': '10px'}))
        
        if depenses_education is not None:
            depenses_items.append(html.Div([
                html.Span("Éducation: ", style={'color': COLORS['text_secondary']}),
                html.Span(f"{depenses_education:.1f}%", style={'color': COLORS['text'], 'fontWeight': 'bold'})
            ]))
        
        cards.append(
            html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '25px', 'borderRadius': '10px'}, children=[
                html.Div("Dépenses publiques (% du PIB)", style={'color': COLORS['text_secondary'], 'fontSize': '0.95rem', 'marginBottom': '15px'}),
                html.Div([
                    html.Span(f"{(depenses_sante or 0) + (depenses_education or 0):.0f}", 
                             style={'color': COLORS['text'], 'fontSize': '3rem', 'fontWeight': 'bold', 'marginRight': '5px'}),
                    html.Span("et", style={'color': COLORS['text'], 'fontSize': '1.2rem', 'verticalAlign': 'super'})
                ], style={'marginBottom': '15px'}),
                html.Div(depenses_items)
            ])
        )
    
    if not cards:
        return html.Div("Données KPI non disponibles pour cette sélection", 
                       style={'color': COLORS['warning'], 'textAlign': 'center', 'padding': '20px'})
    
    return html.Div(style={'display': 'grid', 'gridTemplateColumns': f'repeat({min(len(cards), 4)}, 1fr)', 'gap': '20px'}, 
                    children=cards)

def create_mini_chart(df, country, indicator, current_year):
    """Crée un mini graphique de tendance pour les KPI"""
    df_indicator = df[(df['country'] == country) & (df['indicator'] == indicator)]
    df_indicator = df_indicator.sort_values('year').tail(10)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_indicator['year'],
        y=df_indicator['value'],
        mode='lines',
        line=dict(color='#4A9EFF', width=2),
        fill='tozeroy',
        fillcolor='rgba(74, 158, 255, 0.1)'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        hovermode=False
    )
    
    return fig

@app.callback(
    Output('key-stats', 'children'),
    [Input('data-store', 'data'),
     Input('country-selector', 'value'),
     Input('indicator-selector', 'value')]
)
def update_key_stats(data_dict, country, indicator):
    """Affiche les statistiques clés"""
    if not data_dict or not data_dict.get('data'):
        return html.Div("Aucune donnée disponible", style={'color': COLORS['error'], 'textAlign': 'center', 'padding': '20px'})
    
    df = pd.DataFrame(data_dict['data'])
    df_filtered = df[(df['country'] == country) & (df['indicator'] == indicator)]
    
    if df_filtered.empty:
        return html.Div("Aucune donnée pour cette sélection", style={'color': COLORS['warning'], 'textAlign': 'center', 'padding': '20px'})
    
    # Calculer les statistiques
    latest_value = df_filtered.sort_values('year').iloc[-1]['value']
    latest_year = df_filtered.sort_values('year').iloc[-1]['year']
    
    if len(df_filtered) > 1:
        previous_value = df_filtered.sort_values('year').iloc[-2]['value']
        change = latest_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0
    else:
        change = 0
        change_pct = 0
    
    avg_value = df_filtered['value'].mean()
    min_value = df_filtered['value'].min()
    max_value = df_filtered['value'].max()
    
    # Créer les cartes de stats
    return html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px'}, children=[
        # Valeur actuelle
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px', 'border': f'2px solid {COLORS["primary"]}'}, children=[
            html.Div(f"Valeur {int(latest_year)}", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
            html.Div(f"{latest_value:,.2f}", style={'color': COLORS['text'], 'fontSize': '2rem', 'fontWeight': 'bold'}),
            html.Div(
                f"{'↑' if change > 0 else '↓'} {abs(change_pct):.2f}%",
                style={'color': COLORS['success'] if change > 0 else COLORS['error'], 'fontSize': '0.9rem', 'marginTop': '5px'}
            )
        ]),
        
        # Moyenne
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.Div("Moyenne", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
            html.Div(f"{avg_value:,.2f}", style={'color': COLORS['text'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ]),
        
        # Minimum
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.Div("Minimum", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
            html.Div(f"{min_value:,.2f}", style={'color': COLORS['error'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ]),
        
        # Maximum
        html.Div(style={'backgroundColor': COLORS['surface'], 'padding': '20px', 'borderRadius': '10px'}, children=[
            html.Div("Maximum", style={'color': COLORS['text_secondary'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
            html.Div(f"{max_value:,.2f}", style={'color': COLORS['success'], 'fontSize': '2rem', 'fontWeight': 'bold'})
        ])
    ])

@app.callback(
    Output('time-series-chart', 'figure'),
    [Input('data-store', 'data'),
     Input('country-selector', 'value'),
     Input('indicator-selector', 'value'),
     Input('period-selector', 'value')]
)
def update_time_series(data_dict, country, indicator, period):
    """Graphique d'évolution temporelle"""
    if not data_dict or not data_dict.get('data'):
        return go.Figure()
    
    df = pd.DataFrame(data_dict['data'])
    df_filtered = df[(df['country'] == country) & (df['indicator'] == indicator)].sort_values('year')
    
    if period < 100:
        max_year = df_filtered['year'].max()
        df_filtered = df_filtered[df_filtered['year'] >= max_year - period]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_filtered['year'],
        y=df_filtered['value'],
        mode='lines+markers',
        name=INDICATORS.get(indicator, indicator),
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8, color=COLORS['primary']),
        fill='tozeroy',
        fillcolor=f'rgba(76, 175, 80, 0.1)'
    ))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']},
        xaxis=dict(
            title='Année',
            gridcolor=COLORS['grid'],
            showgrid=True
        ),
        yaxis=dict(
            title='Valeur',
            gridcolor=COLORS['grid'],
            showgrid=True
        ),
        hovermode='x unified',
        margin=dict(l=50, r=50, t=20, b=50)
    )
    
    return fig

@app.callback(
    Output('ranking-chart', 'figure'),
    [Input('data-store', 'data'),
     Input('indicator-selector', 'value')]
)
def update_ranking(data_dict, indicator):
    """Classement des pays UEMOA"""
    if not data_dict or not data_dict.get('data'):
        return go.Figure()
    
    df = pd.DataFrame(data_dict['data'])
    df_indicator = df[df['indicator'] == indicator]
    
    # Obtenir la dernière année pour chaque pays
    latest_data = df_indicator.sort_values('year').groupby('country').tail(1)
    latest_data = latest_data.sort_values('value', ascending=True)
    
    # Remplacer les codes pays par les noms
    latest_data['country_name'] = latest_data['country'].map(UEMOA_COUNTRIES)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=latest_data['country_name'],
        x=latest_data['value'],
        orientation='h',
        marker=dict(
            color=latest_data['value'],
            colorscale='RdYlGn',
            showscale=False
        ),
        text=latest_data['value'].round(2),
        textposition='auto'
    ))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']},
        xaxis=dict(
            title='Valeur',
            gridcolor=COLORS['grid'],
            showgrid=True
        ),
        yaxis=dict(
            title='',
            gridcolor=COLORS['grid']
        ),
        margin=dict(l=150, r=50, t=20, b=50)
    )
    
    return fig

@app.callback(
    Output('comparison-chart', 'figure'),
    [Input('data-store', 'data'),
     Input('indicator-selector', 'value'),
     Input('period-selector', 'value')]
)
def update_comparison(data_dict, indicator, period):
    """Comparaison multi-pays"""
    if not data_dict or not data_dict.get('data'):
        return go.Figure()
    
    df = pd.DataFrame(data_dict['data'])
    df_indicator = df[df['indicator'] == indicator].sort_values('year')
    
    if period < 100:
        max_year = df_indicator['year'].max()
        df_indicator = df_indicator[df_indicator['year'] >= max_year - period]
    
    fig = go.Figure()
    
    colors_list = px.colors.qualitative.Set2
    
    for i, (country_code, country_name) in enumerate(UEMOA_COUNTRIES.items()):
        df_country = df_indicator[df_indicator['country'] == country_code]
        if not df_country.empty:
            fig.add_trace(go.Scatter(
                x=df_country['year'],
                y=df_country['value'],
                mode='lines+markers',
                name=country_name,
                line=dict(width=2, color=colors_list[i % len(colors_list)]),
                marker=dict(size=6)
            ))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']},
        xaxis=dict(
            title='Année',
            gridcolor=COLORS['grid'],
            showgrid=True
        ),
        yaxis=dict(
            title='Valeur',
            gridcolor=COLORS['grid'],
            showgrid=True
        ),
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=50, r=50, t=60, b=50)
    )
    
    return fig

@app.callback(
    Output('correlation-chart', 'figure'),
    [Input('data-store', 'data'),
     Input('country-selector', 'value')]
)
def update_correlation(data_dict, country):
    """Matrice de corrélation des indicateurs"""
    if not data_dict or not data_dict.get('data'):
        return go.Figure()
    
    df = pd.DataFrame(data_dict['data'])
    df_country = df[df['country'] == country]
    
    # Pivoter pour avoir les indicateurs en colonnes
    pivot_df = df_country.pivot_table(
        index='year',
        columns='indicator',
        values='value'
    )
    
    # Calculer la corrélation
    corr_matrix = pivot_df.corr()
    
    # Remplacer les codes par les noms
    indicator_names = [INDICATORS.get(ind, ind) for ind in corr_matrix.columns]
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=indicator_names,
        y=indicator_names,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Corrélation")
    ))
    
    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['surface'],
        font={'color': COLORS['text']},
        xaxis=dict(tickangle=-45),
        margin=dict(l=150, r=50, t=50, b=150)
    )
    
    return fig

# CSS personnalisé
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .custom-dropdown .Select-control {
                background-color: #1a1f2e !important;
                border-color: #2a2f3e !important;
            }
            .custom-dropdown .Select-menu-outer {
                background-color: #1a1f2e !important;
            }
            .custom-dropdown .Select-option {
                background-color: #1a1f2e !important;
                color: #E0E0E0 !important;
            }
            .custom-dropdown .Select-option:hover {
                background-color: #2a2f3e !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                ║
    ║              TABLEAU DE BORD BANQUE MONDIALE - INDICATEURS UEMOA              ║
    ║                    Analyse macroéconomique interactive                        ║
    ║                                                                                ║
    ╚════════════════════════════════════════════════════════════════════════════════╝
    
    🚀 Démarrage du tableau de bord...
    
    📊 Données disponibles:
       ✓ {} observations de la Banque Mondiale
       ✓ {} indicateurs économiques
       ✓ {} pays de la zone UEMOA
    
    🌐 Accès: http://127.0.0.1:8051
    
    📡 Mise à jour automatique toutes les 60 secondes
    🛑 Pour arrêter: Ctrl+C
    
    ════════════════════════════════════════════════════════════════════════════════
    """.format(len(df_wb), len(INDICATORS), len(UEMOA_COUNTRIES)))
    
    app.run(debug=False, host='127.0.0.1', port=8051)

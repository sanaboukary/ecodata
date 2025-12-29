"""
Tableau de Bord Banque Mondiale - Design Premium
Style exact selon l'image fournie: fond noir, couleurs cyan/bleu, layout une page
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
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

# ==================== COULEURS PREMIUM ====================
COLORS = {
    'background': '#0a1929',      # Fond noir-bleu très foncé
    'card': '#132f4c',            # Carte bleu foncé
    'primary': '#00d9ff',         # Cyan brillant (pour les chiffres principaux)
    'secondary': '#3d8bfd',       # Bleu (pour les graphiques)
    'text': '#ffffff',            # Texte blanc
    'text_dim': '#8796a5',        # Texte grisé
    'success': '#00ff88',         # Vert cyan
    'chart_line': '#00d9ff',      # Ligne de graphique cyan
    'grid': '#1e3a5f',            # Grille
    'bar': '#3d8bfd'              # Barres bleues
}

# ==================== INDICATEURS ====================
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "Taux de croissance du PIB",
    "SI.POV.DDAY": "Taux de pauvreté (1,90 USD/jour)",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    "SH.XPD.GHED.GD.ZS": "Dépenses publiques santé (% PIB)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses publiques éducation (% PIB)",
}

# Indicateurs Doing Business (simulés pour le radar)
DOING_BUSINESS_INDICATORS = [
    "Voix et accontabilité",
    "Vide du loi", 
    "Stabilité patl politique",
    "Contrôle de corruption",
    "Effectivite ducable",
    "Efficacinert"
]

def get_wb_data():
    """Récupère données WB depuis MongoDB"""
    obs = db['curated_observations']
    cursor = obs.find({'source': {'$in': ['worldbank', 'WorldBank']}})
    
    records = []
    for o in cursor:
        try:
            indicator = o.get('attrs', {}).get('indicator', o.get('dataset'))
            country = o.get('attrs', {}).get('country')
            value = float(o['value'])
            year = pd.to_datetime(o['ts']).year
            
            records.append({
                'indicator': indicator,
                'country': country,
                'year': year,
                'value': value
            })
        except:
            continue
    
    return pd.DataFrame(records)

# Charger données
print("\n" + "="*80)
print("🌍 CHARGEMENT DASHBOARD BANQUE MONDIALE PREMIUM")
print("="*80)

df_wb = get_wb_data()
print(f"✅ Chargé {len(df_wb)} observations")

if not df_wb.empty:
    # Nettoyer les valeurs None
    df_wb = df_wb.dropna(subset=['country', 'year', 'indicator', 'value'])
    
    countries = sorted([c for c in df_wb['country'].unique() if c])
    years = sorted([y for y in df_wb['year'].unique() if y])
    print(f"🌍 Pays: {len(countries)}")
    print(f"📅 Années: {min(years):.0f} - {max(years):.0f}")
    print(f"📊 Indicateurs: {df_wb['indicator'].nunique()}")
else:
    countries = []
    years = []

print("="*80 + "\n")

# ==================== APPLICATION DASH ====================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Banque Mondiale - Dashboard Premium"

# Style CSS personnalisé pour les dropdowns
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Style pour les dropdowns Dash */
            .Select-control {
                background-color: #132f4c !important;
                border-color: #1e3a5f !important;
            }
            .Select-menu-outer {
                background-color: #132f4c !important;
                border-color: #1e3a5f !important;
            }
            .Select-menu {
                background-color: #132f4c !important;
            }
            .Select-option {
                background-color: #132f4c !important;
                color: #ffffff !important;
            }
            .Select-option:hover {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            .Select-value-label {
                color: #ffffff !important;
            }
            .Select-placeholder {
                color: #8796a5 !important;
            }
            .Select-input > input {
                color: #ffffff !important;
            }
            .Select-arrow {
                border-color: #8796a5 transparent transparent !important;
            }
            
            /* Style pour les nouveaux dropdowns (react-select v2+) */
            div[class*="control"] {
                background-color: #132f4c !important;
                border-color: #1e3a5f !important;
            }
            div[class*="menu"] {
                background-color: #132f4c !important;
            }
            div[class*="option"] {
                background-color: #132f4c !important;
                color: #ffffff !important;
            }
            div[class*="option"]:hover {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            div[class*="singleValue"] {
                color: #ffffff !important;
            }
            div[class*="placeholder"] {
                color: #8796a5 !important;
            }
            div[class*="Input"] {
                color: #ffffff !important;
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

# ==================== STYLES ====================
CARD_STYLE = {
    'backgroundColor': COLORS['card'],
    'padding': '20px',
    'borderRadius': '10px',
    'border': f'1px solid {COLORS["grid"]}',
    'height': '100%'
}

KPI_STYLE = {
    'backgroundColor': COLORS['card'],
    'padding': '20px',
    'borderRadius': '10px',
    'border': f'1px solid {COLORS["grid"]}',
    'textAlign': 'left'
}

# ==================== LAYOUT ====================
app.layout = html.Div(style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '30px',
    'fontFamily': 'Arial, sans-serif'
}, children=[
    
    # ========== HEADER ==========
    html.Div(style={'marginBottom': '30px'}, children=[
        html.H1("BANQUE MONDIALE", 
                style={
                    'color': COLORS['text'],
                    'fontSize': '2.5rem',
                    'fontWeight': 'bold',
                    'margin': '0',
                    'letterSpacing': '2px'
                })
    ]),
    
    # ========== FILTRES ==========
    html.Div(style={
        **CARD_STYLE,
        'marginBottom': '30px',
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gap': '20px'
    }, children=[
        html.Div([
            html.Label("🌍 Pays", style={'color': COLORS['text_dim'], 'fontSize': '0.9rem', 'marginBottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': c, 'value': c} for c in countries] if countries else [],
                value=countries[0] if countries else None,
                clearable=False,
                style={
                    'backgroundColor': COLORS['card'],
                    'color': COLORS['text'],
                    'borderColor': COLORS['grid']
                },
                className='custom-dropdown'
            )
        ]),
        html.Div([
            html.Label("📅 Année", style={'color': COLORS['text_dim'], 'fontSize': '0.9rem', 'marginBottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='year-filter',
                options=[{'label': str(int(y)), 'value': y} for y in years] if years else [],
                value=years[-1] if years else None,
                clearable=False,
                style={
                    'backgroundColor': COLORS['card'],
                    'color': COLORS['text'],
                    'borderColor': COLORS['grid']
                },
                className='custom-dropdown'
            )
        ])
    ]),
    
    # ========== ROW 1: KPI PRINCIPAUX + RADAR CHART ==========
    html.Div(style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr 1fr 1fr',
        'gap': '20px',
        'marginBottom': '30px'
    }, children=[
        # KPI 1: GDP Growth avec sparkline
        html.Div(id='kpi-gdp', style=KPI_STYLE),
        
        # KPI 2: Poverty Rate
        html.Div(id='kpi-poverty', style=KPI_STYLE),
        
        # KPI 3: GNI per capita
        html.Div(id='kpi-gni', style=KPI_STYLE),
        
        # Radar Chart Doing Business
        html.Div(style=CARD_STYLE, children=[
            html.Div("Doing Business — Classements globaux", 
                    style={'color': COLORS['text'], 'fontSize': '0.9rem', 'marginBottom': '15px'}),
            dcc.Graph(id='radar-chart', style={'height': '180px'}, config={'displayModeBar': False})
        ])
    ]),
    
    # ========== ROW 2: DÉPENSES PUBLIQUES ==========
    html.Div(style={
        'display': 'grid',
        'gridTemplateColumns': '1fr',
        'gap': '20px',
        'marginBottom': '30px'
    }, children=[
        html.Div(id='kpi-spending', style=CARD_STYLE)
    ]),
    
    # Store pour les données
    dcc.Store(id='data-store', data=df_wb.to_dict('records')),
    
    # Interval pour refresh
    dcc.Interval(id='interval', interval=60000, n_intervals=0)
])


# ==================== CALLBACKS ====================

@app.callback(
    Output('kpi-gdp', 'children'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value'),
     Input('data-store', 'data')]
)
def update_gdp_kpi(country, year, data):
    if not data or not country or not year:
        return create_kpi_card("Taux de croissance du PIB", "N/A", None, COLORS['primary'])
    
    df = pd.DataFrame(data)
    
    # Valeur actuelle
    df_current = df[(df['country'] == country) & 
                    (df['year'] == year) & 
                    (df['indicator'] == 'NY.GDP.MKTP.KD.ZG')]
    
    current_value = df_current['value'].iloc[0] if not df_current.empty else None
    
    # Données historiques pour sparkline (5 dernières années)
    df_history = df[(df['country'] == country) & 
                    (df['indicator'] == 'NY.GDP.MKTP.KD.ZG')]
    df_history = df_history.sort_values('year').tail(10)
    
    sparkline_data = df_history['value'].tolist() if not df_history.empty else None
    
    return create_kpi_card(
        "Taux de croissance\ndu PIB",
        f"+{current_value:.1f}%" if current_value and current_value > 0 else f"{current_value:.1f}%" if current_value else "N/A",
        sparkline_data,
        COLORS['primary']
    )


@app.callback(
    Output('kpi-poverty', 'children'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value'),
     Input('data-store', 'data')]
)
def update_poverty_kpi(country, year, data):
    if not data or not country or not year:
        return create_kpi_card_simple("Taux de pauvreté\n(1,90 USD/jour)", "N/A", COLORS['primary'])
    
    df = pd.DataFrame(data)
    df_current = df[(df['country'] == country) & 
                    (df['year'] == year) & 
                    (df['indicator'] == 'SI.POV.DDAY')]
    
    value = df_current['value'].iloc[0] if not df_current.empty else None
    
    return create_kpi_card_simple(
        "Taux de pauvreté\n(1,90 USD/jour)",
        f"${value:,.0f}" if value else "N/A",
        COLORS['primary']
    )


@app.callback(
    Output('kpi-gni', 'children'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value'),
     Input('data-store', 'data')]
)
def update_gni_kpi(country, year, data):
    if not data or not country or not year:
        return create_kpi_card_simple("RNB par habitant (USD)", "N/A", COLORS['primary'])
    
    df = pd.DataFrame(data)
    df_current = df[(df['country'] == country) & 
                    (df['year'] == year) & 
                    (df['indicator'] == 'NY.GNP.PCAP.CD')]
    
    value = df_current['value'].iloc[0] if not df_current.empty else None
    
    return create_kpi_card_simple(
        "RNB par habitant (USD)",
        f"${value:,.0f}" if value else "N/A",
        COLORS['primary']
    )


@app.callback(
    Output('kpi-spending', 'children'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value'),
     Input('data-store', 'data')]
)
def update_spending_kpi(country, year, data):
    if not data or not country or not year:
        return html.Div("Chargement...", style={'color': COLORS['text_dim']})
    
    df = pd.DataFrame(data)
    
    # Dépenses santé
    df_health = df[(df['country'] == country) & 
                   (df['year'] == year) & 
                   (df['indicator'] == 'SH.XPD.GHED.GD.ZS')]
    health = df_health['value'].iloc[0] if not df_health.empty else 0
    
    # Dépenses éducation
    df_edu = df[(df['country'] == country) & 
                (df['year'] == year) & 
                (df['indicator'] == 'SE.XPD.TOTL.GD.ZS')]
    edu = df_edu['value'].iloc[0] if not df_edu.empty else 0
    
    total = health + edu if health and edu else 0
    
    return html.Div([
        html.Div("Dépenses publiques", style={'color': COLORS['text'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
        html.Div("(% du PIB)", style={'color': COLORS['text_dim'], 'fontSize': '0.8rem', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div(f"{total:.0f}ᵉˢᵗ" if total else "N/A", 
                    style={'color': COLORS['text'], 'fontSize': '2.5rem', 'fontWeight': 'bold', 'marginBottom': '20px'})
        ]),
        
        # Barres de progression
        html.Div([
            create_progress_bar("Voix et accontabilité", 56),
            create_progress_bar("Vide du loi", 22),
            create_progress_bar("Stabilité patl politique", 66),
            create_progress_bar("Contrôle de corruption", 49),
            create_progress_bar("Effectivite ducable", 82),
            create_progress_bar("Efficacinert", 66),
        ])
    ])


@app.callback(
    Output('radar-chart', 'figure'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value')]
)
def update_radar(country, year):
    # Données simulées pour le radar chart
    categories = DOING_BUSINESS_INDICATORS
    values = [56, 22, 66, 49, 82, 66]  # Pourcentages simulés
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor=f'rgba(0, 217, 255, 0.2)',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=6, color=COLORS['primary'])
    ))
    
    fig.update_layout(
        polar=dict(
            bgcolor=COLORS['card'],
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
                gridcolor=COLORS['grid']
            ),
            angularaxis=dict(
                gridcolor=COLORS['grid'],
                linecolor=COLORS['grid']
            )
        ),
        showlegend=False,
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        margin=dict(l=40, r=40, t=20, b=20),
        font=dict(color=COLORS['text_dim'], size=9)
    )
    
    return fig


# ==================== FONCTIONS HELPER ====================

def create_kpi_card(title, value, sparkline_data, color):
    """Crée une carte KPI avec sparkline"""
    children = [
        html.Div(title, style={
            'color': COLORS['text'],
            'fontSize': '0.85rem',
            'marginBottom': '15px',
            'whiteSpace': 'pre-line',
            'lineHeight': '1.3'
        }),
        html.Div(value, style={
            'color': color,
            'fontSize': '2.5rem',
            'fontWeight': 'bold',
            'marginBottom': '15px'
        })
    ]
    
    # Ajouter sparkline si disponible
    if sparkline_data and len(sparkline_data) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=sparkline_data,
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f'rgba(0, 217, 255, 0.1)'
        ))
        fig.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=60
        )
        children.append(dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '60px'}))
    
    return html.Div(children)


def create_kpi_card_simple(title, value, color):
    """Crée une carte KPI simple sans graphique"""
    return html.Div([
        html.Div(title, style={
            'color': COLORS['text'],
            'fontSize': '0.85rem',
            'marginBottom': '15px',
            'whiteSpace': 'pre-line',
            'lineHeight': '1.3'
        }),
        html.Div(value, style={
            'color': color,
            'fontSize': '2.5rem',
            'fontWeight': 'bold'
        })
    ])


def create_progress_bar(label, percentage):
    """Crée une barre de progression"""
    return html.Div(style={'marginBottom': '12px'}, children=[
        html.Div([
            html.Span(label, style={'color': COLORS['text'], 'fontSize': '0.85rem'}),
            html.Span(f"{percentage}%", style={'color': COLORS['primary'], 'fontSize': '0.85rem', 'float': 'right'})
        ], style={'marginBottom': '5px'}),
        html.Div(style={
            'width': '100%',
            'height': '8px',
            'backgroundColor': COLORS['background'],
            'borderRadius': '4px',
            'overflow': 'hidden'
        }, children=[
            html.Div(style={
                'width': f'{percentage}%',
                'height': '100%',
                'backgroundColor': COLORS['bar'],
                'transition': 'width 0.3s ease'
            })
        ])
    ])


# ==================== DÉMARRAGE ====================
if __name__ == '__main__':
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "    DASHBOARD BANQUE MONDIALE - PREMIUM DESIGN".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    print(f"    🌍 Pays: {len(countries)}")
    print(f"    📊 Observations: {len(df_wb):,}")
    print(f"    🎨 Style: Fond noir + Cyan/Bleu")
    print(f"\n    🌐 URL: http://127.0.0.1:8052")
    print(f"    🛑 Arrêter: Ctrl+C\n")
    
    app.run(debug=False, host='127.0.0.1', port=8052)

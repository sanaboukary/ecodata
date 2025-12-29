"""
Tableau de Bord Interactif BRVM - Expert Level
Application Dash professionnelle avec données réelles
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

# Ajouter le répertoire du projet au path pour importer les modules Django
sys.path.insert(0, str(Path(__file__).parent))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.connectors.brvm import fetch_brvm
from scripts.connectors.brvm_stocks import BRVM_STOCKS, get_all_symbols

# Connexion MongoDB via Django
client, db = get_mongo_db()

# Cache pour les données en temps réel
_live_data_cache = {'data': None, 'timestamp': None}

# Récupération des données BRVM
def get_brvm_data(use_live=False):
    """
    Récupère les données BRVM de MongoDB ou en temps réel
    
    Args:
        use_live: Si True, récupère les données en direct de la source BRVM
    """
    if use_live:
        # Utiliser le cache si les données ont moins de 8 secondes
        now = datetime.now()
        if (_live_data_cache['data'] is not None and 
            _live_data_cache['timestamp'] is not None and 
            (now - _live_data_cache['timestamp']).total_seconds() < 8):
            return _live_data_cache['data']
        
        # Récupérer les nouvelles données en direct
        try:
            live_data = fetch_brvm()
            if live_data:
                df = pd.DataFrame(live_data)
                df['timestamp'] = pd.to_datetime(df['ts'])
                df['price'] = df['close']
                df['open'] = df.get('open', df['close'])
                df['high'] = df.get('high', df['close'])
                df['low'] = df.get('low', df['close'])
                
                # Mettre en cache
                _live_data_cache['data'] = df
                _live_data_cache['timestamp'] = now
                print(f"✅ Données LIVE récupérées: {len(df)} observations à {now.strftime('%H:%M:%S')}")
                return df
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération des données live: {e}")
            # Fallback vers MongoDB
    
    # Récupérer depuis MongoDB (toujours à jour car collecte automatique)
    cursor = db.curated_observations.find(
        {"source": "BRVM"},
        sort=[("ts", -1)],
        limit=5000  # Limiter pour performance
    )
    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
    
    # Conversion en DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['ts'])
    
    # Extraction du symbole depuis key (format: "BRVM-SYMBOL" ou juste "SYMBOL")
    df['symbol'] = df['key'].apply(lambda k: k.replace('BRVM-', '') if isinstance(k, str) else k)
    
    # Extraction OHLCV depuis attrs (champ attrs ou attributes)
    def get_attr(row, field, default=0):
        attrs = row.get('attrs') or row.get('attributes') or {}
        return attrs.get(field, default) if isinstance(attrs, dict) else default
    
    df['open'] = df.apply(lambda row: get_attr(row, 'open', row.get('value', 0)), axis=1)
    df['high'] = df.apply(lambda row: get_attr(row, 'high', row.get('value', 0)), axis=1)
    df['low'] = df.apply(lambda row: get_attr(row, 'low', row.get('value', 0)), axis=1)
    df['volume'] = df.apply(lambda row: get_attr(row, 'volume', 0), axis=1)
    
    # Close = value
    df['close'] = df['value']
    df['price'] = df['value']
    
    # Enrichir avec les métadonnées des stocks connus
    def enrich_stock(symbol):
        stock_info = BRVM_STOCKS.get(symbol, {})
        return {
            'name': stock_info.get('name', symbol),
            'sector': stock_info.get('sector', 'N/A'),
            'country': stock_info.get('country', 'N/A')
        }
    
    enriched = df['symbol'].apply(enrich_stock).apply(pd.Series)
    df['name'] = enriched['name']
    df['sector'] = enriched['sector']
    df['country'] = enriched['country']
    
    return df

# Calcul des indicateurs
def calculate_market_indicators(df):
    """Calcule les indicateurs de marché"""
    if df.empty:
        return {
            'brvm10': 0,
            'brvm10_change': 0,
            'composite': 0,
            'composite_change': 0,
            'total_volume': 0,
            'total_cap': 0,
            'avg_variation': 0
        }
    
    # Simule les indices (à remplacer par le vrai calcul)
    latest_prices = df.sort_values('timestamp').groupby('symbol').last()
    
    # BRVM 10 - Top 10 capitalisations
    brvm10 = 261.21
    brvm10_change = 0.53
    
    # BRVM Composite
    composite = 208.03
    composite_change = 0.46
    
    # Volume total
    total_volume = df['volume'].sum()
    
    # Capitalisation totale (exemple)
    total_cap = 7890.4
    
    # Variation moyenne sectorielle
    avg_variation = -0.4
    
    return {
        'brvm10': brvm10,
        'brvm10_change': brvm10_change,
        'composite': composite,
        'composite_change': composite_change,
        'total_volume': total_volume / 1e6,  # En millions
        'total_cap': total_cap,
        'avg_variation': avg_variation
    }

# Initialisation de l'application Dash
app = dash.Dash(
    __name__,
    title="Tableau de Bord BRVM",
    update_title="Chargement...",
    suppress_callback_exceptions=True
)

# Chargement des données
df_brvm = get_brvm_data()
indicators = calculate_market_indicators(df_brvm)

# Couleurs du thème (style Bloomberg/TradingView)
COLORS = {
    'background': '#0a0a0a',
    'card_bg': '#1a1a1a',
    'text': '#e8e8e8',
    'gold': '#d4af37',
    'green': '#00ff88',
    'red': '#ff3366',
    'blue': '#3366ff',
    'grid': '#2a2a2a',
    'border': '#333333'
}

# Style CSS personnalisé
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: #0a0a0a;
                color: #e8e8e8;
            }
            
            .header {
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                padding: 20px 40px;
                border-bottom: 2px solid #d4af37;
            }
            
            .header-title {
                font-size: 28px;
                font-weight: 700;
                color: #d4af37;
                letter-spacing: 2px;
            }
            
            .metric-card {
                background: #1a1a1a;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #333333;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                transition: transform 0.2s;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                border-color: #d4af37;
            }
            
            .metric-value {
                font-size: 36px;
                font-weight: 700;
                margin: 10px 0;
            }
            
            .metric-label {
                font-size: 12px;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .positive {
                color: #00ff88;
            }
            
            .negative {
                color: #ff3366;
            }
            
            .chart-container {
                background: #1a1a1a;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #333333;
                margin: 20px 0;
            }
            
            /* Dropdown personnalisé - Style gold premium */
            .custom-dropdown .Select-control {
                background-color: #1a1a1a !important;
                border: 2px solid #d4af37 !important;
                border-radius: 8px !important;
                min-height: 45px !important;
                box-shadow: 0 2px 8px rgba(212, 175, 55, 0.2) !important;
            }
            
            .custom-dropdown .Select-control:hover {
                border-color: #e8c04f !important;
                box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4) !important;
            }
            
            .custom-dropdown .Select-menu-outer {
                background-color: #1a1a1a !important;
                border: 2px solid #d4af37 !important;
                border-radius: 8px !important;
                margin-top: 4px !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5) !important;
            }
            
            .custom-dropdown .Select-menu {
                max-height: 400px !important;
            }
            
            .custom-dropdown .Select-option {
                background-color: #1a1a1a !important;
                color: #e8e8e8 !important;
                padding: 12px 16px !important;
                border-bottom: 1px solid #2a2a2a !important;
                transition: all 0.2s ease !important;
            }
            
            .custom-dropdown .Select-option:hover {
                background-color: #2a2a2a !important;
                color: #d4af37 !important;
                transform: translateX(5px) !important;
            }
            
            .custom-dropdown .Select-option.is-selected {
                background-color: #d4af37 !important;
                color: #1a1a1a !important;
                font-weight: 600 !important;
            }
            
            .custom-dropdown .Select-value-label {
                color: #e8e8e8 !important;
                font-weight: 500 !important;
            }
            
            .custom-dropdown .Select-placeholder {
                color: #888 !important;
            }
            
            .custom-dropdown .Select-arrow {
                border-color: #d4af37 transparent transparent !important;
            }
            
            .custom-dropdown .Select-input > input {
                color: #e8e8e8 !important;
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

# Layout de l'application - Design Final selon image de référence
app.layout = html.Div([
    # En-tête avec titre et indicateur de mise à jour
    html.Div([
        html.Div([
            html.H1("BOURSE RÉGIONALE DES VALEURS MOBILIÈRES", className="header-title"),
            html.Div(id='last-update', 
                    style={'fontSize': '12px', 'color': '#888', 'marginTop': '5px'}),
        ], style={'flex': '1'}),
    ], className="header", style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
    
    # Indicateurs principaux - Header avec 5 cartes (dynamiques)
    html.Div([
        # BRVM 10
        html.Div([
            html.Div([
                html.Div("BRVM 10", className="metric-label"),
                html.Div(id='brvm10-value', className="metric-value positive"),
                html.Div(id='brvm10-change', style={'fontSize': '14px', 'marginTop': '5px'}),
            ], className="metric-card")
        ], style={'width': '18%'}),
        
        # BRVM Composite
        html.Div([
            html.Div([
                html.Div("BRVM Composite", className="metric-label"),
                html.Div(id='composite-value', className="metric-value positive"),
                html.Div(id='composite-change', style={'fontSize': '14px', 'marginTop': '5px'}),
            ], className="metric-card")
        ], style={'width': '18%'}),
        
        # Graphique Coursesel (mini-chart de tendance)
        html.Div([
            html.Div([
                html.Div("Coursesel", className="metric-label"),
                dcc.Graph(id='mini-chart', config={'displayModeBar': False},
                         style={'height': '80px', 'marginTop': '10px'})
            ], className="metric-card")
        ], style={'width': '28%'}),
        
        # Valeur négociée
        html.Div([
            html.Div([
                html.Div("Valeur Négociée", className="metric-label"),
                html.Div(id='volume-value', className="metric-value", style={'color': COLORS['gold']}),
                html.Div(id='cap-value', style={'fontSize': '11px', 'color': '#888', 'marginTop': '5px'}),
            ], className="metric-card")
        ], style={'width': '18%'}),
        
        # Taux de Variation
        html.Div([
            html.Div([
                html.Div("Taux de Variation", className="metric-label"),
                html.Div(id='variation-value', className="metric-value negative"),
                html.Div("Moyen Sectoriel", style={'fontSize': '11px', 'color': '#888', 'marginTop': '5px'}),
            ], className="metric-card")
        ], style={'width': '18%'}),
        
    ], style={'display': 'flex', 'gap': '15px', 'padding': '20px 30px', 'background': COLORS['background']}),
    
    # Cours moyens journaliers + Graphique principal
    html.Div([
        # Colonne gauche - Cours moyens
        html.Div([
            html.Div("COURS MOYENS JOURNALIERS DES ACTIONS", 
                    style={'fontSize': '14px', 'marginBottom': '15px', 'color': '#888'}),
            
            # Actions en hausse
            html.Div([
                html.Div([
                    html.Div(symbol, style={'fontSize': '12px', 'marginBottom': '5px'}),
                    html.Div(id=f'chart-{symbol.lower()}', children=[
                        dcc.Graph(id=f'mini-{symbol.lower()}', config={'displayModeBar': False},
                                 style={'height': '40px'})
                    ])
                ], className="metric-card", style={'padding': '10px', 'marginBottom': '10px'})
                for symbol in ['SONATEL', 'ONATEL BF', 'BOA BF', 'SIBTL CI', 'TOTAL']
            ]),
            
            # Actions en baisse
            html.Div([
                html.Div([
                    html.Div(symbol, style={'fontSize': '12px'}),
                    html.Div(change, style={'color': COLORS['red'], 'fontSize': '16px', 'fontWeight': '600'})
                ], className="metric-card", 
                style={'padding': '10px', 'marginBottom': '10px', 'background': '#1a0a0a'})
                for symbol, change in [
                    ('ECOBANK CI', '-0,4 %'),
                    ('FILTISAC', '-0,9 %'),
                    ('PALM CI', '-1,3 %'),
                    ('BOA CI', '-1,6 %')
                ]
            ]),
            
        ], style={'width': '25%', 'padding': '20px'}),
        
        # Graphique principal avec sélecteur d'action
        html.Div([
            # Sélecteur d'action - Box bien visible avec toutes les 47 actions
            html.Div([
                html.Label(
                    "SELECTIONNER UNE ACTION",
                    htmlFor='stock-selector',
                    style={
                        'fontSize': '14px', 
                        'color': COLORS['gold'], 
                        'marginBottom': '10px',
                        'fontWeight': '600',
                        'textTransform': 'uppercase',
                        'letterSpacing': '1px',
                        'display': 'block'
                    }
                ),
                dcc.Dropdown(
                    id='stock-selector',
                    options=[
                        {'label': '📈 BRVM Composite (Indice Global)', 'value': 'COMPOSITE'}
                    ] + [
                        {
                            'label': f'{BRVM_STOCKS[sym]["name"]} ({sym}) - {BRVM_STOCKS[sym]["sector"]}',
                            'value': sym
                        }
                        for sym in sorted(get_all_symbols())
                    ],
                    value='COMPOSITE',
                    clearable=False,
                    searchable=True,
                    placeholder="Choisir une action...",
                    style={
                        'width': '100%',
                        'fontFamily': 'Inter, sans-serif'
                    },
                    className='custom-dropdown'
                )
            ], style={
                'marginBottom': '25px', 
                'padding': '25px', 
                'background': 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)', 
                'borderRadius': '15px',
                'border': '3px solid #d4af37',
                'boxShadow': '0 8px 16px rgba(212, 175, 55, 0.4)',
                'transition': 'all 0.3s ease'
            }),
            
            # Graphique
            dcc.Graph(id='main-chart', style={'height': '500px'})
        ], style={'width': '50%'}),
        
        # Colonne droite - Indicateurs techniques + Stats
        html.Div([
            # Indicateurs techniques pour l'action sélectionnée
            html.Div([
                html.Div("INDICATEURS TECHNIQUES", style={'fontSize': '14px', 'marginBottom': '10px', 'color': '#888'}),
                html.Div(id='technical-indicators', children=[
                    html.Div("Sélectionnez une action", style={'color': '#666', 'fontSize': '12px', 'padding': '20px'})
                ])
            ], className="metric-card", style={'marginBottom': '20px'}),
            
            # Perdants
            html.Div([
                html.Div("PERDANTS", style={'fontSize': '14px', 'marginBottom': '10px', 'color': '#888'}),
                html.Div([
                    html.Div([
                        html.Div(stock, style={'fontSize': '12px'}),
                        html.Div(change, style={'color': COLORS['red'], 'fontSize': '14px'})
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 
                             'padding': '8px 0', 'borderBottom': '1px solid #2a2a2a'})
                    for stock, change in [
                        ('PALM CI', '-3,2 %'),
                        ('SERVAIR ABIDJAN', '-2,7 %'),
                        ('BICICI', '-1,8 %'),
                        ('SUCRIVOIRE', '-1,8 %'),
                        ('FILTISAC', '-1,6 %')
                    ]
                ])
            ], className="metric-card", style={'marginBottom': '20px'}),
            
            # Capitalisation
            html.Div([
                html.Div(f"{indicators['total_cap']:.1f} Md FCFA", 
                        className="metric-value", style={'color': COLORS['gold']}),
                html.Div("Capitalisation Totale", style={'fontSize': '12px', 'color': '#888'}),
                html.Div("13,9 Md USD", style={'fontSize': '10px', 'color': '#666', 'marginTop': '5px'}),
            ], className="metric-card", style={'marginBottom': '20px'}),
            
            # Taux de variation
            html.Div([
                html.Div(f"{indicators['avg_variation']:.1f} %", 
                        className="metric-value negative"),
                html.Div("Taux de Variation", style={'fontSize': '12px', 'color': '#888'}),
                html.Div("Moyen Sectoriel", style={'fontSize': '10px', 'color': '#666', 'marginTop': '5px'}),
            ], className="metric-card"),
            
        ], style={'width': '25%', 'padding': '20px'}),
        
    ], style={'display': 'flex', 'gap': '0px'}),
    
    # Granularité et graphiques détaillés
    html.Div([
        html.Div([
            html.Div("Granularité : Seconde", style={'fontSize': '14px', 'marginBottom': '10px'}),
            html.Div("Evolution en secondes", style={'fontSize': '10px', 'color': '#888', 'marginBottom': '10px'}),
            dcc.Graph(id='granularity-chart', style={'height': '80px'}),
            
            # Mini charts pour actions
            html.Div([
                html.Div([
                    html.Div(stock, style={'fontSize': '10px', 'marginBottom': '5px'}),
                    dcc.Graph(id=f'stock-{stock.lower().replace(" ", "-")}', 
                             config={'displayModeBar': False},
                             style={'height': '30px'})
                ], style={'marginBottom': '15px'})
                for stock in ['SONATEL', 'ONATEL BF', 'BOA BF', 'SIBTL CI']
            ]),
            
            html.Div(f"{indicators['total_volume']:.2f}K", 
                    className="metric-value", style={'color': COLORS['gold'], 'fontSize': '24px'}),
            
        ], style={'width': '20%', 'padding': '20px'}),
        
        html.Div([
            html.Div([
                html.Div("Productions en Bourse", style={'fontSize': '12px', 'marginBottom': '10px'}),
                dcc.Graph(id='production-chart', style={'height': '150px'}),
            ])
        ], style={'width': '80%', 'padding': '20px'}),
        
    ], style={'display': 'flex', 'background': '#0a0a0a', 'borderTop': '1px solid #333'}),
    
    # Intervalle de mise à jour
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # 10 secondes - données en temps réel
        n_intervals=0
    ),
    
    # Store pour les données live
    dcc.Store(id='live-mode', data=True)  # Mode live activé par défaut
    
], style={'background': COLORS['background'], 'minHeight': '100vh'})


# ========== CALLBACKS ==========

# Callback 0: Indicateur de dernière mise à jour
@app.callback(
    Output('last-update', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_timestamp(n):
    """Affiche l'heure de la dernière mise à jour"""
    now = datetime.now()
    return f"⏱️ Dernière mise à jour: {now.strftime('%H:%M:%S')} | Actualisation toutes les 10s"

# Callback pour les KPIs du header
@app.callback(
    [Output('brvm10-value', 'children'),
     Output('brvm10-change', 'children'),
     Output('brvm10-change', 'style'),
     Output('composite-value', 'children'),
     Output('composite-change', 'children'),
     Output('composite-change', 'style'),
     Output('volume-value', 'children'),
     Output('cap-value', 'children'),
     Output('variation-value', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_header_kpis(n):
    """Met à jour les KPIs du header en temps réel"""
    df = get_brvm_data(use_live=True)
    
    if df.empty:
        return "N/A", "N/A", {}, "N/A", "N/A", {}, "N/A", "N/A", "N/A"
    
    indicators = calculate_market_indicators(df)
    
    # BRVM 10
    brvm10_val = f"{indicators['brvm10']:.2f}"
    brvm10_chg = f"+{indicators['brvm10_change']:.2f} %" if indicators['brvm10_change'] >= 0 else f"{indicators['brvm10_change']:.2f} %"
    brvm10_style = {'color': COLORS['green'] if indicators['brvm10_change'] >= 0 else COLORS['red'], 'fontSize': '14px', 'marginTop': '5px'}
    
    # Composite
    comp_val = f"{indicators['composite']:.2f}"
    comp_chg = f"+{indicators['composite_change']:.2f} %" if indicators['composite_change'] >= 0 else f"{indicators['composite_change']:.2f} %"
    comp_style = {'color': COLORS['green'] if indicators['composite_change'] >= 0 else COLORS['red'], 'fontSize': '14px', 'marginTop': '5px'}
    
    # Volume
    vol_val = f"{indicators['total_volume']:.2f} K"
    cap_val = f"Capitalisation : {indicators['total_cap']:.0f} Md FCFA"
    
    # Variation moyenne
    var_val = f"{indicators['avg_variation']:.1f} %"
    
    return brvm10_val, brvm10_chg, brvm10_style, comp_val, comp_chg, comp_style, vol_val, cap_val, var_val

# Callback 1: Générer les mini-charts pour toutes les actions dans la colonne gauche
@app.callback(
    Output('stock-mini-charts-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_stock_mini_charts(n):
    """Génère dynamiquement les mini-charts pour chaque action"""
    df = get_brvm_data(use_live=True)
    
    if df.empty:
        return html.Div("Aucune donnée disponible", style={'color': '#888', 'fontSize': '11px'})
    
    # Obtenir la liste des actions avec leurs derniers prix
    price_col = 'close' if 'close' in df.columns else 'price'
    latest_by_stock = df.sort_values('timestamp').groupby('symbol').tail(20)
    
    # Grouper par symbole
    stocks = df.groupby('symbol').agg({
        'name': 'first',
        price_col: 'last'
    }).reset_index()
    stocks = stocks.sort_values(price_col, ascending=False).head(20)  # Top 20 par prix
    
    mini_charts = []
    
    for _, stock in stocks.iterrows():
        symbol = stock['symbol']
        name = stock['name'] if stock['name'] != 'N/A' else symbol
        current_price = stock[price_col]
        
        # Données pour ce stock
        stock_data = latest_by_stock[latest_by_stock['symbol'] == symbol].sort_values('timestamp')
        
        if len(stock_data) < 2:
            continue
        
        # Calculer la variation
        first_price = stock_data[price_col].iloc[0]
        variation = ((current_price - first_price) / first_price * 100) if first_price > 0 else 0
        color = COLORS['green'] if variation >= 0 else COLORS['red']
        
        # Créer le mini sparkline
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(stock_data))),
            y=stock_data[price_col],
            mode='lines',
            line=dict(color=color, width=1.5),
            fill='tozeroy',
            fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)',
            hovertemplate=f'%{{y:,.0f}} FCFA<extra></extra>'
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            height=35
        )
        
        # Card pour cette action
        mini_charts.append(
            html.Div([
                html.Div([
                    html.Div(symbol, style={'fontSize': '11px', 'fontWeight': '600', 'color': COLORS['text']}),
                    html.Div(f"{variation:+.1f}%", style={'fontSize': '10px', 'color': color, 'fontWeight': '600'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '5px'}),
                dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '35px'}),
                html.Div(f"{current_price:,.0f} F", 
                        style={'fontSize': '10px', 'color': '#888', 'marginTop': '3px'})
            ], className="metric-card", style={'padding': '8px', 'marginBottom': '8px', 'background': '#1a1a1a'})
        )
    
    return mini_charts


# Callback 2: Liste des perdants dans la colonne droite
@app.callback(
    Output('losers-list', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_losers_list(n):
    """Génère la liste des actions en baisse"""
    df = get_brvm_data(use_live=True)
    
    if df.empty:
        return html.Div("Aucune donnée", style={'color': '#888', 'fontSize': '11px'})
    
    price_col = 'close' if 'close' in df.columns else 'price'
    
    # Calculer les variations pour chaque action
    variations = []
    for symbol in df['symbol'].unique():
        stock_data = df[df['symbol'] == symbol].sort_values('timestamp')
        if len(stock_data) >= 2:
            first = stock_data[price_col].iloc[0]
            last = stock_data[price_col].iloc[-1]
            var = ((last - first) / first * 100) if first > 0 else 0
            name = stock_data['name'].iloc[-1] if 'name' in stock_data.columns else symbol
            variations.append({'symbol': symbol, 'name': name, 'variation': var, 'price': last})
    
    # Trier par variation (les plus négatifs en premier)
    variations_df = pd.DataFrame(variations).sort_values('variation').head(10)
    
    losers = []
    for _, row in variations_df.iterrows():
        losers.append(
            html.Div([
                html.Div(row['symbol'], style={'fontSize': '11px', 'fontWeight': '600'}),
                html.Div(f"{row['variation']:.2f}%", 
                        style={'fontSize': '11px', 'color': COLORS['red'], 'fontWeight': '600'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 
                     'padding': '6px 0', 'borderBottom': f'1px solid {COLORS["grid"]}'})
        )
    
    return losers


# Callback 3: Graphique principal (chandelier)
@app.callback(
    Output('main-chart', 'figure'),
    [Input('stock-selector', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_main_chart(selected_stock, n):
    """Met à jour le graphique principal en chandelier - action sélectionnée ou composite"""
    df = get_brvm_data(use_live=True)
    
    if df.empty:
        return go.Figure()
    
    # Si COMPOSITE sélectionné, agréger toutes les actions
    if selected_stock == 'COMPOSITE':
        df_filtered = df.sort_values('timestamp').groupby('timestamp').agg({
            'open': 'mean',
            'high': 'max',
            'low': 'min',
            'close': 'mean',
            'volume': 'sum'
        }).reset_index().tail(100)
        title = 'BRVM Composite - Évolution Globale'
        stock_name = 'BRVM Composite'
    else:
        # Filtrer pour l'action sélectionnée
        df_filtered = df[df['symbol'] == selected_stock].sort_values('timestamp').tail(100)
        stock_info = BRVM_STOCKS.get(selected_stock, {})
        stock_name = stock_info.get('name', selected_stock)
        title = f'{stock_name} ({selected_stock}) - Évolution du Cours'
    
    if df_filtered.empty or len(df_filtered) < 2:
        return go.Figure()
    
    # S'assurer qu'on a les bonnes colonnes OHLC
    if 'open' not in df_filtered.columns or df_filtered['open'].isna().all():
        df_filtered['open'] = df_filtered['close'] * 0.998
        df_filtered['high'] = df_filtered['close'] * 1.005
        df_filtered['low'] = df_filtered['close'] * 0.995
    
    fig = go.Figure()
    
    # Chandelier principal
    fig.add_trace(go.Candlestick(
        x=df_filtered['timestamp'],
        open=df_filtered['open'],
        high=df_filtered['high'],
        low=df_filtered['low'],
        close=df_filtered['close'],
        increasing_line_color=COLORS['green'],
        decreasing_line_color=COLORS['red'],
        name='Prix'
    ))
    
    # Ajouter une moyenne mobile sur 5 périodes
    if len(df_filtered) >= 5:
        df_filtered['ma5'] = df_filtered['close'].rolling(window=5).mean()
        fig.add_trace(go.Scatter(
            x=df_filtered['timestamp'],
            y=df_filtered['ma5'],
            mode='lines',
            name='MA5',
            line=dict(color='#3366ff', width=1, dash='dot'),
            opacity=0.7
        ))
    
    # Ajouter une moyenne mobile sur 10 périodes
    if len(df_filtered) >= 10:
        df_filtered['ma10'] = df_filtered['close'].rolling(window=10).mean()
        fig.add_trace(go.Scatter(
            x=df_filtered['timestamp'],
            y=df_filtered['ma10'],
            mode='lines',
            name='MA10',
            line=dict(color='#d4af37', width=1, dash='dash'),
            opacity=0.7
        ))
    
    # Calculer la variation
    if len(df_filtered) >= 2:
        first_price = df_filtered['close'].iloc[0]
        last_price = df_filtered['close'].iloc[-1]
        variation = ((last_price - first_price) / first_price * 100) if first_price > 0 else 0
        var_color = COLORS['green'] if variation >= 0 else COLORS['red']
        var_text = f" ({variation:+.2f}%)"
    else:
        var_text = ""
        var_color = COLORS['text']
    
    fig.update_layout(
        title={
            'text': f'{title}{var_text}',
            'font': {'color': var_color if var_text else COLORS['gold']}
        },
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['card_bg'],
        font_color=COLORS['text'],
        xaxis=dict(
            gridcolor=COLORS['grid'],
            showgrid=True,
            title="",
            rangeslider_visible=False
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            showgrid=True,
            title="Prix (FCFA)",
            side='right'
        ),
        margin=dict(l=0, r=50, t=40, b=30),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(26, 26, 26, 0.8)'
        )
    )
    
    return fig


# Callback 4: Mini-chart dans l'header (Coursesel)
@app.callback(
    Output('mini-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_mini_chart(n):
    """Mini graphique pour l'en-tête avec données en temps réel"""
    df = get_brvm_data(use_live=True)
    
    if df.empty:
        return go.Figure()
    
    # Utiliser close au lieu de price si disponible
    price_col = 'close' if 'close' in df.columns else 'price'
    df_agg = df.groupby('timestamp').agg({price_col: 'mean'}).reset_index()
    df_agg = df_agg.sort_values('timestamp').tail(50)
    df_agg.rename(columns={price_col: 'price'}, inplace=True)
    
    # Déterminer la couleur selon la tendance
    color = COLORS['green']
    if len(df_agg) > 1:
        if df_agg['price'].iloc[-1] < df_agg['price'].iloc[0]:
            color = COLORS['red']
    
    fig = go.Figure(data=[go.Scatter(
        x=df_agg['timestamp'],
        y=df_agg['price'],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)'
    )])
    
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


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TABLEAU DE BORD BRVM - NIVEAU EXPERT")
    print("Connecte aux sources de donnees en temps reel")
    print("="*80)
    print(f"\nDemarrage du tableau de bord interactif BRVM...")
    print(f"\nConnexion aux sources de donnees:")
    print(f"  - MongoDB: {len(df_brvm)} observations historiques")
    print(f"  - Connecteur BRVM: {len(BRVM_STOCKS)} actions cotees en temps reel")
    print(f"  - Mise a jour: toutes les 10 secondes")
    print(f"\nAcces: http://127.0.0.1:8050")
    print(f"Mode LIVE active - Donnees en temps reel")
    print(f"Pour arreter: Ctrl+C")
    print("="*80 + "\n")
    
    # Désactiver le debug mode pour éviter les problèmes de socket sous Windows
    app.run(debug=False, host='127.0.0.1', port=8050)

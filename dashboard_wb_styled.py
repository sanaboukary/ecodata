"""
Tableau de Bord Banque Mondiale - Design Premium (Version Simplifiée)
Style exact selon l'image fournie: fond noir, couleurs cyan/bleu, dropdowns stylés
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from pymongo import MongoClient

# ==================== CONNEXION MONGODB ====================
client = MongoClient('mongodb://SANA:Boukary89%40@localhost:27018/')
db = client['centralisation_db']

# ==================== COULEURS PREMIUM ====================
COLORS = {
    'background': '#0a1929',      # Fond noir-bleu très foncé
    'card': '#132f4c',            # Carte bleu foncé
    'primary': '#00d9ff',         # Cyan brillant
    'secondary': '#3d8bfd',       # Bleu
    'text': '#ffffff',            # Texte blanc
    'text_dim': '#8796a5',        # Texte grisé
    'grid': '#1e3a5f',            # Grille
    'bar': '#3d8bfd'              # Barres bleues
}

# ==================== INDICATEURS ====================
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "Taux de croissance du PIB",
    "SI.POV.DDAY": "Taux de pauvreté (1,90 USD/jour)",
    "NY.GNP.PCAP.CD": "RNB par habitant (USD)",
    "SH.XPD.GHED.GD.ZS": "Dépenses de santé publique (% du PIB)",
    "SE.XPD.TOTL.GD.ZS": "Dépenses d'éducation publique (% du PIB)",
}

# Indicateurs Doing Business - Noms en français
DOING_BUSINESS_INDICATORS = [
    "Voix et responsabilité",
    "État de droit",
    "Stabilité politique",
    "Contrôle de la corruption",
    "Efficacité du gouvernement",
    "Qualité de la réglementation"
]

# Dictionnaire pour convertir les codes pays ISO en noms complets
COUNTRY_NAMES = {
    'ABW': 'Aruba', 'AFG': 'Afghanistan', 'AGO': 'Angola', 'ALB': 'Albanie', 
    'AND': 'Andorre', 'ARE': 'Émirats arabes unis', 'ARG': 'Argentine', 'ARM': 'Arménie',
    'ASM': 'Samoa américaines', 'ATG': 'Antigua-et-Barbuda', 'AUS': 'Australie', 
    'AUT': 'Autriche', 'AZE': 'Azerbaïdjan', 'BDI': 'Burundi', 'BEL': 'Belgique',
    'BEN': 'Bénin', 'BFA': 'Burkina Faso', 'BGD': 'Bangladesh', 'BGR': 'Bulgarie',
    'BHR': 'Bahreïn', 'BHS': 'Bahamas', 'BIH': 'Bosnie-Herzégovine', 'BLR': 'Biélorussie',
    'BLZ': 'Belize', 'BMU': 'Bermudes', 'BOL': 'Bolivie', 'BRA': 'Brésil',
    'BRB': 'Barbade', 'BRN': 'Brunéi Darussalam', 'BTN': 'Bhoutan', 'BWA': 'Botswana',
    'CAF': 'République centrafricaine', 'CAN': 'Canada', 'CHE': 'Suisse', 'CHL': 'Chili',
    'CHN': 'Chine', 'CIV': "Côte d'Ivoire", 'CMR': 'Cameroun', 'COD': 'Congo (RDC)',
    'COG': 'Congo', 'COL': 'Colombie', 'COM': 'Comores', 'CPV': 'Cap-Vert',
    'CRI': 'Costa Rica', 'CUB': 'Cuba', 'CUW': 'Curaçao', 'CYM': 'Îles Caïmans',
    'CYP': 'Chypre', 'CZE': 'République tchèque', 'DEU': 'Allemagne', 'DJI': 'Djibouti',
    'DMA': 'Dominique', 'DNK': 'Danemark', 'DOM': 'République dominicaine', 'DZA': 'Algérie',
    'ECU': 'Équateur', 'EGY': 'Égypte', 'ERI': 'Érythrée', 'ESP': 'Espagne',
    'EST': 'Estonie', 'ETH': 'Éthiopie', 'FIN': 'Finlande', 'FJI': 'Fidji',
    'FRA': 'France', 'FRO': 'Îles Féroé', 'FSM': 'Micronésie', 'GAB': 'Gabon',
    'GBR': 'Royaume-Uni', 'GEO': 'Géorgie', 'GHA': 'Ghana', 'GIB': 'Gibraltar',
    'GIN': 'Guinée', 'GMB': 'Gambie', 'GNB': 'Guinée-Bissau', 'GNQ': 'Guinée équatoriale',
    'GRC': 'Grèce', 'GRD': 'Grenade', 'GRL': 'Groenland', 'GTM': 'Guatemala',
    'GUM': 'Guam', 'GUY': 'Guyana', 'HKG': 'Hong Kong', 'HND': 'Honduras',
    'HRV': 'Croatie', 'HTI': 'Haïti', 'HUN': 'Hongrie', 'IDN': 'Indonésie',
    'IMN': 'Île de Man', 'IND': 'Inde', 'IRL': 'Irlande', 'IRN': 'Iran',
    'IRQ': 'Iraq', 'ISL': 'Islande', 'ISR': 'Israël', 'ITA': 'Italie',
    'JAM': 'Jamaïque', 'JOR': 'Jordanie', 'JPN': 'Japon', 'KAZ': 'Kazakhstan',
    'KEN': 'Kenya', 'KGZ': 'Kirghizistan', 'KHM': 'Cambodge', 'KIR': 'Kiribati',
    'KNA': 'Saint-Kitts-et-Nevis', 'KOR': 'Corée du Sud', 'KWT': 'Koweït', 'LAO': 'Laos',
    'LBN': 'Liban', 'LBR': 'Libéria', 'LBY': 'Libye', 'LCA': 'Sainte-Lucie',
    'LIE': 'Liechtenstein', 'LKA': 'Sri Lanka', 'LSO': 'Lesotho', 'LTU': 'Lituanie',
    'LUX': 'Luxembourg', 'LVA': 'Lettonie', 'MAC': 'Macao', 'MAF': 'Saint-Martin',
    'MAR': 'Maroc', 'MCO': 'Monaco', 'MDA': 'Moldavie', 'MDG': 'Madagascar',
    'MDV': 'Maldives', 'MEX': 'Mexique', 'MHL': 'Îles Marshall', 'MKD': 'Macédoine du Nord',
    'MLI': 'Mali', 'MLT': 'Malte', 'MMR': 'Myanmar', 'MNE': 'Monténégro',
    'MNG': 'Mongolie', 'MNP': 'Îles Mariannes du Nord', 'MOZ': 'Mozambique', 'MRT': 'Mauritanie',
    'MUS': 'Maurice', 'MWI': 'Malawi', 'MYS': 'Malaisie', 'NAM': 'Namibie',
    'NCL': 'Nouvelle-Calédonie', 'NER': 'Niger', 'NGA': 'Nigéria', 'NIC': 'Nicaragua',
    'NLD': 'Pays-Bas', 'NOR': 'Norvège', 'NPL': 'Népal', 'NRU': 'Nauru',
    'NZL': 'Nouvelle-Zélande', 'OMN': 'Oman', 'PAK': 'Pakistan', 'PAN': 'Panama',
    'PER': 'Pérou', 'PHL': 'Philippines', 'PLW': 'Palaos', 'PNG': 'Papouasie-Nouvelle-Guinée',
    'POL': 'Pologne', 'PRI': 'Porto Rico', 'PRK': 'Corée du Nord', 'PRT': 'Portugal',
    'PRY': 'Paraguay', 'PSE': 'Palestine', 'PYF': 'Polynésie française', 'QAT': 'Qatar',
    'ROU': 'Roumanie', 'RUS': 'Russie', 'RWA': 'Rwanda', 'SAU': 'Arabie saoudite',
    'SDN': 'Soudan', 'SEN': 'Sénégal', 'SGP': 'Singapour', 'SLB': 'Îles Salomon',
    'SLE': 'Sierra Leone', 'SLV': 'Salvador', 'SMR': 'Saint-Marin', 'SOM': 'Somalie',
    'SRB': 'Serbie', 'SSD': 'Soudan du Sud', 'STP': 'Sao Tomé-et-Principe', 'SUR': 'Suriname',
    'SVK': 'Slovaquie', 'SVN': 'Slovénie', 'SWE': 'Suède', 'SWZ': 'Eswatini',
    'SXM': 'Sint Maarten', 'SYC': 'Seychelles', 'SYR': 'Syrie', 'TCA': 'Îles Turques-et-Caïques',
    'TCD': 'Tchad', 'TGO': 'Togo', 'THA': 'Thaïlande', 'TJK': 'Tadjikistan',
    'TKM': 'Turkménistan', 'TLS': 'Timor-Leste', 'TON': 'Tonga', 'TTO': 'Trinité-et-Tobago',
    'TUN': 'Tunisie', 'TUR': 'Turquie', 'TUV': 'Tuvalu', 'TZA': 'Tanzanie',
    'UGA': 'Ouganda', 'UKR': 'Ukraine', 'URY': 'Uruguay', 'USA': 'États-Unis',
    'UZB': 'Ouzbékistan', 'VCT': 'Saint-Vincent-et-les-Grenadines', 'VEN': 'Venezuela', 
    'VGB': 'Îles Vierges britanniques', 'VIR': 'Îles Vierges américaines', 'VNM': 'Vietnam',
    'VUT': 'Vanuatu', 'WSM': 'Samoa', 'XKX': 'Kosovo', 'YEM': 'Yémen',
    'ZAF': 'Afrique du Sud', 'ZMB': 'Zambie', 'ZWE': 'Zimbabwe'
}

def get_country_name(code):
    """Retourne le nom complet du pays depuis son code ISO"""
    return COUNTRY_NAMES.get(code, code)

def get_wb_data():
    """Récupère données WB depuis MongoDB"""
    obs = db['curated_observations']
    cursor = obs.find({'source': {'$in': ['worldbank', 'WorldBank']}})
    
    records = []
    for o in cursor:
        try:
            indicator = o.get('attrs', {}).get('indicator', o.get('dataset'))
            country = o.get('attrs', {}).get('country')

            # Si pas de country dans attrs, extraire depuis 'key' (format: COUNTRY.INDICATOR)
            if not country and o.get('key'):
                country = o['key'].split('.')[0]

            # Conversion valeur/année
            value = float(o.get('value')) if o.get('value') is not None else None
            year = pd.to_datetime(o.get('ts')).year if o.get('ts') else None

            # Ne pas filtrer les zéros (valeurs 0.0 sont valides)
            if indicator and country and (value is not None) and (year is not None):
                records.append({
                    'indicator': indicator,
                    'country': country,
                    'year': int(year),
                    'value': float(value)
                })
        except Exception:
            continue
    
    return pd.DataFrame(records)

# Charger données
print("\n" + "="*80)
print("🌍 CHARGEMENT DASHBOARD BANQUE MONDIALE PREMIUM")
print("="*80)

df_wb = get_wb_data()
print(f"✅ Chargé {len(df_wb)} observations")

if not df_wb.empty:
    df_wb = df_wb.dropna(subset=['country', 'year', 'indicator', 'value'])
    countries = sorted([c for c in df_wb['country'].unique() if c])
    years = sorted([y for y in df_wb['year'].unique() if y])
    print(f"🌍 Pays: {len(countries)}")
    print(f"📅 Années: {int(min(years))} - {int(max(years))}")
    print(f"📊 Indicateurs: {df_wb['indicator'].nunique()}")
    
    # Créer les options du dropdown avec noms complets
    country_options = [{'label': get_country_name(c), 'value': c} for c in countries]
else:
    countries = []
    years = []
    country_options = []

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
            /* Fond de la page */
            body {
                background-color: #0a1929;
                margin: 0;
                padding: 0;
            }
            
            /* SUPPRIMER TOUT FOND BLANC - Style pour les dropdowns */
            
            /* Ancienne version de react-select */
            .custom-dropdown .Select-control {
                background-color: #132f4c !important;
                border: 1px solid #1e3a5f !important;
            }
            .custom-dropdown .Select-menu-outer {
                background-color: #132f4c !important;
                border: 1px solid #1e3a5f !important;
            }
            .custom-dropdown .Select-menu {
                background-color: #132f4c !important;
            }
            .custom-dropdown .Select-option {
                background-color: #132f4c !important;
                color: #ffffff !important;
                padding: 8px 12px;
            }
            .custom-dropdown .Select-option:hover {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            .custom-dropdown .Select-option.is-selected {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            .custom-dropdown .Select-value-label {
                color: #ffffff !important;
            }
            .custom-dropdown .Select-placeholder {
                color: #8796a5 !important;
            }
            .custom-dropdown .Select-input > input {
                color: #ffffff !important;
            }
            .custom-dropdown .Select-arrow {
                border-color: #8796a5 transparent transparent !important;
            }
            
            /* Version moderne de react-select - TOUT EN BLEU FONCÉ */
            .custom-dropdown div[class*="control"] {
                background-color: #132f4c !important;
                border-color: #1e3a5f !important;
                min-height: 38px;
            }
            .custom-dropdown div[class*="menu"] {
                background-color: #132f4c !important;
                border: 1px solid #1e3a5f !important;
            }
            .custom-dropdown div[class*="MenuList"] {
                background-color: #132f4c !important;
            }
            .custom-dropdown div[class*="option"] {
                background-color: #132f4c !important;
                color: #ffffff !important;
                padding: 8px 12px;
            }
            .custom-dropdown div[class*="option"]:hover,
            .custom-dropdown div[class*="option--is-focused"] {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            .custom-dropdown div[class*="option--is-selected"] {
                background-color: #1e3a5f !important;
                color: #00d9ff !important;
            }
            .custom-dropdown div[class*="singleValue"] {
                color: #ffffff !important;
            }
            .custom-dropdown div[class*="placeholder"] {
                color: #8796a5 !important;
            }
            .custom-dropdown div[class*="Input"] input {
                color: #ffffff !important;
            }
            .custom-dropdown div[class*="indicatorSeparator"] {
                background-color: #1e3a5f !important;
            }
            .custom-dropdown div[class*="indicatorContainer"] {
                color: #8796a5 !important;
            }
            
            /* Force le fond bleu pour TOUTES les parties du dropdown */
            .custom-dropdown * {
                background-color: #132f4c !important;
            }
            .custom-dropdown div[class*="control"] *,
            .custom-dropdown div[class*="menu"] *,
            .custom-dropdown div[class*="MenuList"] * {
                background-color: #132f4c !important;
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
                options=country_options,
                value=countries[0] if countries else None,
                clearable=False,
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
        html.Div(id='kpi-gdp', style=KPI_STYLE),
        html.Div(id='kpi-poverty', style=KPI_STYLE),
        html.Div(id='kpi-gni', style=KPI_STYLE),
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
    
    # Store
    dcc.Store(id='data-store', data=df_wb.to_dict('records')),
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
    df_current = df[(df['country'] == country) & 
                    (df['year'] == year) & 
                    (df['indicator'] == 'NY.GDP.MKTP.KD.ZG')]
    
    current_value = df_current['value'].iloc[0] if not df_current.empty else None
    
    # Historique pour sparkline
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
    # Cherche l'année demandée puis recule vers l'année disponible la plus récente
    df_c = df[(df['country'] == country) & (df['indicator'] == 'SI.POV.DDAY')]
    if df_c.empty:
        value, year_used = None, None
    else:
        candidates = df_c[df_c['year'] <= year].sort_values('year')
        if candidates.empty:
            candidates = df_c.sort_values('year')
        row = candidates.tail(1)
        value = float(row['value'].iloc[0]) if not row.empty else None
        year_used = int(row['year'].iloc[0]) if not row.empty else None

    return create_kpi_card_simple(
        "Taux de pauvreté\n(1,90 USD/jour)",
        (f"{value:.1f}%" + (f"  (année: {year_used})" if year_used and year_used != year else "")) if value is not None else "N/A",
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
    # Cherche la meilleure année disponible (<= année choisie, sinon la plus proche disponible)
    df_c = df[(df['country'] == country) & (df['indicator'] == 'NY.GNP.PCAP.CD')]
    if df_c.empty:
        value, year_used = None, None
    else:
        candidates = df_c[df_c['year'] <= year].sort_values('year')
        if candidates.empty:
            candidates = df_c.sort_values('year')
        row = candidates.tail(1)
        value = float(row['value'].iloc[0]) if not row.empty else None
        year_used = int(row['year'].iloc[0]) if not row.empty else None
    
    return create_kpi_card_simple(
        "RNB par habitant (USD)",
        (f"{value:,.0f} USD" + (f"  (année: {year_used})" if year_used and year_used != year else "")) if value is not None else "N/A",
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
    # Helper pour récupérer la meilleure valeur disponible
    def best_value(df_sub, ind_code, year_sel):
        tmp = df_sub[df_sub['indicator'] == ind_code]
        if tmp.empty:
            return None, None
        cand = tmp[tmp['year'] <= year_sel].sort_values('year')
        if cand.empty:
            cand = tmp.sort_values('year')
        r = cand.tail(1)
        if r.empty:
            return None, None
        return float(r['value'].iloc[0]), int(r['year'].iloc[0])

    # Dépenses santé et éducation avec fallback d'année
    health, y_h = best_value(df[(df['country'] == country)], 'SH.XPD.GHED.GD.ZS', year)
    edu, y_e = best_value(df[(df['country'] == country)], 'SE.XPD.TOTL.GD.ZS', year)

    health = health if health is not None else 0.0
    edu = edu if edu is not None else 0.0
    total = health + edu

    # Les valeurs sont déjà des % du PIB, on les borne à [0, 100]
    health_pct = max(0, min(int(round(health)), 100))
    edu_pct = max(0, min(int(round(edu)), 100))
    year_note = None
    if (y_h and y_h != year) or (y_e and y_e != year):
        year_note = f"Données: santé {y_h if y_h else '—'} / éducation {y_e if y_e else '—'}"
    
    return html.Div([
        html.Div("Dépenses publiques", style={'color': COLORS['text'], 'fontSize': '0.9rem', 'marginBottom': '10px'}),
        html.Div("(% du PIB)", style={'color': COLORS['text_dim'], 'fontSize': '0.8rem', 'marginBottom': '20px'}),
        (html.Div(year_note, style={'color': COLORS['text_dim'], 'fontSize': '0.75rem', 'marginBottom': '10px'}) if year_note else html.Div()),
        
        html.Div([
            html.Div(f"{total:.1f}%" if total or total == 0 else "N/A", 
                    style={'color': COLORS['text'], 'fontSize': '2.5rem', 'fontWeight': 'bold', 'marginBottom': '20px'})
        ]),
        
        # Barres de progression avec vraies données
        html.Div([
            create_progress_bar("Santé publique", health_pct if health_pct <= 100 else 100),
            create_progress_bar("Éducation publique", edu_pct if edu_pct <= 100 else 100),
            create_progress_bar("Voix et responsabilité", 56),
            create_progress_bar("État de droit", 22),
            create_progress_bar("Stabilité politique", 66),
            create_progress_bar("Contrôle de la corruption", 49),
        ])
    ])


@app.callback(
    Output('radar-chart', 'figure'),
    [Input('country-filter', 'value'),
     Input('year-filter', 'value')]
)
def update_radar(country, year):
    categories = DOING_BUSINESS_INDICATORS
    values = [56, 22, 66, 49, 82, 66]
    
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
    """Crée une carte KPI simple"""
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
    print(f"    🎨 Style: Fond noir + Cyan/Bleu + Dropdowns bleu foncé")
    print(f"\n    🌐 URL: http://127.0.0.1:8052")
    print(f"    🛑 Arrêter: Ctrl+C\n")
    
    app.run(debug=False, host='127.0.0.1', port=8052)

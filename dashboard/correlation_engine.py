# =====================
# Génération de recommandations trading (achat/vente)
# =====================
def generate_trading_recommendations(days: int = 7) -> list:
    """
    Génère des recommandations d'achat/vente pour les actions mentionnées dans les publications BRVM récentes.
    Critères simples :
      - Si publication corrélée ET variation positive récente => 'Acheter'
      - Si publication corrélée ET variation négative récente => 'Vendre'
      - Sinon => 'Surveiller'
    """
    from dashboard.push_service import send_push_to_all
    _, db = get_mongo_db()
    corr_results = correlate_publications_with_actions(days=days)
    recos = []
    for item in corr_results:
        if not item["actions"]:
            continue
        for symbol in item["actions"]:
            obs = list(db.curated_observations.find({
                "source": "BRVM",
                "dataset": "QUOTES",
                "key": symbol,
                "ts": {"$gte": (datetime.utcnow() - timedelta(days=days)).isoformat()}
            }).sort("ts", -1).limit(2))
            reco = "Surveiller"
            if len(obs) >= 2:
                delta = obs[0]["value"] - obs[1]["value"]
                if delta > 0:
                    reco = "Acheter"
                elif delta < 0:
                    reco = "Vendre"
            recos.append({
                "action": symbol,
                "publication": item["publication"],
                "date": item["date"],
                "url": item["url"],
                "recommandation": reco,
                "variation": obs[0]["value"] - obs[1]["value"] if len(obs) >= 2 else None
            })
            # Envoi automatique de notification push si recommandation forte
            if reco in ("Acheter", "Vendre"):
                title = f"Signal BRVM : {reco} {symbol}"
                body = f"{item['publication']}\nVariation : {obs[0]['value'] - obs[1]['value'] if len(obs) >= 2 else 'N/A'}"
                send_push_to_all(title, body, data={"symbol": symbol, "recommandation": reco})
    return recos
# =====================
# Corrélation Publications BRVM / Actions
# =====================
import re
from typing import List, Dict, Any

KEYWORDS_ACTIONS = [
    "dividende", "résultat", "augmentation de capital", "fusion", "acquisition", "bénéfice", "perte", "distribution", "assemblée générale", "nomination", "rachat", "introduction en bourse"
]

def extract_action_symbols(text: str, stock_symbols: List[str]) -> List[str]:
    """
    Extrait les symboles d'actions mentionnés dans un texte de publication.
    """
    found = []
    for symbol in stock_symbols:
        if re.search(rf"\\b{re.escape(symbol)}\\b", text, re.IGNORECASE):
            found.append(symbol)
    return found

def correlate_publications_with_actions(days: int = 7) -> List[Dict[str, Any]]:
    """
    Analyse les publications BRVM récentes et tente de les corréler avec les actions cotées.
    Retourne une liste de dicts : publication, actions concernées, score de corrélation.
    """
    _, db = get_mongo_db()
    # Récupérer les publications récentes
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    pubs = list(db.curated_observations.find({
        "source": "BRVM_PUBLICATION",
        "dataset": "PUBLICATION",
        "ts": {"$gte": since}
    }))
    # Récupérer la liste des symboles d'actions
    stocks = list(db.curated_observations.find({"source": "BRVM", "dataset": "QUOTES"}).distinct("key"))
    results = []
    for pub in pubs:
        text = pub["key"] + " " + pub["attrs"].get("url", "")
        actions = extract_action_symbols(text, stocks)
        score = 0
        if actions:
            score += 1
        for kw in KEYWORDS_ACTIONS:
            if re.search(kw, text, re.IGNORECASE):
                score += 1
        results.append({
            "publication": pub["key"],
            "date": pub["ts"],
            "url": pub["attrs"].get("url"),
            "actions": actions,
            "correlation_score": score
        })
    return results
"""
Moteur d'analyse de corrélations entre pays et indicateurs
Détecte risques de contagion et dépendances économiques
"""

from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db
import numpy as np
import pandas as pd
from scipy.stats import pearsonr


class CorrelationEngine:
    """Analyse corrélations cross-country et contagion"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
    
    def calculate_country_correlation_matrix(self, countries, indicator, years=5):
        """
        Calcule matrice de corrélation entre pays pour un indicateur
        
        Args:
            countries: Liste codes ISO3
            indicator: Code indicateur (NY.GDP.MKTP.KD.ZG, etc.)
            years: Période historique
        
        Returns:
            Dict avec matrice corrélation + p-values
        """
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Récupérer données pour chaque pays
        country_data = {}
        
        for country in countries:
            docs = list(self.db.curated_observations.find(
                {
                    'dataset': indicator,
                    'key': {'$regex': f'^{country}'},
                    'ts': {'$gte': threshold}
                },
                sort=[('ts', 1)]
            ))
            
            if docs:
                country_data[country] = {
                    'dates': [d['ts'] for d in docs],
                    'values': [d['value'] for d in docs]
                }
        
        if len(country_data) < 2:
            return {'error': 'Insufficient data for correlation analysis'}
        
        # Construire DataFrame aligné sur dates communes
        df = self._align_time_series(country_data)
        
        if df.empty:
            return {'error': 'No common dates found'}
        
        # Calculer corrélations
        corr_matrix = df.corr().to_dict()
        
        # Calculer p-values
        p_values = {}
        for country1 in df.columns:
            p_values[country1] = {}
            for country2 in df.columns:
                if country1 != country2:
                    _, p_value = pearsonr(df[country1].dropna(), df[country2].dropna())
                    p_values[country1][country2] = round(p_value, 4)
                else:
                    p_values[country1][country2] = 0.0
        
        # Identifier paires fortement corrélées
        strong_correlations = []
        for country1 in corr_matrix:
            for country2 in corr_matrix[country1]:
                if country1 < country2:  # Éviter doublons
                    corr = corr_matrix[country1][country2]
                    if abs(corr) > 0.7:  # Seuil forte corrélation
                        strong_correlations.append({
                            'country1': country1,
                            'country2': country2,
                            'correlation': round(corr, 3),
                            'p_value': p_values[country1][country2],
                            'strength': 'very strong' if abs(corr) > 0.9 else 'strong'
                        })
        
        # Trier par corrélation absolue décroissante
        strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'indicator': indicator,
            'countries': countries,
            'period_years': years,
            'correlation_matrix': corr_matrix,
            'p_values': p_values,
            'strong_correlations': strong_correlations,
            'data_points': len(df),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_contagion_risk(self, source_country, indicator, target_countries=None, years=5):
        """
        Analyse risque de contagion d'un pays vers autres
        
        Args:
            source_country: Pays source crise
            indicator: Indicateur à analyser
            target_countries: Pays cibles (si None, tous CEDEAO)
            years: Période historique
        
        Returns:
            Dict avec scores risque contagion
        """
        if target_countries is None:
            target_countries = ['SEN', 'CIV', 'BEN', 'BFA', 'MLI', 'NER', 'TGO', 'GHA', 'NGA']
        
        # Retirer pays source
        target_countries = [c for c in target_countries if c != source_country]
        
        # Calculer corrélations avec pays source
        all_countries = [source_country] + target_countries
        corr_analysis = self.calculate_country_correlation_matrix(
            all_countries, indicator, years
        )
        
        if 'error' in corr_analysis:
            return corr_analysis
        
        # Extraire corrélations avec pays source
        contagion_risks = []
        corr_matrix = corr_analysis['correlation_matrix']
        p_values = corr_analysis['p_values']
        
        for target in target_countries:
            if target in corr_matrix.get(source_country, {}):
                corr = corr_matrix[source_country][target]
                p_val = p_values[source_country][target]
                
                # Calculer score risque 0-100
                risk_score = abs(corr) * 100
                
                # Classification risque
                if risk_score > 80:
                    risk_level = 'critical'
                elif risk_score > 60:
                    risk_level = 'high'
                elif risk_score > 40:
                    risk_level = 'moderate'
                else:
                    risk_level = 'low'
                
                contagion_risks.append({
                    'target_country': target,
                    'correlation': round(corr, 3),
                    'p_value': p_val,
                    'risk_score': round(risk_score, 1),
                    'risk_level': risk_level,
                    'significant': p_val < 0.05
                })
        
        # Trier par risque décroissant
        contagion_risks.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            'source_country': source_country,
            'indicator': indicator,
            'contagion_analysis': contagion_risks,
            'highest_risk': contagion_risks[0] if contagion_risks else None,
            'countries_at_risk': [
                c['target_country'] for c in contagion_risks 
                if c['risk_level'] in ['high', 'critical']
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def cross_indicator_correlation(self, country, indicators, years=5):
        """
        Analyse corrélations entre indicateurs pour un pays
        
        Args:
            country: Code ISO3
            indicators: Liste codes indicateurs
            years: Période
        
        Returns:
            Dict avec matrice corrélations indicateurs
        """
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Récupérer données pour chaque indicateur
        indicator_data = {}
        
        for indicator in indicators:
            docs = list(self.db.curated_observations.find(
                {
                    'dataset': indicator,
                    'key': {'$regex': f'^{country}'},
                    'ts': {'$gte': threshold}
                },
                sort=[('ts', 1)]
            ))
            
            if docs:
                indicator_data[indicator] = {
                    'dates': [d['ts'] for d in docs],
                    'values': [d['value'] for d in docs]
                }
        
        if len(indicator_data) < 2:
            return {'error': 'Need at least 2 indicators with data'}
        
        # Aligner séries temporelles
        df = self._align_time_series(indicator_data)
        
        if df.empty:
            return {'error': 'No common dates'}
        
        # Calculer corrélations
        corr_matrix = df.corr().to_dict()
        
        # Identifier relations fortes
        relationships = []
        for ind1 in corr_matrix:
            for ind2 in corr_matrix[ind1]:
                if ind1 < ind2:
                    corr = corr_matrix[ind1][ind2]
                    if abs(corr) > 0.5:
                        relationships.append({
                            'indicator1': ind1,
                            'indicator2': ind2,
                            'correlation': round(corr, 3),
                            'relationship': self._interpret_correlation(corr)
                        })
        
        relationships.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'country': country,
            'indicators': indicators,
            'correlation_matrix': corr_matrix,
            'strong_relationships': relationships,
            'timestamp': datetime.now().isoformat()
        }
    
    def time_lagged_correlation(self, country1, country2, indicator, max_lag_months=12, years=5):
        """
        Analyse corrélations avec décalages temporels (leads/lags)
        Détecte si pays1 prédit pays2 avec délai
        
        Args:
            country1: Pays leader potentiel
            country2: Pays follower potentiel
            indicator: Indicateur
            max_lag_months: Décalage max à tester
            years: Période
        
        Returns:
            Dict avec meilleur lag et corrélations
        """
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Récupérer données
        data1 = list(self.db.curated_observations.find(
            {'dataset': indicator, 'key': {'$regex': f'^{country1}'}, 'ts': {'$gte': threshold}},
            sort=[('ts', 1)]
        ))
        
        data2 = list(self.db.curated_observations.find(
            {'dataset': indicator, 'key': {'$regex': f'^{country2}'}, 'ts': {'$gte': threshold}},
            sort=[('ts', 1)]
        ))
        
        if not data1 or not data2:
            return {'error': 'Insufficient data'}
        
        # Convertir en séries pandas
        df1 = pd.DataFrame(data1)[['ts', 'value']].rename(columns={'value': country1})
        df2 = pd.DataFrame(data2)[['ts', 'value']].rename(columns={'value': country2})
        
        df1['ts'] = pd.to_datetime(df1['ts'])
        df2['ts'] = pd.to_datetime(df2['ts'])
        
        df1.set_index('ts', inplace=True)
        df2.set_index('ts', inplace=True)
        
        # Aligner sur fréquence commune (mensuelle)
        df1 = df1.resample('M').mean()
        df2 = df2.resample('M').mean()
        
        # Tester différents lags
        lag_results = []
        
        for lag in range(-max_lag_months, max_lag_months + 1):
            if lag == 0:
                series1 = df1[country1].dropna()
                series2 = df2[country2].dropna()
            elif lag > 0:
                # country1 lead de country2 par lag mois
                series1 = df1[country1].shift(-lag).dropna()
                series2 = df2[country2].dropna()
            else:
                # country2 lead de country1
                series1 = df1[country1].dropna()
                series2 = df2[country2].shift(lag).dropna()
            
            # Aligner indices
            common_idx = series1.index.intersection(series2.index)
            if len(common_idx) > 10:
                corr, p_val = pearsonr(series1[common_idx], series2[common_idx])
                lag_results.append({
                    'lag_months': lag,
                    'correlation': round(corr, 3),
                    'p_value': round(p_val, 4),
                    'data_points': len(common_idx)
                })
        
        # Trouver meilleur lag (max corrélation absolue)
        if lag_results:
            best_lag = max(lag_results, key=lambda x: abs(x['correlation']))
            
            return {
                'country1': country1,
                'country2': country2,
                'indicator': indicator,
                'best_lag': best_lag,
                'all_lags': lag_results,
                'interpretation': self._interpret_lag(best_lag, country1, country2),
                'timestamp': datetime.now().isoformat()
            }
        
        return {'error': 'Could not compute lagged correlations'}
    
    def _align_time_series(self, country_data):
        """Aligne séries temporelles sur dates communes"""
        dataframes = []
        
        for country, data in country_data.items():
            df = pd.DataFrame({
                'date': pd.to_datetime(data['dates']),
                country: data['values']
            })
            df.set_index('date', inplace=True)
            dataframes.append(df)
        
        # Merge sur dates communes
        result = dataframes[0]
        for df in dataframes[1:]:
            result = result.join(df, how='inner')
        
        return result
    
    def _interpret_correlation(self, corr):
        """Interprétation textuelle corrélation"""
        if corr > 0.7:
            return "Forte corrélation positive"
        elif corr > 0.3:
            return "Corrélation positive modérée"
        elif corr > -0.3:
            return "Faible ou pas de corrélation"
        elif corr > -0.7:
            return "Corrélation négative modérée"
        else:
            return "Forte corrélation négative"
    
    def _interpret_lag(self, best_lag, country1, country2):
        """Interprétation décalage temporel"""
        lag = best_lag['lag_months']
        corr = best_lag['correlation']
        
        if abs(corr) < 0.3:
            return f"Pas de relation temporelle claire entre {country1} et {country2}"
        
        if lag > 0:
            return f"{country1} précède {country2} de {lag} mois (corrélation {corr:.2f})"
        elif lag < 0:
            return f"{country2} précède {country1} de {abs(lag)} mois (corrélation {corr:.2f})"
        else:
            return f"{country1} et {country2} évoluent simultanément (corrélation {corr:.2f})"


# Singleton
correlation_engine = CorrelationEngine()

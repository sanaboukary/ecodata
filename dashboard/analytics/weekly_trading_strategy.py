#!/usr/bin/env python3
"""
📈 STRATÉGIE TRADING HEBDOMADAIRE - BRVM
Objectif : 50-80% rendement/semaine avec 85-95% précision
Analyse quotidienne pour recommandations court terme
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class WeeklyTradingStrategy:
    """
    Stratégie de trading orientée résultats hebdomadaires
    
    Critères :
    - Momentum fort (5-10 jours)
    - Volume exceptionnel (3x+ moyenne)
    - Catalyseurs imminents (AG, résultats, dividendes)
    - Sentiment positif publications
    - Support/résistance techniques
    """
    
    def __init__(self):
        self.target_return = 0.65  # 65% rendement cible
        self.min_confidence = 0.85  # 85% confiance minimum
        self.max_positions = 5     # 5 positions max simultanées
        self.holding_period = 5    # 5 jours ouvrables (1 semaine)
    
    def analyser_potentiel_hebdomadaire(
        self,
        prix_historique: List[float],
        volumes: List[float],
        publications_recentes: List[Dict],
        evenements_futurs: List[Dict],
        indicateurs_techniques: Dict
    ) -> Dict:
        """
        Analyse potentiel de gain sur 5 jours
        
        Returns:
            {
                'score': 0-100,
                'potentiel_gain': 0.0-1.0 (% rendement estimé),
                'confiance': 0.0-1.0,
                'horizon': 'court_terme',  # < 7 jours
                'catalyseurs': [...],
                'risques': [...]
            }
        """
        
        score_total = 0
        catalyseurs = []
        risques = []
        
        # 1. MOMENTUM COURT TERME (30 points)
        score_momentum, cat_mom, risq_mom = self._evaluer_momentum_court_terme(
            prix_historique, volumes
        )
        score_total += score_momentum
        catalyseurs.extend(cat_mom)
        risques.extend(risq_mom)
        
        # 2. CATALYSEURS IMMINENTS (25 points)
        score_catalyseurs, cats = self._detecter_catalyseurs_imminents(
            evenements_futurs, publications_recentes
        )
        score_total += score_catalyseurs
        catalyseurs.extend(cats)
        
        # 3. SENTIMENT PUBLICATIONS (20 points)
        score_sentiment, cat_sent = self._analyser_sentiment_publications(
            publications_recentes
        )
        score_total += score_sentiment
        catalyseurs.extend(cat_sent)
        
        # 4. BREAKOUT TECHNIQUE (15 points)
        score_breakout, cat_break = self._detecter_breakout_imminent(
            prix_historique, indicateurs_techniques
        )
        score_total += score_breakout
        catalyseurs.extend(cat_break)
        
        # 5. VOLUME EXCEPTIONNEL (10 points)
        score_volume, cat_vol = self._evaluer_volume_anormal(volumes)
        score_total += score_volume
        catalyseurs.extend(cat_vol)
        
        # Calculer potentiel gain
        potentiel_gain = self._estimer_potentiel_gain(
            score_total, prix_historique, indicateurs_techniques
        )
        
        # Confiance basée sur convergence signaux
        confiance = self._calculer_confiance(
            score_total, len(catalyseurs), len(risques)
        )
        
        return {
            'score': min(score_total, 100),
            'potentiel_gain': potentiel_gain,
            'confiance': confiance,
            'horizon': 'court_terme',
            'jours_holding': self.holding_period,
            'catalyseurs': catalyseurs,
            'risques': risques,
            'recommendation': self._generer_recommendation(
                score_total, potentiel_gain, confiance
            )
        }
    
    def _evaluer_momentum_court_terme(
        self, prix: List[float], volumes: List[float]
    ) -> Tuple[float, List[str], List[str]]:
        """Évalue momentum sur 5-10 derniers jours"""
        
        if len(prix) < 10:
            return 0, [], ["Historique insuffisant"]
        
        score = 0
        catalyseurs = []
        risques = []
        
        # Performance 5 jours
        perf_5j = (prix[-1] - prix[-5]) / prix[-5] * 100
        
        # Performance 10 jours
        perf_10j = (prix[-1] - prix[-10]) / prix[-10] * 100
        
        # Accélération (5j > 10j = momentum croissant)
        if perf_5j > perf_10j:
            score += 15
            catalyseurs.append(f"🚀 Accélération momentum: {perf_5j:.1f}% (5j) > {perf_10j:.1f}% (10j)")
        
        # Performance absolue forte
        if perf_5j > 10:
            score += 10
            catalyseurs.append(f"📈 Forte hausse 5j: +{perf_5j:.1f}%")
        elif perf_5j > 5:
            score += 5
            catalyseurs.append(f"📊 Hausse modérée 5j: +{perf_5j:.1f}%")
        elif perf_5j < -5:
            risques.append(f"📉 Baisse récente 5j: {perf_5j:.1f}%")
        
        # Tendance volume
        vol_recent = np.mean(volumes[-5:])
        vol_ancien = np.mean(volumes[-10:-5])
        
        if vol_recent > vol_ancien * 1.5:
            score += 5
            catalyseurs.append(f"📊 Volume croissant: +{(vol_recent/vol_ancien-1)*100:.0f}%")
        
        return score, catalyseurs, risques
    
    def _detecter_catalyseurs_imminents(
        self, evenements: List[Dict], publications: List[Dict]
    ) -> Tuple[float, List[str]]:
        """Détecte événements à venir < 7 jours"""
        
        score = 0
        catalyseurs = []
        today = datetime.now()
        
        for event in evenements:
            date_event = datetime.fromisoformat(event.get('date', '2099-01-01'))
            jours_restants = (date_event - today).days
            
            if 0 <= jours_restants <= 7:
                type_event = event.get('type', '')
                
                if type_event == 'AG':
                    score += 10
                    catalyseurs.append(f"🏛️ AG dans {jours_restants}j - Potentiel dividende/restructuration")
                
                elif type_event == 'RESULTATS':
                    score += 15
                    catalyseurs.append(f"📊 Publication résultats dans {jours_restants}j")
                
                elif type_event == 'DIVIDENDE':
                    score += 12
                    catalyseurs.append(f"💰 Versement dividende dans {jours_restants}j")
        
        # Publications récentes positives
        for pub in publications[-5:]:  # 5 dernières
            if pub.get('sentiment', 0) > 0.5:
                score += 3
                catalyseurs.append(f"📰 {pub.get('titre', '')[:50]}... (sentiment positif)")
        
        return min(score, 25), catalyseurs
    
    def _analyser_sentiment_publications(
        self, publications: List[Dict]
    ) -> Tuple[float, List[str]]:
        """Analyse sentiment des publications récentes"""
        
        if not publications:
            return 0, []
        
        score = 0
        catalyseurs = []
        
        sentiments = [p.get('sentiment_score', 0) for p in publications[-10:]]
        sentiment_moyen = np.mean(sentiments) if sentiments else 0
        
        # Mots-clés positifs
        mots_positifs = [
            'croissance', 'hausse', 'progression', 'record',
            'expansion', 'investissement', 'acquisition',
            'dividende exceptionnel', 'bénéfice', 'chiffre d\'affaires'
        ]
        
        for pub in publications[-5:]:
            titre = pub.get('titre', '').lower()
            
            for mot in mots_positifs:
                if mot in titre:
                    score += 2
                    catalyseurs.append(f"✅ Publication positive: {mot}")
        
        # Sentiment global
        if sentiment_moyen > 0.7:
            score += 10
            catalyseurs.append(f"😊 Sentiment très positif (score: {sentiment_moyen:.2f})")
        elif sentiment_moyen > 0.5:
            score += 5
            catalyseurs.append(f"🙂 Sentiment positif (score: {sentiment_moyen:.2f})")
        
        return min(score, 20), catalyseurs
    
    def _detecter_breakout_imminent(
        self, prix: List[float], indicateurs: Dict
    ) -> Tuple[float, List[str]]:
        """Détecte rupture technique imminente"""
        
        score = 0
        catalyseurs = []
        
        prix_actuel = prix[-1]
        
        # Proche résistance
        resistance = indicateurs.get('resistance', float('inf'))
        distance_resistance = abs(prix_actuel - resistance) / prix_actuel
        
        if distance_resistance < 0.02:  # < 2%
            score += 8
            catalyseurs.append(f"🎯 Proche résistance ({resistance:.0f} FCFA) - Breakout imminent")
        
        # RSI proche 70 (surachat imminent)
        rsi = indicateurs.get('rsi', 50)
        if 65 < rsi < 75:
            score += 5
            catalyseurs.append(f"📈 RSI momentum: {rsi:.1f} (zone achat)")
        
        # MACD croisement haussier récent
        if indicateurs.get('macd_signal', '') == 'BULLISH_CROSS':
            score += 7
            catalyseurs.append("🔼 MACD croisement haussier récent")
        
        return min(score, 15), catalyseurs
    
    def _evaluer_volume_anormal(self, volumes: List[float]) -> Tuple[float, List[str]]:
        """Détecte pic de volume = intérêt institutionnel"""
        
        if len(volumes) < 20:
            return 0, []
        
        vol_recent = volumes[-1]
        vol_moyen_20j = np.mean(volumes[-20:])
        
        ratio = vol_recent / vol_moyen_20j if vol_moyen_20j > 0 else 0
        
        catalyseurs = []
        score = 0
        
        if ratio > 5:
            score = 10
            catalyseurs.append(f"🔥 Volume EXCEPTIONNEL: {ratio:.1f}x moyenne")
        elif ratio > 3:
            score = 7
            catalyseurs.append(f"📊 Volume très élevé: {ratio:.1f}x moyenne")
        elif ratio > 2:
            score = 4
            catalyseurs.append(f"📈 Volume élevé: {ratio:.1f}x moyenne")
        
        return score, catalyseurs
    
    def _estimer_potentiel_gain(
        self, score: float, prix: List[float], indicateurs: Dict
    ) -> float:
        """Estime potentiel de gain sur 5 jours"""
        
        # Base : score/100
        potentiel_base = score / 100
        
        # Ajustement volatilité
        volatilite = indicateurs.get('volatility', 0.05)
        
        # Ajustement distance résistance
        resistance = indicateurs.get('resistance', prix[-1] * 1.2)
        distance_resistance = (resistance - prix[-1]) / prix[-1]
        
        # Formule : base × (1 + volatilité) × min(distance_resistance, 0.5)
        potentiel = potentiel_base * (1 + volatilite) * min(distance_resistance, 0.5)
        
        # Cap à 80% (objectif max)
        return min(potentiel, 0.80)
    
    def _calculer_confiance(
        self, score: float, nb_catalyseurs: int, nb_risques: int
    ) -> float:
        """Calcule niveau de confiance"""
        
        # Base : score/100
        confiance = score / 100
        
        # Bonus catalyseurs multiples
        if nb_catalyseurs >= 5:
            confiance *= 1.1
        elif nb_catalyseurs >= 3:
            confiance *= 1.05
        
        # Pénalité risques
        if nb_risques >= 3:
            confiance *= 0.9
        elif nb_risques >= 2:
            confiance *= 0.95
        
        # Cap 95%
        return min(confiance, 0.95)
    
    def _generer_recommendation(
        self, score: float, potentiel: float, confiance: float
    ) -> str:
        """Génère recommendation claire"""
        
        if score >= 70 and confiance >= 0.85 and potentiel >= 0.30:
            return 'ACHAT FORT'
        elif score >= 60 and confiance >= 0.75 and potentiel >= 0.20:
            return 'ACHAT'
        elif score >= 50:
            return 'SURVEILLER'
        else:
            return 'NEUTRE'
    
    def filtrer_top_opportunites(
        self, analyses: List[Dict], max_count: int = 5
    ) -> List[Dict]:
        """
        Filtre top opportunités hebdomadaires
        
        Critères :
        - Confiance >= 85%
        - Potentiel >= 30%
        - Score >= 65
        """
        
        # Filtrer
        opportunites = [
            a for a in analyses
            if a['confiance'] >= 0.85
            and a['potentiel_gain'] >= 0.30
            and a['score'] >= 65
        ]
        
        # Trier par potentiel × confiance
        opportunites.sort(
            key=lambda x: x['potentiel_gain'] * x['confiance'],
            reverse=True
        )
        
        return opportunites[:max_count]

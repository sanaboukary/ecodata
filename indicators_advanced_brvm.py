#!/usr/bin/env python3
"""
INDICATEURS AVANCÉS BRVM – EXPERT 30 ANS
========================================
Algorithmes professionnels calibrés pour le marché BRVM
- Volume Z-Score (anomalies statistiques)
- Momentum Accéléré (accélération de tendance)
- Breakout Detector (compression → rupture)
- EMA (réactivité court terme)
- Probabilité TOP 5 (fréquence historique)
- Régime Inter-Marché (BRVM Composite)
"""

import numpy as np
import statistics
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class IndicatorsAdvancedBRVM:
    """Suite complète d'indicateurs avancés calibrés BRVM"""
    
    @staticmethod
    def volume_zscore(volumes: List[float], n: int = 8) -> Optional[float]:
        """
        Z-SCORE VOLUME (détection anomalies statistiques)
        
        Formule: Z = (volume_actuel - moyenne_8w) / écart_type
        
        Interprétation BRVM:
        - Z > 2.0 : Volume TRÈS anormal (actualité forte)
        - Z > 1.5 : Volume anormal (intérêt inhabituel)
        - 0.5 < Z < 1.5 : Volume légèrement élevé
        - -0.5 < Z < 0.5 : Volume normal
        - Z < -0.5 : Volume faible (éviter)
        
        SUPÉRIEUR au simple ratio car mesure la significativité statistique
        """
        if not volumes or len(volumes) < n + 1:
            return None
        
        current_volume = volumes[-1]
        historical_volumes = volumes[-n-1:-1]  # 8 dernières semaines (exclu actuelle)
        
        # Filtre volumes = 0 (BRVM low liquidity)
        valid_volumes = [v for v in historical_volumes if v > 0]
        
        if len(valid_volumes) < max(3, n // 2):  # Minimum 3-4 semaines valides
            return None
        
        mean_vol = statistics.mean(valid_volumes)
        
        # Protection division par zéro
        if mean_vol == 0:
            return None
        
        # Écart-type (utilise stdev si >1 valeur, sinon fallback)
        if len(valid_volumes) > 1:
            std_vol = statistics.stdev(valid_volumes)
        else:
            std_vol = mean_vol * 0.3  # Fallback: 30% du mean
        
        # Protection std = 0 (marché ultra-stable)
        if std_vol == 0:
            std_vol = mean_vol * 0.1
        
        z_score = (current_volume - mean_vol) / std_vol
        
        return round(z_score, 2)
    
    @staticmethod
    def momentum_accelere(prix: List[float], n: int = 3) -> Optional[float]:
        """
        MOMENTUM ACCÉLÉRÉ (détection accélération de tendance)
        
        Formule: Accel = Var%(w0) - Var%(w-1)
        
        Interprétation BRVM:
        - Accel > 3% : Accélération haussière FORTE (explosion en cours)
        - Accel > 1% : Accélération haussière
        - -1% < Accel < 1% : Stable (pas d'accélération)
        - Accel < -1% : Décélération (perte de momentum)
        - Accel < -3% : Décélération forte (retournement probable)
        
        Détecte les variations de 2e ordre (vitesse de la vitesse)
        """
        if not prix or len(prix) < n + 2:
            return None
        
        # Variation% semaine actuelle (w0)
        var_w0 = ((prix[-1] - prix[-2]) / prix[-2] * 100) if prix[-2] > 0 else 0
        
        # Variation% semaine précédente (w-1)
        var_w1 = ((prix[-2] - prix[-3]) / prix[-3] * 100) if prix[-3] > 0 else 0
        
        # Accélération = différence des variations
        acceleration = var_w0 - var_w1
        
        return round(acceleration, 2)
    
    @staticmethod
    def breakout_detector(
        prix: List[float], 
        volumes: List[float], 
        atr_history: List[float],
        lookback: int = 3
    ) -> Dict:
        """
        BREAKOUT DETECTOR (compression → rupture)
        
        Phase 1 - COMPRESSION détectée si:
        - ATR < ATR_moyen (volatilité contracte)
        - Range 3 semaines serré (< 5%)
        
        Phase 2 - RUPTURE détectée si:
        - Close > Max(3 dernières semaines)
        - Volume ≥ 1.8 × moyenne
        
        Retour: {"compression": bool, "rupture": bool, "score": 0-100}
        """
        if not prix or len(prix) < lookback + 2:
            return {"compression": False, "rupture": False, "score": 0}
        
        result = {
            "compression": False,
            "rupture": False,
            "score": 0,
            "details": []
        }
        
        # === PHASE 1: COMPRESSION ===
        
        # ATR actuel vs ATR moyen
        if atr_history and len(atr_history) >= lookback + 1:
            atr_actuel = atr_history[-1]
            atr_moyen = statistics.mean(atr_history[-lookback-1:-1])
            
            if atr_actuel < atr_moyen * 0.85:  # ATR < 85% moyenne
                result["compression"] = True
                result["details"].append(f"ATR contracté ({atr_actuel:.1f}% < {atr_moyen:.1f}%)")
        
        # Range 3 semaines serré
        recent_prices = prix[-lookback-1:-1]
        if recent_prices:
            price_range = (max(recent_prices) - min(recent_prices)) / min(recent_prices) * 100
            if price_range < 5:  # Range < 5%
                result["compression"] = True
                result["details"].append(f"Range serré ({price_range:.1f}%)")
        
        # === PHASE 2: RUPTURE ===
        
        current_close = prix[-1]
        max_recent = max(prix[-lookback-1:-1]) if len(prix) >= lookback + 1 else current_close
        
        # Prix dépasse le max récent
        rupture_prix = current_close > max_recent * 1.01  # +1% au-dessus max
        
        # Volume anormal
        rupture_volume = False
        if volumes and len(volumes) >= lookback + 1:
            vol_actuel = volumes[-1]
            vol_moyen = statistics.mean([v for v in volumes[-lookback-1:-1] if v > 0])
            if vol_moyen > 0 and vol_actuel >= vol_moyen * 1.8:
                rupture_volume = True
                result["details"].append(f"Volume explosif ({vol_actuel/vol_moyen:.1f}x)")
        
        if rupture_prix and rupture_volume:
            result["rupture"] = True
            result["details"].append(f"Breakout confirmé (prix > max {lookback}w)")
        
        # === SCORE GLOBAL ===
        score = 0
        if result["compression"]:
            score += 40
        if result["rupture"]:
            score += 60
        
        result["score"] = score
        
        return result
    
    @staticmethod
    def ema(prix: List[float], n: int) -> Optional[float]:
        """
        EMA (Exponential Moving Average) - Réactivité court terme
        
        Formule: EMA = Prix × k + EMA_prev × (1-k)
        où k = 2 / (n+1)
        
        Avantage sur SMA: Pondère davantage les valeurs récentes
        Utilisation BRVM: EMA5, EMA10 pour EXPLOSION_7J (réactivité)
        """
        if not prix or len(prix) < n:
            return None
        
        k = 2 / (n + 1)
        ema = prix[0]
        
        for p in prix[1:]:
            ema = p * k + ema * (1 - k)
        
        return round(ema, 2)
    
    @staticmethod
    def probabilite_top5_historique(
        db,
        symbol: str,
        lookback_weeks: int = 26
    ) -> Dict:
        """
        PROBABILITÉ TOP 5 (fréquence historique d'apparition)
        
        Analyse: Sur les N dernières semaines, combien de fois l'action
        est apparue dans le TOP 5 des hausses hebdomadaires ?
        
        Formule: Proba = Nb_apparitions / Nb_semaines_observées
        
        Interprétation BRVM:
        - Proba > 20% : Action régulièrement performante (TOP 5 fréquent)
        - Proba 10-20% : Performances occasionnelles
        - Proba < 10% : Rarement dans le TOP 5
        
        Utilité: Pondération dans EXPLOSION_SCORE (actions habituées à performer)
        """
        from datetime import datetime, timedelta
        
        # Calcul date début lookback
        date_debut = datetime.now() - timedelta(weeks=lookback_weeks)
        
        # Récupération historique prix hebdo
        prices_weekly = list(db.prices_weekly.find({
            "symbol": symbol,
            "week": {"$gte": date_debut.strftime("%Y-W%W")}
        }).sort("week", 1))
        
        if len(prices_weekly) < 4:  # Minimum 4 semaines
            return {
                "probabilite": 0,
                "apparitions": 0,
                "semaines_observees": 0,
                "fiable": False
            }
        
        # Pour chaque semaine, vérifier si dans TOP 5 gains
        apparitions_top5 = 0
        semaines_valides = 0
        
        for i in range(1, len(prices_weekly)):
            week_data = prices_weekly[i]
            prev_week = prices_weekly[i-1]
            
            close_actuel = week_data.get("close")
            close_prev = prev_week.get("close")
            
            if not close_actuel or not close_prev or close_prev <= 0:
                continue
            
            # Calcul variation%
            variation_pct = ((close_actuel - close_prev) / close_prev) * 100
            week_id = week_data.get("week")
            
            # Comparer avec toutes les autres actions cette semaine
            all_actions_this_week = list(db.prices_weekly.find({
                "week": week_id
            }))
            
            # Calcul variations de toutes les actions
            variations = []
            for action in all_actions_this_week:
                sym = action.get("symbol")
                if sym == symbol:
                    continue
                
                # Récupérer prix semaine précédente
                prev_action = db.prices_weekly.find_one({
                    "symbol": sym,
                    "week": prev_week.get("week")
                })
                
                if prev_action:
                    c_act = action.get("close")
                    c_prev = prev_action.get("close")
                    if c_act and c_prev and c_prev > 0:
                        var = ((c_act - c_prev) / c_prev) * 100
                        variations.append(var)
            
            # Ajouter variation de notre action
            variations.append(variation_pct)
            variations.sort(reverse=True)
            
            # Vérifier si dans TOP 5
            if variation_pct in variations[:5]:
                apparitions_top5 += 1
            
            semaines_valides += 1
        
        # Calcul probabilité
        probabilite = (apparitions_top5 / semaines_valides * 100) if semaines_valides > 0 else 0
        
        return {
            "probabilite": round(probabilite, 1),
            "apparitions": apparitions_top5,
            "semaines_observees": semaines_valides,
            "fiable": semaines_valides >= 8  # Minimum 8 semaines pour fiabilité
        }
    
    @staticmethod
    def regime_inter_marche(db, current_week: str = None) -> Dict:
        """
        RÉGIME INTER-MARCHÉ (analyse BRVM Composite)
        
        Analyse le régime de marché global via l'indice BRVM Composite:
        - BULL: Composite en hausse, SMA5 > SMA10 → Multiplier EXPLOSION_SCORE × 1.1
        - BEAR: Composite en baisse, SMA5 < SMA10 → Multiplier EXPLOSION_SCORE × 0.85
        - NEUTRAL: Indécis → Multiplier × 1.0
        
        Logique: En marché haussier, les explosions ont plus de chance de réussir.
        En marché baissier, être plus sélectif (pénalité).
        """
        if current_week is None:
            current_week = datetime.now().strftime("%Y-W%W")
        
        # Récupération historique BRVM Composite
        composite_data = list(db.prices_weekly.find({
            "symbol": "BRVM-COMPOSITE"
        }).sort("week", 1).limit(20))
        
        if len(composite_data) < 10:
            return {
                "regime": "NEUTRAL",
                "multiplier": 1.0,
                "details": "Données insuffisantes pour déterminer régime"
            }
        
        # SMA5 et SMA10 du Composite
        prix_composite = [d.get("close") for d in composite_data if d.get("close")]
        
        if len(prix_composite) < 10:
            return {
                "regime": "NEUTRAL",
                "multiplier": 1.0,
                "details": "Données insuffisantes"
            }
        
        sma5 = statistics.mean(prix_composite[-5:])
        sma10 = statistics.mean(prix_composite[-10:])
        
        # Variation% dernière semaine
        var_last_week = ((prix_composite[-1] - prix_composite[-2]) / prix_composite[-2] * 100) if len(prix_composite) >= 2 else 0
        
        # Détermination régime
        if sma5 > sma10 and var_last_week > 0.5:
            regime = "BULL"
            multiplier = 1.1
            details = f"Marché haussier (SMA5={sma5:.0f} > SMA10={sma10:.0f}, +{var_last_week:.1f}%)"
        elif sma5 < sma10 and var_last_week < -0.5:
            regime = "BEAR"
            multiplier = 0.85
            details = f"Marché baissier (SMA5={sma5:.0f} < SMA10={sma10:.0f}, {var_last_week:.1f}%)"
        else:
            regime = "NEUTRAL"
            multiplier = 1.0
            details = f"Marché neutre (SMA5={sma5:.0f}, SMA10={sma10:.0f})"
        
        return {
            "regime": regime,
            "multiplier": multiplier,
            "details": details,
            "sma5": round(sma5, 2),
            "sma10": round(sma10, 2),
            "variation_pct": round(var_last_week, 2)
        }
    
    @staticmethod
    def calculate_adaptive_stop_target(
        atr_pct: float,
        horizon: str = "WEEKLY"
    ) -> Tuple[float, float]:
        """
        STOP/TARGET ADAPTATIF selon horizon et ATR
        
        Calibration experte BRVM (30 ans):
        
        WEEKLY (2-8 semaines):
        - Stop: 1.0 × ATR% (min 4%)
        - Target: 2.6 × ATR%
        - RR: 2.6
        
        EXPLOSION_7J (7-10 jours):
        - Stop: 0.8 × ATR% (min 3.5%)
        - Target: 1.8 × ATR%
        - RR: 2.25
        
        Retour: (stop_pct, target_pct)
        """
        if horizon == "WEEKLY":
            stop_factor = 1.0
            target_factor = 2.6
            min_stop = 4.0
        elif horizon == "EXPLOSION_7J":
            stop_factor = 0.8
            target_factor = 1.8
            min_stop = 3.5
        else:  # Default
            stop_factor = 1.0
            target_factor = 2.5
            min_stop = 4.0
        
        stop_pct = max(stop_factor * atr_pct, min_stop)
        target_pct = target_factor * atr_pct
        
        return round(stop_pct, 2), round(target_pct, 2)


# === FONCTIONS UTILITAIRES ===

def score_volume_zscore(z: float) -> int:
    """
    Conversion Z-score volume en score 0-100
    
    Calibration BRVM experte:
    - Z > 2.0 : 100 (volume TRÈS anormal)
    - Z > 1.5 : 80 (volume anormal)
    - Z > 1.0 : 60 (volume élevé)
    - Z > 0.5 : 40 (volume légèrement élevé)
    - Z > 0 : 20 (volume normal+)
    - Z ≤ 0 : 0 (volume faible/normal)
    """
    if z is None:
        return 0
    
    if z >= 2.0:
        return 100
    elif z >= 1.5:
        return 80
    elif z >= 1.0:
        return 60
    elif z >= 0.5:
        return 40
    elif z > 0:
        return 20
    else:
        return 0


def score_momentum_accelere(accel: float) -> int:
    """
    Conversion accélération en score 0-100
    
    Calibration BRVM:
    - Accel > 5% : 100 (accélération explosive)
    - Accel > 3% : 80 (accélération forte)
    - Accel > 1% : 60 (accélération légère)
    - -1% < Accel < 1% : 40 (stable)
    - Accel < -1% : 20 (décélération)
    - Accel < -3% : 0 (décélération forte)
    """
    if accel is None:
        return 40  # Neutre
    
    if accel >= 5:
        return 100
    elif accel >= 3:
        return 80
    elif accel >= 1:
        return 60
    elif accel >= -1:
        return 40
    elif accel >= -3:
        return 20
    else:
        return 0


def test_indicators():
    """Test rapide des indicateurs"""
    print("=== TEST INDICATEURS AVANCÉS BRVM ===\n")
    
    # Test Volume Z-Score
    volumes = [5000, 5200, 4800, 5100, 4900, 5300, 5000, 4700, 12000]  # Dernière = spike
    z = IndicatorsAdvancedBRVM.volume_zscore(volumes)
    print(f"Volume Z-Score: {z} (attendu: ~2.5+)")
    print(f"Score: {score_volume_zscore(z)}/100\n")
    
    # Test Momentum Accéléré
    prix = [1000, 1010, 1025, 1055, 1095]  # Accélération croissante
    accel = IndicatorsAdvancedBRVM.momentum_accelere(prix)
    print(f"Momentum Accéléré: {accel}% (attendu: positif)")
    print(f"Score: {score_momentum_accelere(accel)}/100\n")
    
    # Test Breakout
    prix_breakout = [1000, 1005, 1002, 1008, 1050]  # Rupture à la fin
    volumes_breakout = [5000, 5100, 4900, 5200, 11000]
    atr_history = [10, 9.5, 8.8, 8.5, 8.2]  # Compression ATR
    breakout = IndicatorsAdvancedBRVM.breakout_detector(
        prix_breakout, volumes_breakout, atr_history
    )
    print(f"Breakout Detector: {breakout}\n")
    
    # Test EMA
    prix_ema = [1000, 1010, 1020, 1015, 1025, 1030]
    ema5 = IndicatorsAdvancedBRVM.ema(prix_ema, 5)
    print(f"EMA5: {ema5} (attendu: ~1020)\n")
    
    # Test Stop/Target
    stop, target = IndicatorsAdvancedBRVM.calculate_adaptive_stop_target(
        atr_pct=12.0, horizon="EXPLOSION_7J"
    )
    print(f"Stop/Target EXPLOSION_7J (ATR=12%):")
    print(f"  Stop: {stop}% (0.8×ATR)")
    print(f"  Target: {target}% (1.8×ATR)")
    print(f"  RR: {target/stop:.2f}\n")
    
    print("✅ Tests terminés")


if __name__ == "__main__":
    test_indicators()

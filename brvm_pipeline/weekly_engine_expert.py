#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODE EXPERT BRVM - MOTEUR WEEKLY PRODUCTION

OBJECTIF:
- Produit 3-8 candidats
- Execute 1-2 max
- RR >= 2.3 reel
- Mathematiquement exploitable
- Bat 95% des moteurs locaux

ARCHITECTURE:
RAW -> DAILY -> WEEKLY -> FILTRES EXPERT -> WOS RECALIBRE -> CLASSEMENT PRO

INNOVATION:
- Filtres realistes BRVM (pas elitistes steriles)
- WOS avec score ATR zone
- Stop/Target institutionnels
- Expected Return probabiliste
- Classement par ranking_score
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
import math

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION EXPERT BRVM
# ============================================================================

COLLECTION_WEEKLY = "prices_weekly"
COLLECTION_SEMANTIC = "AGREGATION_SEMANTIQUE_ACTION"
COLLECTION_DECISIONS = "decisions_brvm_weekly"

# FILTRES WEEKLY VERSION EXPERT BRVM
FILTERS = {
    # Liquidite (realiste BRVM)
    'volume_moyen_min': 2500,      # Au lieu de 5000 (trop brutal)
    'volume_ratio_min': 1.1,        # Au lieu de 1.3 (plus accessible)
    
    # RSI elargi
    'rsi_min': 25,                  # Au lieu de 30
    'rsi_max': 55,                  # Au lieu de 45 (permet hausse RSI 48-52)
    
    # ATR calibre BRVM PRO
    'atr_min': 6,                   # Zone tradable minimum
    'atr_max': 25,                  # Zone tradable maximum
    'atr_ideal_min': 8,             # Zone ideale
    'atr_ideal_max': 18,
    
    # Sentiment (non bloquant sauf catastrophe)
    'sentiment_blocage': ['VERY_NEGATIVE', 'SUSPENSION'],
    
    # Seuils finaux
    'wos_min': 65,                  # Au lieu de 70 (plus realiste)
    'rr_min': 2.2,                  # RR minimum
    'er_min': 3.0,                  # Expected Return minimum (%)
}

# NOUVEAUX POIDS WOS OPTIMISES BRVM
WOS_WEIGHTS = {
    'tendance': 0.35,               # Au lieu de 0.45
    'rsi': 0.25,
    'volume': 0.20,
    'atr_zone': 0.10,               # NOUVEAU
    'sentiment': 0.10
}

# STOPS/TARGETS PRO
STOP_TARGET = {
    'stop_multiplier': 1.0,         # stop = 1.0 x ATR%
    'target_multiplier': 2.6,       # target = 2.6 x ATR% -> RR=2.6
    'min_stop_pct': 4.0             # Stop minimum absolu
}

# ============================================================================
# ETAPE 1: FILTRES WEEKLY EXPERT
# ============================================================================

def apply_weekly_filters(symbol, week_str):
    """
    Filtres WEEKLY VERSION EXPERT BRVM
    
    Retourne: (passe: bool, raison: str, data: dict)
    """
    # Recuperer donnees weekly
    weekly = db[COLLECTION_WEEKLY].find_one({
        'symbol': symbol,
        'week': week_str
    })
    
    if not weekly:
        return False, "Pas de donnees weekly", None
    
    # ========================================================================
    # FILTRE 1: Liquidite realiste BRVM
    # ========================================================================
    
    # Volume moyen >= 2500
    volumes = list(db[COLLECTION_WEEKLY].find(
        {'symbol': symbol, 'week': {'$lte': week_str}},
        {'volume': 1}
    ).sort('week', -1).limit(8))
    
    if volumes:
        volume_moyen = sum(v.get('volume', 0) for v in volumes) / len(volumes)
    else:
        volume_moyen = 0
    
    if volume_moyen < FILTERS['volume_moyen_min']:
        return False, f"Volume moyen {volume_moyen:.0f} < {FILTERS['volume_moyen_min']}", None
    
    # Volume ratio >= 1.1
    volume_ratio = weekly.get('volume_ratio', 0)
    if volume_ratio < FILTERS['volume_ratio_min']:
        return False, f"Volume ratio {volume_ratio:.2f} < {FILTERS['volume_ratio_min']}", None
    
    # ========================================================================
    # FILTRE 2: RSI elargi (25-55)
    # ========================================================================
    
    rsi = weekly.get('rsi')
    if rsi is None:
        return False, "RSI manquant", None
    
    if not (FILTERS['rsi_min'] <= rsi <= FILTERS['rsi_max']):
        return False, f"RSI {rsi:.1f} hors zone [{FILTERS['rsi_min']}-{FILTERS['rsi_max']}]", None
    
    # ========================================================================
    # FILTRE 3: ATR calibre (6-25%)
    # ========================================================================
    
    atr_pct = weekly.get('atr_pct')
    if atr_pct is None:
        return False, "ATR manquant", None
    
    if not (FILTERS['atr_min'] <= atr_pct <= FILTERS['atr_max']):
        return False, f"ATR {atr_pct:.1f}% hors zone [{FILTERS['atr_min']}-{FILTERS['atr_max']}%]", None
    
    # ========================================================================
    # FILTRE 4: Tendance simplifiee
    # ========================================================================
    
    sma5 = weekly.get('sma5')
    sma10 = weekly.get('sma10')
    close = weekly.get('close', 0)
    
    trend_ok = False
    
    if sma5 and sma10:
        # SMA5 >= SMA10 OU Close > SMA10
        if sma5 >= sma10 or close > sma10:
            trend_ok = True
    elif close > 0:
        # Si pas de SMA, accepter par defaut
        trend_ok = True
    
    if not trend_ok:
        return False, "Tendance baissiere (SMA5 < SMA10 et Close < SMA10)", None
    
    # ========================================================================
    # FILTRE 5: Sentiment (non bloquant sauf catastrophe)
    # ========================================================================
    
    # Chercher donnees semantiques
    semantic = db[COLLECTION_SEMANTIC].find_one({
        'ticker': symbol,
        'semaine': week_str
    })
    
    nlp_flag = None
    if semantic:
        # Verifier si signal negatif majeur
        sentiment = semantic.get('sentiment_general', 'NEUTRAL')
        if sentiment in FILTERS['sentiment_blocage']:
            return False, f"Sentiment bloquant: {sentiment}", None
        nlp_flag = sentiment
    
    # ========================================================================
    # FILTRE PASSE - Retourner donnees pour WOS
    # ========================================================================
    
    return True, "OK", {
        'symbol': symbol,
        'week': week_str,
        'close': close,
        'rsi': rsi,
        'atr_pct': atr_pct,
        'sma5': sma5,
        'sma10': sma10,
        'volume_ratio': volume_ratio,
        'volume_moyen': volume_moyen,
        'trend': weekly.get('trend', 'NEUTRAL'),
        'volatility': weekly.get('volatility', 0),
        'nlp_flag': nlp_flag,
        'variation_pct': weekly.get('variation_pct', 0)
    }

# ============================================================================
# ETAPE 2: CALCUL WOS RECALIBRE
# ============================================================================

def calculate_atr_zone_score(atr_pct):
    """
    Score ATR zone (0-100)
    
    Zone ideale BRVM: 8-18%
    Zone acceptable: 6-8% et 18-25%
    """
    if FILTERS['atr_ideal_min'] <= atr_pct <= FILTERS['atr_ideal_max']:
        return 100  # Zone ideale
    elif FILTERS['atr_min'] <= atr_pct < FILTERS['atr_ideal_min']:
        return 60   # Lent mais ok
    elif FILTERS['atr_ideal_max'] < atr_pct <= FILTERS['atr_max']:
        return 60   # Speculatif mais ok
    else:
        return 0    # Hors zone

def calculate_wos_expert(data):
    """
    WOS RECALIBRE - BRVM EXPERT
    
    Nouvelle formule:
    WOS = 0.35 tendance + 0.25 RSI + 0.20 volume + 0.10 ATR zone + 0.10 sentiment
    
    Seuil: WOS >= 65 (au lieu de 70)
    """
    # ========================================================================
    # 1. SCORE TENDANCE (0-100)
    # ========================================================================
    
    score_tendance = 0
    
    sma5 = data.get('sma5')
    sma10 = data.get('sma10')
    close = data.get('close', 0)
    
    if sma5 and sma10 and close:
        # SMA5 > SMA10 > Close = max points
        if sma5 > sma10 and close > sma5:
            score_tendance = 100
        elif sma5 > sma10:
            score_tendance = 80
        elif close > sma10:
            score_tendance = 60
        else:
            score_tendance = 40
    
    # ========================================================================
    # 2. SCORE RSI (0-100)
    # ========================================================================
    
    rsi = data.get('rsi', 50)
    
    # Zone optimale RSI: 40-50 (accumulation pro)
    if 40 <= rsi <= 50:
        score_rsi = 100
    elif 35 <= rsi < 40 or 50 < rsi <= 55:
        score_rsi = 80
    elif 25 <= rsi < 35:
        score_rsi = 60  # Oversold (rebond potentiel)
    else:
        score_rsi = 40
    
    # ========================================================================
    # 3. SCORE VOLUME (0-100)
    # ========================================================================
    
    volume_ratio = data.get('volume_ratio', 1)
    
    if volume_ratio >= 2.0:
        score_volume = 100  # Explosion volume
    elif volume_ratio >= 1.5:
        score_volume = 80   # Bon volume
    elif volume_ratio >= 1.2:
        score_volume = 60   # Hausse moderee
    elif volume_ratio >= 1.1:
        score_volume = 40   # Minimum acceptable
    else:
        score_volume = 20
    
    # ========================================================================
    # 4. SCORE ATR ZONE (0-100) - NOUVEAU
    # ========================================================================
    
    atr_pct = data.get('atr_pct', 10)
    score_atr_zone = calculate_atr_zone_score(atr_pct)
    
    # ========================================================================
    # 5. SCORE SENTIMENT (0-100)
    # ========================================================================
    
    nlp_flag = data.get('nlp_flag')
    
    if nlp_flag == 'POSITIVE':
        score_sentiment = 100
    elif nlp_flag == 'NEUTRAL' or nlp_flag is None:
        score_sentiment = 50
    elif nlp_flag == 'NEGATIVE':
        score_sentiment = 20
    else:
        score_sentiment = 0  # VERY_NEGATIVE (deja filtre)
    
    # ========================================================================
    # WOS FINAL
    # ========================================================================
    
    wos = (
        WOS_WEIGHTS['tendance'] * score_tendance +
        WOS_WEIGHTS['rsi'] * score_rsi +
        WOS_WEIGHTS['volume'] * score_volume +
        WOS_WEIGHTS['atr_zone'] * score_atr_zone +
        WOS_WEIGHTS['sentiment'] * score_sentiment
    )
    
    return {
        'wos': round(wos, 1),
        'score_tendance': round(score_tendance, 1),
        'score_rsi': round(score_rsi, 1),
        'score_volume': round(score_volume, 1),
        'score_atr_zone': round(score_atr_zone, 1),
        'score_sentiment': round(score_sentiment, 1)
    }

# ============================================================================
# ETAPE 3: STOP/TARGET PRO
# ============================================================================

def calculate_stop_target(atr_pct):
    """
    Stop/Target institutionnels
    
    stop_pct = max(1.0 x ATR%, 4%)
    target_pct = 2.6 x ATR%
    RR = target_pct / stop_pct
    """
    stop_pct = max(STOP_TARGET['stop_multiplier'] * atr_pct, STOP_TARGET['min_stop_pct'])
    target_pct = STOP_TARGET['target_multiplier'] * atr_pct
    
    rr = round(target_pct / stop_pct, 2) if stop_pct > 0 else 0
    
    return {
        'stop_pct': round(stop_pct, 2),
        'target_pct': round(target_pct, 2),
        'risk_reward': rr
    }

# ============================================================================
# ETAPE 4: EXPECTED RETURN REALISTE
# ============================================================================

def calculate_expected_return(wos, stop_pct, target_pct):
    """
    Expected Return realiste (probabiliste)
    
    proba = min(0.80, 0.45 + (WOS / 200))
    ER = (target_pct x proba) - (stop_pct x (1 - proba))
    
    Filtre: ER > 3%
    """
    # Probabilite basee sur WOS
    proba = min(0.80, 0.45 + (wos / 200))
    
    # Expected Return
    er = (target_pct * proba) - (stop_pct * (1 - proba))
    
    return {
        'expected_return': round(er, 2),
        'proba_gain': round(proba * 100, 1)
    }

# ============================================================================
# ETAPE 5: CLASSEMENT FINAL
# ============================================================================

def calculate_ranking_score(er, rr, wos):
    """
    Ranking Score pour affichage dashboard
    
    ranking_score = 0.5 x ER + 0.3 x RR + 0.2 x WOS
    
    Tri decroissant
    """
    # Normaliser RR sur 100 (RR=3 -> 100 points)
    rr_normalized = min(100, (rr / 3) * 100)
    
    ranking = (
        0.5 * er +
        0.3 * rr_normalized +
        0.2 * wos
    )
    
    return round(ranking, 2)

def classify_decision(wos, rr, er):
    """
    Classification finale A/B
    
    Classe A: WOS >= 75 ET RR >= 2.5 ET ER > 10
    Classe B: WOS >= 65 ET RR >= 2.2 ET ER > 3
    """
    if wos >= 75 and rr >= 2.5 and er > 10:
        return 'A'
    elif wos >= 65 and rr >= 2.2 and er > 3:
        return 'B'
    else:
        return 'C'  # Ne sera pas affiche

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def generate_weekly_decisions(week_str=None):
    """
    Generer decisions weekly EXPERT BRVM
    
    Retour: 3-8 candidats (classes A/B uniquement)
    """
    if not week_str:
        week_str = datetime.now().strftime("%Y-W%V")
    
    print("\n" + "="*80)
    print(f"MODE EXPERT BRVM - WEEKLY DECISIONS - {week_str}")
    print("="*80)
    print("\nFILTRES ACTIFS:")
    print(f"  - Liquidite: volume_moyen >= {FILTERS['volume_moyen_min']}, ratio >= {FILTERS['volume_ratio_min']}")
    print(f"  - RSI: {FILTERS['rsi_min']}-{FILTERS['rsi_max']} (elargi)")
    print(f"  - ATR: {FILTERS['atr_min']}-{FILTERS['atr_max']}% (zone tradable)")
    print(f"  - WOS: >= {FILTERS['wos_min']} (realiste)")
    print(f"  - RR: >= {FILTERS['rr_min']}")
    print(f"  - ER: > {FILTERS['er_min']}%")
    print("\n" + "="*80 + "\n")
    
    # Tous les symboles
    symbols = db[COLLECTION_WEEKLY].distinct('symbol', {'week': week_str})
    
    print(f"Analyse de {len(symbols)} actions...\n")
    
    candidates = []
    stats = {
        'total': len(symbols),
        'filtre_liquidite': 0,
        'filtre_rsi': 0,
        'filtre_atr': 0,
        'filtre_tendance': 0,
        'filtre_sentiment': 0,
        'filtre_wos': 0,
        'filtre_rr': 0,
        'filtre_er': 0,
        'valides': 0
    }
    
    for symbol in symbols:
        # ====================================================================
        # ETAPE 1: Filtres WEEKLY
        # ====================================================================
        
        passe, raison, data = apply_weekly_filters(symbol, week_str)
        
        if not passe:
            # Comptabiliser raison
            if 'Volume' in raison:
                stats['filtre_liquidite'] += 1
            elif 'RSI' in raison:
                stats['filtre_rsi'] += 1
            elif 'ATR' in raison:
                stats['filtre_atr'] += 1
            elif 'Tendance' in raison or 'SMA' in raison:
                stats['filtre_tendance'] += 1
            elif 'Sentiment' in raison:
                stats['filtre_sentiment'] += 1
            continue
        
        # ====================================================================
        # ETAPE 2: WOS RECALIBRE
        # ====================================================================
        
        wos_data = calculate_wos_expert(data)
        wos = wos_data['wos']
        
        if wos < FILTERS['wos_min']:
            stats['filtre_wos'] += 1
            continue
        
        # ====================================================================
        # ETAPE 3: Stop/Target
        # ====================================================================
        
        st_data = calculate_stop_target(data['atr_pct'])
        rr = st_data['risk_reward']
        
        if rr < FILTERS['rr_min']:
            stats['filtre_rr'] += 1
            continue
        
        # ====================================================================
        # ETAPE 4: Expected Return
        # ====================================================================
        
        er_data = calculate_expected_return(wos, st_data['stop_pct'], st_data['target_pct'])
        er = er_data['expected_return']
        
        if er < FILTERS['er_min']:
            stats['filtre_er'] += 1
            continue
        
        # ====================================================================
        # ETAPE 5: Classement
        # ====================================================================
        
        classe = classify_decision(wos, rr, er)
        
        if classe == 'C':
            continue  # Ne pas afficher classe C
        
        ranking_score = calculate_ranking_score(er, rr, wos)
        
        # ====================================================================
        # CANDIDAT VALIDE
        # ====================================================================
        
        stats['valides'] += 1
        
        decision = {
            'symbol': symbol,
            'week': week_str,
            'signal': 'BUY',
            'classe': classe,
            
            # Scores
            'wos': wos,
            'ranking_score': ranking_score,
            
            # Composantes WOS
            'score_tendance': wos_data['score_tendance'],
            'score_rsi': wos_data['score_rsi'],
            'score_volume': wos_data['score_volume'],
            'score_atr_zone': wos_data['score_atr_zone'],
            'score_sentiment': wos_data['score_sentiment'],
            
            # Stop/Target
            'stop_pct': st_data['stop_pct'],
            'target_pct': st_data['target_pct'],
            'risk_reward': rr,
            
            # Expected Return
            'expected_return': er,
            'proba_gain': er_data['proba_gain'],
            
            # Donnees techniques
            'rsi': data['rsi'],
            'atr_pct': data['atr_pct'],
            'volume_ratio': data['volume_ratio'],
            'close': data['close'],
            'variation_pct': data['variation_pct'],
            
            # Metadata
            'generated_at': datetime.now(),
            'mode': 'EXPERT_BRVM'
        }
        
        candidates.append(decision)
    
    # ========================================================================
    # TRI PAR RANKING_SCORE DECROISSANT
    # ========================================================================
    
    candidates.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    # ========================================================================
    # SAUVEGARDE MONGODB
    # ========================================================================
    
    db[COLLECTION_DECISIONS].delete_many({'week': week_str, 'mode': 'EXPERT_BRVM'})
    
    if candidates:
        for rank, cand in enumerate(candidates, 1):
            cand['rank'] = rank
            db[COLLECTION_DECISIONS].insert_one(cand)
    
    # ========================================================================
    # AFFICHAGE
    # ========================================================================
    
    print("="*80)
    print("STATISTIQUES FILTRAGE")
    print("="*80)
    print(f"Total actions:          {stats['total']}")
    print(f"  Filtre Liquidite:     {stats['filtre_liquidite']}")
    print(f"  Filtre RSI:           {stats['filtre_rsi']}")
    print(f"  Filtre ATR:           {stats['filtre_atr']}")
    print(f"  Filtre Tendance:      {stats['filtre_tendance']}")
    print(f"  Filtre Sentiment:     {stats['filtre_sentiment']}")
    print(f"  Filtre WOS:           {stats['filtre_wos']}")
    print(f"  Filtre RR:            {stats['filtre_rr']}")
    print(f"  Filtre ER:            {stats['filtre_er']}")
    print(f"\nCANDIDATS VALIDES:      {stats['valides']}")
    print("="*80 + "\n")
    
    if not candidates:
        print("Aucun candidat cette semaine (filtres stricts)")
        print("\nC'est NORMAL sur BRVM - Le moteur est selectif.")
        return []
    
    print("="*80)
    print(f"RECOMMANDATIONS WEEKLY - {week_str}")
    print("="*80)
    print(f"\n{'#':<3} {'TICKER':<8} {'CL':<3} {'RANK':<6} {'WOS':<6} {'RR':<6} {'ER%':<6} {'STOP%':<7} {'TARGET%':<8} {'PRIX':<8}")
    print("-"*80)
    
    for cand in candidates:
        print(
            f"{cand['rank']:<3} "
            f"{cand['symbol']:<8} "
            f"{cand['classe']:<3} "
            f"{cand['ranking_score']:<6.1f} "
            f"{cand['wos']:<6.1f} "
            f"{cand['risk_reward']:<6.2f} "
            f"{cand['expected_return']:<6.1f} "
            f"{cand['stop_pct']:<7.1f} "
            f"{cand['target_pct']:<8.1f} "
            f"{cand['close']:<8.0f}"
        )
    
    print("\n" + "="*80)
    print(f"Sauvegarde: {len(candidates)} decisions dans MongoDB")
    print(f"Collection: {COLLECTION_DECISIONS}")
    print("="*80 + "\n")
    
    # Conseil execution
    classe_a = len([c for c in candidates if c['classe'] == 'A'])
    classe_b = len([c for c in candidates if c['classe'] == 'B'])
    
    print("CONSEIL EXECUTION:")
    print(f"  Classe A: {classe_a} (executer max 1)")
    print(f"  Classe B: {classe_b} (executer max 1)")
    print(f"\nExecution recommandee: 1-2 positions max")
    print("\n" + "="*80 + "\n")
    
    return candidates

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WEEKLY ENGINE EXPERT BRVM')
    parser.add_argument('--week', help='Semaine (YYYY-Www)')
    
    args = parser.parse_args()
    
    generate_weekly_decisions(args.week)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR RECOMMANDATIONS BRVM - TOLÉRANCE ZÉRO
Version standalone (sans Django) pour gros clients
"""

from pymongo import MongoClient
from datetime import datetime

print("="*80)
print("MODE EXPERT BRVM - RECOMMANDATIONS TOLÉRANCE ZÉRO")
print("Pour gros clients - Qualité maximale uniquement")
print("="*80)

# ============================================================================
# CONFIGURATION STRICTE
# ============================================================================

FILTERS = {
    'volume_moyen_min': 2500,
    'volume_ratio_min': 1.1,
    'rsi_min': 25,
    'rsi_max': 55,
    'atr_min': 6,
    'atr_max': 25,
    'atr_ideal_min': 8,
    'atr_ideal_max': 18,
    'wos_min': 65,         # Strict
    'rr_min': 2.3,         # TOLÉRANCE ZÉRO : RR >= 2.3
    'er_min': 5.0,         # TOLÉRANCE ZÉRO : ER >= 5%
}

WOS_WEIGHTS = {
    'tendance': 0.35,
    'rsi': 0.25,
    'volume': 0.20,
    'atr_zone': 0.10,
    'sentiment': 0.10
}

# ============================================================================
# CONNEXION MongoDB
# ============================================================================

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# ============================================================================
# SÉLECTION SEMAINE
# ============================================================================

weeks = sorted(db.prices_weekly.distinct('week'))
if not weeks:
    print("\n❌ ERREUR : Aucune donnée weekly")
    exit(1)

WEEK = weeks[-1]
print(f"\n📅 Semaine analysée : {WEEK}")
print(f"   Historique : {len(weeks)} semaines ({weeks[0]} → {WEEK})")

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

week_obs = list(db.prices_weekly.find({'week': WEEK}))
print(f"\n📊 {len(week_obs)} actions disponibles semaine {WEEK}")

# Filtrage initial : indicators + ATR tradable
candidates = []
for obs in week_obs:
    if not obs.get('rsi') or not obs.get('atr_pct'):
        continue
    
    atr = obs.get('atr_pct', 0)
    if not (FILTERS['atr_min'] <= atr <= FILTERS['atr_max']):
        continue
    
    candidates.append(obs)

print(f"   Avec indicateurs + ATR tradable : {len(candidates)}")

if len(candidates) == 0:
    print("\n⚠️  TOLÉRANCE ZÉRO : Aucune action tradable cette semaine")
    print("   → Attendre opportunités de meilleure qualité")
    exit(0)

# ============================================================================
# FONCTION CALCUL WOS
# ============================================================================

def calculate_wos(obs):
    """WOS recalibré BRVM"""
    
    # 1. Score tendance
    sma5 = obs.get('sma5', 0)
    sma10 = obs.get('sma10', 0)
    close = obs.get('close', 0)
    
    if sma5 and sma10 and close:
        if sma5 > sma10 and close > sma5:
            score_tendance = 100
        elif sma5 > sma10:
            score_tendance = 80
        elif close > sma10:
            score_tendance = 60
        else:
            score_tendance = 40
    else:
        score_tendance = 50  # Neutre si pas de SMA
    
    # 2. Score RSI
    rsi = obs.get('rsi', 50)
    if 40 <= rsi <= 50:
        score_rsi = 100
    elif 35 <= rsi < 40 or 50 < rsi <= 55:
        score_rsi = 80
    elif 25 <= rsi < 35:
        score_rsi = 60
    else:
        score_rsi = 40
    
    # 3. Score volume
    vol_ratio = obs.get('volume_ratio', 1)
    if vol_ratio >= 2.0:
        score_volume = 100
    elif vol_ratio >= 1.5:
        score_volume = 80
    elif vol_ratio >= 1.2:
        score_volume = 60
    elif vol_ratio >= 1.1:
        score_volume = 40
    else:
        score_volume = 20
    
    # 4. Score ATR zone
    atr = obs.get('atr_pct', 10)
    if FILTERS['atr_ideal_min'] <= atr <= FILTERS['atr_ideal_max']:
        score_atr = 100
    elif FILTERS['atr_min'] <= atr < FILTERS['atr_ideal_min']:
        score_atr = 60
    elif FILTERS['atr_ideal_max'] < atr <= FILTERS['atr_max']:
        score_atr = 60
    else:
        score_atr = 0
    
    # 5. Score sentiment (neutre par défaut)
    score_sentiment = 50
    
    # WOS final
    wos = (
        WOS_WEIGHTS['tendance'] * score_tendance +
        WOS_WEIGHTS['rsi'] * score_rsi +
        WOS_WEIGHTS['volume'] * score_volume +
        WOS_WEIGHTS['atr_zone'] * score_atr +
        WOS_WEIGHTS['sentiment'] * score_sentiment
    )
    
    return round(wos, 1)

# ============================================================================
# CALCUL STOP/TARGET/RR
# ============================================================================

def calculate_metrics(obs):
    """Calcul Stop, Target, RR, ER"""
    atr = obs.get('atr_pct', 10)
    
    # Stop/Target
    stop_pct = max(1.0 * atr, 4.0)
    target_pct = 2.6 * atr
    rr = round(target_pct / stop_pct, 2) if stop_pct > 0 else 0
    
    # WOS
    wos = calculate_wos(obs)
    
    # Expected Return
    proba = min(0.80, 0.45 + (wos / 200))
    er = round((target_pct * proba) - (stop_pct * (1 - proba)), 2)
    
    # Ranking score
    rr_normalized = min(100, (rr / 3) * 100)
    ranking = round(0.5 * er + 0.3 * rr_normalized + 0.2 * wos, 2)
    
    return {
        'wos': wos,
        'stop_pct': round(stop_pct, 2),
        'target_pct': round(target_pct, 2),
        'rr': rr,
        'er': er,
        'proba': round(proba * 100, 1),
        'ranking': ranking
    }

# ============================================================================
# FILTRAGE ET CLASSEMENT
# ============================================================================

print(f"\n🔍 Application filtres TOLÉRANCE ZÉRO...")

decisions = []
stats = {
    'total': len(candidates),
    'filtre_rsi': 0,
    'filtre_wos': 0,
    'filtre_rr': 0,
    'filtre_er': 0,
    'valides': 0
}

for obs in candidates:
    symbol = obs.get('symbol')
    
    # Filtre RSI
    rsi = obs.get('rsi', 50)
    if not (FILTERS['rsi_min'] <= rsi <= FILTERS['rsi_max']):
        stats['filtre_rsi'] += 1
        continue
    
    # Calcul métriques
    metrics = calculate_metrics(obs)
    
    # Filtre WOS
    if metrics['wos'] < FILTERS['wos_min']:
        stats['filtre_wos'] += 1
        continue
    
    # Filtre RR (TOLÉRANCE ZÉRO)
    if metrics['rr'] < FILTERS['rr_min']:
        stats['filtre_rr'] += 1
        continue
    
    # Filtre ER (TOLÉRANCE ZÉRO)
    if metrics['er'] < FILTERS['er_min']:
        stats['filtre_er'] += 1
        continue
    
    # Classification
    if metrics['wos'] >= 75 and metrics['rr'] >= 2.5 and metrics['er'] > 10:
        classe = 'A'
    elif metrics['wos'] >= 65 and metrics['rr'] >= 2.3 and metrics['er'] > 5:
        classe = 'B'
    else:
        continue  # Pas de classe C
    
    # VALIDE !
    stats['valides'] += 1
    
    decisions.append({
        'symbol': symbol,
        'week': WEEK,
        'classe': classe,
        'wos': metrics['wos'],
        'rr': metrics['rr'],
        'er': metrics['er'],
        'stop_pct': metrics['stop_pct'],
        'target_pct': metrics['target_pct'],
        'proba_gain': metrics['proba'],
        'ranking': metrics['ranking'],
        'close': obs.get('close', 0),
        'atr_pct': obs.get('atr_pct', 0),
        'rsi': rsi,
        'volume': obs.get('volume', 0),
        'generated_at': datetime.now()
    })

# Tri par ranking
decisions.sort(key=lambda x: x['ranking'], reverse=True)

# ============================================================================
# AFFICHAGE STATISTIQUES
# ============================================================================

print(f"\n{'='*80}")
print(f"STATISTIQUES FILTRAGE STRICT")
print(f"{'='*80}")
print(f"Total candidats       : {stats['total']}")
print(f"  ❌ RSI hors zone     : {stats['filtre_rsi']}")
print(f"  ❌ WOS < {FILTERS['wos_min']}        : {stats['filtre_wos']}")
print(f"  ❌ RR < {FILTERS['rr_min']}         : {stats['filtre_rr']} (TOLÉRANCE ZÉRO)")
print(f"  ❌ ER < {FILTERS['er_min']}%        : {stats['filtre_er']} (TOLÉRANCE ZÉRO)")
print(f"\n✅ RECOMMANDATIONS    : {stats['valides']}")

if stats['valides'] == 0:
    print(f"\n{'='*80}")
    print(f"⚠️  TOLÉRANCE ZÉRO : AUCUNE RECOMMANDATION")
    print(f"{'='*80}")
    print(f"\n💡 GROS CLIENTS :")
    print(f"   • Filtres stricts ont éliminé toutes les actions")
    print(f"   • Qualité insuffisante cette semaine")
    print(f"   • MIEUX AUCUNE recommandation qu'une MAUVAISE")
    print(f"   • Attendre opportunités semaine prochaine")
    print(f"\n{'='*80}")
    exit(0)

# ============================================================================
# RÉSULTATS
# ============================================================================

classe_a = [d for d in decisions if d['classe'] == 'A']
classe_b = [d for d in decisions if d['classe'] == 'B']

print(f"  Classe A (Excellence) : {len(classe_a)}")
print(f"  Classe B (Qualité)    : {len(classe_b)}")

# Moyennes
avg_rr = sum(d['rr'] for d in decisions) / len(decisions)
avg_er = sum(d['er'] for d in decisions) / len(decisions)
avg_wos = sum(d['wos'] for d in decisions) / len(decisions)

print(f"\n📈 QUALITÉ MOYENNE :")
print(f"   RR moyen  : {avg_rr:.2f}")
print(f"   ER moyen  : {avg_er:.1f}%")
print(f"   WOS moyen : {avg_wos:.1f}")

# ============================================================================
# AFFICHAGE RECOMMANDATIONS
# ============================================================================

print(f"\n{'='*80}")
print(f"RECOMMANDATIONS BRVM - {WEEK}")
print(f"{'='*80}\n")
print(f"{'#':<3} {'SYMBOLE':<8} {'CL':<3} {'RANK':<7} {'WOS':<6} {'RR':<6} {'ER%':<6} {'STOP%':<7} {'TARGET%':<8} {'ATR%':<7}")
print("-"*80)

for i, dec in enumerate(decisions, 1):
    marker = "🟢" if dec['classe'] == 'A' else "🟡"
    print(
        f"{i:<3} {dec['symbol']:<8} {dec['classe']:<3} {dec['ranking']:<7.1f} "
        f"{dec['wos']:<6.1f} {dec['rr']:<6.2f} {dec['er']:<6.1f} "
        f"{dec['stop_pct']:<7.1f} {dec['target_pct']:<8.1f} {dec['atr_pct']:<7.1f} {marker}"
    )

# ============================================================================
# CONSEIL EXÉCUTION GROS CLIENTS
# ============================================================================

print(f"\n{'='*80}")
print(f"CONSEIL EXÉCUTION - GROS CLIENTS (TOLÉRANCE ZÉRO)")
print(f"{'='*80}")

if len(classe_a) > 0:
    top1 = classe_a[0]
    print(f"\n✅ RECOMMANDATION PRINCIPALE :")
    print(f"   Symbole    : {top1['symbol']}")
    print(f"   Classe     : A (Excellence)")
    print(f"   Prix actuel: {top1['close']:,.0f} FCFA")
    print(f"   Stop loss  : {top1['stop_pct']:.1f}% ({top1['close'] * (1 - top1['stop_pct']/100):,.0f} FCFA)")
    print(f"   Objectif   : {top1['target_pct']:.1f}% ({top1['close'] * (1 + top1['target_pct']/100):,.0f} FCFA)")
    print(f"   Risk/Reward: {top1['rr']:.2f}")
    print(f"   Gain estimé: {top1['er']:.1f}% (proba {top1['proba_gain']}%)")
    print(f"   WOS        : {top1['wos']:.1f}/100")
    
    if len(classe_a) > 1:
        print(f"\n   Alternative classe A : {classe_a[1]['symbol']} (RR={classe_a[1]['rr']:.2f})")
        
else:
    print(f"\n⚠️  AUCUNE classe A disponible")
    if len(classe_b) > 0:
        top_b = classe_b[0]
        print(f"\n   Option classe B : {top_b['symbol']}")
        print(f"   Qualité acceptable mais pas excellence")
        print(f"   RR = {top_b['rr']:.2f}, ER = {top_b['er']:.1f}%")
        print(f"\n   💡 CONSEIL : Attendre classe A semaine prochaine")
    else:
        print(f"\n   Aucune recommandation viable cette semaine")

print(f"\n📜 RÈGLES TOLÉRANCE ZÉRO :")
print(f"   1. MAX 1-2 positions simultanées (jamais plus)")
print(f"   2. STOP LOSS OBLIGATOIRE (non négociable)")
print(f"   3. Si doute → NE PAS EXÉCUTER")
print(f"   4. Privilégier CLASSE A uniquement")
print(f"   5. Sortir si stop touché (pas de moyennage à la baisse)")

# ============================================================================
# SAUVEGARDE MongoDB
# ============================================================================

print(f"\n{'='*80}")
print(f"SAUVEGARDE MongoDB")
print(f"{'='*80}")

# Supprimer anciennes décisions de la semaine
db.decisions_brvm_weekly.delete_many({'week': WEEK})

# Insérer nouvelles
for rank, dec in enumerate(decisions, 1):
    dec['rank'] = rank
    dec['mode'] = 'EXPERT_TOLERANCE_ZERO'
    db.decisions_brvm_weekly.insert_one(dec)

print(f"✅ {len(decisions)} décisions sauvegardées")
print(f"   Collection : decisions_brvm_weekly")
print(f"   Semaine    : {WEEK}")
print(f"   Date       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print(f"\n{'='*80}")
print(f"✅ GÉNÉRATION TERMINÉE - TOLÉRANCE ZÉRO RESPECTÉE")
print(f"{'='*80}\n")

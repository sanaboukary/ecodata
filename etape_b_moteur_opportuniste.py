#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE B - REBUILD MOTEUR OPPORTUNISTE DAILY
============================================
Détecteur d'opportunités J+1 à J+7 avec 4 détecteurs
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("ETAPE B - MOTEUR OPPORTUNISTE DAILY")
print("="*80 + "\n")

# Configuration détecteurs
DETECTORS_CONFIG = {
    'news_silencieuse': {
        'enabled': True,
        'weight': 0.30,
        'lookback_days': 7,
        'min_price_move': 0.02  # 2% mouvement sans news
    },
    'volume_anormal': {
        'enabled': True,
        'weight': 0.35,
        'sigma_threshold': 2.5,  # 2.5 écarts-types
        'min_volume': 100
    },
    'rupture_sommeil': {
        'enabled': True,
        'weight': 0.20,
        'dormant_days': 30,
        'activation_volume_mult': 3  # 3x volume moyen
    },
    'retard_secteur': {
        'enabled': False,  # Désactivé - besoin secteurs mappés
        'weight': 0.15,
        'underperformance_threshold': -0.05  # -5% vs secteur
    }
}

print("Configuration detecteurs:")
for name, config in DETECTORS_CONFIG.items():
    status = "ACTIF" if config['enabled'] else "INACTIF"
    weight = config.get('weight', 0) * 100
    print(f"  {name:20} : {status} ({weight:.0f}%)")

# 1. PRÉPARATION DES DONNÉES
print("\n" + "-"*80)
print("PHASE 1: PREPARATION DONNEES")
print("-"*80 + "\n")

# Récupérer toutes les données DAILY des 30 derniers jours
cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
recent_daily = list(db.prices_daily.find(
    {'date': {'$gte': cutoff_date}}
).sort([('symbol', 1), ('date', 1)]))

print(f"Donnees DAILY recentes (30j): {len(recent_daily)}")

# Grouper par symbole
symbol_data = defaultdict(list)
for doc in recent_daily:
    symbol = doc.get('symbol')
    if symbol:
        symbol_data[symbol].append(doc)

print(f"Symboles actifs: {len(symbol_data)}\n")

# Récupérer publications BRVM récentes
recent_pubs = list(db.curated_observations.find({
    'source': 'BRVM_PUBLICATION',
    'ts': {'$gte': cutoff_date}
}))

print(f"Publications BRVM (30j): {len(recent_pubs)}\n")

# 2. DÉTECTEUR 1: NEWS SILENCIEUSE
print("-"*80)
print("DETECTEUR 1: NEWS SILENCIEUSE")
print("-"*80)

detector1_hits = []

if DETECTORS_CONFIG['news_silencieuse']['enabled']:
    print("Recherche mouvements de prix sans publication...\n")
    
    for symbol, docs in symbol_data.items():
        if len(docs) < 7:
            continue
        
        # Trier par date
        docs.sort(key=lambda x: x.get('date', ''))
        
        # Vérifier chaque jour
        for i in range(len(docs) - 1):
            current = docs[i]
            previous = docs[i-1] if i > 0 else None
            
            if not previous:
                continue
            
            # Mouvement de prix
            close_prev = previous.get('close', 0)
            close_curr = current.get('close', 0)
            
            if close_prev == 0:
                continue
            
            price_move = abs((close_curr - close_prev) / close_prev)
            
            # Seuil de mouvement significatif
            if price_move >= DETECTORS_CONFIG['news_silencieuse']['min_price_move']:
                # Vérifier s'il y a une publication ce jour
                date = current.get('date')
                has_publication = any(
                    pub.get('ticker') == symbol and pub.get('ts', '').startswith(date)
                    for pub in recent_pubs
                )
                
                if not has_publication:
                    # Opportunité détectée
                    score = min(price_move * 10, 1.0)  # Normaliser à 1
                    
                    detector1_hits.append({
                        'symbol': symbol,
                        'date': date,
                        'detector': 'news_silencieuse',
                        'score': round(score, 3),
                        'price_move': round(price_move * 100, 2),
                        'close': close_curr,
                        'details': {
                            'price_move_pct': round(price_move * 100, 2),
                            'has_news': has_publication
                        }
                    })
    
    print(f"Opportunites detectees: {len(detector1_hits)}")
    if detector1_hits:
        print("Exemples:")
        for opp in detector1_hits[:5]:
            print(f"  {opp['symbol']:8} {opp['date']} : +{opp['details']['price_move_pct']:.1f}% sans news (score: {opp['score']:.2f})")

# 3. DÉTECTEUR 2: VOLUME ANORMAL
print("\n" + "-"*80)
print("DETECTEUR 2: VOLUME ANORMAL")
print("-"*80)

detector2_hits = []

if DETECTORS_CONFIG['volume_anormal']['enabled']:
    print("Recherche pics de volume inhabituels...\n")
    
    for symbol, docs in symbol_data.items():
        if len(docs) < 14:
            continue
        
        # Calculer volume moyen et écart-type
        volumes = [d.get('volume', 0) for d in docs]
        avg_volume = sum(volumes) / len(volumes)
        
        if avg_volume < DETECTORS_CONFIG['volume_anormal']['min_volume']:
            continue
        
        # Écart-type
        variance = sum((v - avg_volume) ** 2 for v in volumes) / len(volumes)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            continue
        
        # Trouver jours avec volume anormal
        for doc in docs[-7:]:  # 7 derniers jours
            volume = doc.get('volume', 0)
            z_score = (volume - avg_volume) / std_dev
            
            if z_score >= DETECTORS_CONFIG['volume_anormal']['sigma_threshold']:
                score = min(z_score / 5, 1.0)  # Normaliser
                
                detector2_hits.append({
                    'symbol': symbol,
                    'date': doc.get('date'),
                    'detector': 'volume_anormal',
                    'score': round(score, 3),
                    'volume': volume,
                    'details': {
                        'volume': int(volume),
                        'avg_volume': int(avg_volume),
                        'z_score': round(z_score, 2),
                        'multiplier': round(volume / avg_volume, 1)
                    }
                })
    
    print(f"Opportunites detectees: {len(detector2_hits)}")
    if detector2_hits:
        print("Exemples:")
        for opp in detector2_hits[:5]:
            print(f"  {opp['symbol']:8} {opp['date']} : {opp['details']['multiplier']:.1f}x volume (z={opp['details']['z_score']:.1f})")

# 4. DÉTECTEUR 3: RUPTURE SOMMEIL
print("\n" + "-"*80)
print("DETECTEUR 3: RUPTURE SOMMEIL")
print("-"*80)

detector3_hits = []

if DETECTORS_CONFIG['rupture_sommeil']['enabled']:
    print("Recherche actions dormantes qui se reveillent...\n")
    
    # Récupérer plus de données (60j) pour détection sommeil
    extended_cutoff = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    extended_daily = list(db.prices_daily.find(
        {'date': {'$gte': extended_cutoff}}
    ).sort([('symbol', 1), ('date', 1)]))
    
    extended_symbol_data = defaultdict(list)
    for doc in extended_daily:
        symbol = doc.get('symbol')
        if symbol:
            extended_symbol_data[symbol].append(doc)
    
    for symbol, docs in extended_symbol_data.items():
        if len(docs) < 30:
            continue
        
        # Trier
        docs.sort(key=lambda x: x.get('date', ''))
        
        # Vérifier les 30 premiers jours (période "dormante")
        dormant_period = docs[:30]
        recent_period = docs[-7:]
        
        # Volume moyen période dormante
        dormant_volumes = [d.get('volume', 0) for d in dormant_period]
        avg_dormant_volume = sum(dormant_volumes) / len(dormant_volumes)
        
        if avg_dormant_volume == 0:
            avg_dormant_volume = 1
        
        # Volume moyen période récente
        recent_volumes = [d.get('volume', 0) for d in recent_period]
        avg_recent_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Activation?
        volume_mult = avg_recent_volume / avg_dormant_volume
        
        if volume_mult >= DETECTORS_CONFIG['rupture_sommeil']['activation_volume_mult']:
            score = min(volume_mult / 10, 1.0)
            
            detector3_hits.append({
                'symbol': symbol,
                'date': recent_period[-1].get('date'),
                'detector': 'rupture_sommeil',
                'score': round(score, 3),
                'volume_mult': round(volume_mult, 1),
                'details': {
                    'dormant_avg_volume': int(avg_dormant_volume),
                    'recent_avg_volume': int(avg_recent_volume),
                    'activation_mult': round(volume_mult, 1)
                }
            })
    
    print(f"Opportunites detectees: {len(detector3_hits)}")
    if detector3_hits:
        print("Exemples:")
        for opp in detector3_hits[:5]:
            print(f"  {opp['symbol']:8} {opp['date']} : Activation {opp['details']['activation_mult']:.1f}x volume")

# 5. CONSOLIDATION OPPORTUNITÉS
print("\n" + "-"*80)
print("PHASE 2: CONSOLIDATION OPPORTUNITES")
print("-"*80 + "\n")

all_opportunities = detector1_hits + detector2_hits + detector3_hits

print(f"Total opportunites brutes: {len(all_opportunities)}")

# Grouper par (symbol, date) et calculer score composite
composite_scores = defaultdict(lambda: {'detectors': [], 'total_score': 0})

for opp in all_opportunities:
    key = (opp['symbol'], opp['date'])
    detector = opp['detector']
    weight = DETECTORS_CONFIG[detector]['weight']
    weighted_score = opp['score'] * weight
    
    composite_scores[key]['detectors'].append({
        'name': detector,
        'score': opp['score'],
        'weight': weight,
        'weighted_score': weighted_score,
        'details': opp.get('details', {})
    })
    composite_scores[key]['total_score'] += weighted_score

# Créer opportunités finales
final_opportunities = []
for (symbol, date), data in composite_scores.items():
    if data['total_score'] >= 0.20:  # Seuil minimum
        final_opportunities.append({
            'symbol': symbol,
            'detection_date': date,
            'composite_score': round(data['total_score'], 3),
            'detectors': data['detectors'],
            'status': 'ACTIVE',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=7)
        })

# Trier par score
final_opportunities.sort(key=lambda x: x['composite_score'], reverse=True)

print(f"Opportunites finales (score >= 0.20): {len(final_opportunities)}\n")

# 6. SAUVEGARDE
print("-"*80)
print("PHASE 3: SAUVEGARDE")
print("-"*80 + "\n")

if final_opportunities:
    # Clear anciennes opportunités
    old_count = db.opportunities_brvm.count_documents({})
    if old_count > 0:
        db.opportunities_brvm.delete_many({})
        print(f"Anciennes opportunites supprimees: {old_count}")
    
    # Insérer nouvelles
    db.opportunities_brvm.insert_many(final_opportunities)
    print(f"Nouvelles opportunites inserees: {len(final_opportunities)}\n")
    
    # TOP 5 opportunités
    print("TOP 5 OPPORTUNITES:")
    print("-"*80)
    for i, opp in enumerate(final_opportunities[:5], 1):
        print(f"\n{i}. {opp['symbol']} - Score: {opp['composite_score']:.2f}")
        print(f"   Date: {opp['detection_date']}")
        print(f"   Detecteurs:")
        for det in opp['detectors']:
            print(f"     - {det['name']:20} : {det['weighted_score']:.3f} (poids: {det['weight']*100:.0f}%)")
else:
    print("Aucune opportunite detectee")

# Résumé
print("\n" + "="*80)
print("RECAPITULATIF MOTEUR OPPORTUNISTE")
print("="*80 + "\n")

print(f"Detecteurs actifs: {sum(1 for d in DETECTORS_CONFIG.values() if d['enabled'])}/4")
print(f"Opportunites detectees: {len(final_opportunities)}")
print(f"\nRepartition par detecteur:")
print(f"  News silencieuse    : {len(detector1_hits)}")
print(f"  Volume anormal      : {len(detector2_hits)}")
print(f"  Rupture sommeil     : {len(detector3_hits)}")

print(f"\n{'='*80}")
if len(final_opportunities) > 0:
    print("STATUT: MOTEUR OPPORTUNISTE OPERATIONNEL ✓")
    print("\nProchaines etapes:")
    print("  C - Recalculer Top5 avec 17 semaines")
    print("  D - Activer auto-learning")
else:
    print("STATUT: AUCUNE OPPORTUNITE (Normal si marche calme)")

print(f"\n{'='*80}\n")

# Sauvegarder config
with open('MOTEUR_OPPORTUNISTE_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("MOTEUR OPPORTUNISTE DAILY - RESULTATS\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date execution: {datetime.now()}\n\n")
    f.write(f"Detecteurs actifs: {sum(1 for d in DETECTORS_CONFIG.values() if d['enabled'])}/4\n")
    f.write(f"Opportunites detectees: {len(final_opportunities)}\n\n")
    
    if final_opportunities:
        f.write("TOP 10 OPPORTUNITES:\n")
        f.write("-"*80 + "\n")
        for i, opp in enumerate(final_opportunities[:10], 1):
            f.write(f"\n{i}. {opp['symbol']} - Score: {opp['composite_score']:.2f}\n")
            f.write(f"   Date: {opp['detection_date']}\n")
            f.write(f"   Detecteurs: {', '.join(d['name'] for d in opp['detectors'])}\n")

print("Resultats sauvegardes: MOTEUR_OPPORTUNISTE_RESULTS.txt")

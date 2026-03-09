#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTAURATION PROPRE DES DONNÉES BRVM
====================================
Restaure 43 jours manquants dans prices_daily depuis curated_observations
RÈGLE D'OR: prices_daily = SOURCE DE VÉRITÉ (on n'efface jamais)
"""
from pymongo import MongoClient
from datetime import datetime
from collections import Counter
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============================================================================
# CONNEXION UNIQUE centralisation_db
# ============================================================================

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("RESTAURATION DONNEES BRVM - MODE PRODUCTION")
print("="*80 + "\n")

# ============================================================================
# ÉTAPE 1: IDENTIFIER LES JOURS MANQUANTS
# ============================================================================

print("ETAPE 1: IDENTIFICATION DES JOURS MANQUANTS")
print("-"*80)

# Extraire toutes les dates de curated_observations (3 sources BRVM)
sources_brvm = ['BRVM_AGGREGATED', 'BRVM_CSV_HISTORIQUE', 'BRVM_CSV_RESTAURATION']

dates_curated = set()
for source in sources_brvm:
    if source == 'BRVM_AGGREGATED':
        # Champ 'date'
        dates = db.curated_observations.distinct('date', {'source': source})
    else:
        # Champ 'ts'
        dates = db.curated_observations.distinct('ts', {'source': source})
    
    # Convertir en YYYY-MM-DD
    for d in dates:
        if d:
            date_str = str(d)[:10]
            dates_curated.add(date_str)

print(f"Dates dans curated_observations: {len(dates_curated)}")

# Extraire toutes les dates de prices_daily
dates_daily = set(db.prices_daily.distinct('date'))
print(f"Dates dans prices_daily: {len(dates_daily)}")

# Calculer dates manquantes
missing_dates = sorted(list(dates_curated - dates_daily))
print(f"\nJOURS MANQUANTS: {len(missing_dates)}")

if len(missing_dates) == 0:
    print("\nAucune restauration necessaire - donnees completes")
    sys.exit(0)

# Afficher les premiers/derniers
print(f"\nPremiers 10: {', '.join(missing_dates[:10])}")
if len(missing_dates) > 10:
    print(f"Derniers 10: {', '.join(missing_dates[-10:])}")

# Compter par mois
month_counts = Counter()
for date in missing_dates:
    month = date[:7]
    month_counts[month] += 1

print(f"\nRépartition par mois:")
for month in sorted(month_counts.keys()):
    print(f"  {month}: {month_counts[month]:>2} jours")

# ============================================================================
# ÉTAPE 2: EXTRACTION ET NORMALISATION
# ============================================================================

print("\n\nETAPE 2: EXTRACTION & NORMALISATION")
print("-"*80)

stats = {
    'processed_dates': 0,
    'processed_symbols': 0,
    'inserted': 0,
    'updated': 0,
    'skipped_quality': 0,
    'errors': 0
}

def extract_from_aggregated(date_str):
    """Extraire depuis BRVM_AGGREGATED (OHLC complet)"""
    docs = list(db.curated_observations.find({
        'source': 'BRVM_AGGREGATED',
        'date': date_str
    }))
    
    normalized = []
    for doc in docs:
        symbol = doc.get('symbole') or doc.get('ticker')
        if not symbol:
            continue
        
        # Normaliser
        normalized_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': float(doc.get('open') or doc.get('prix_ouverture', 0)),
            'high': float(doc.get('high') or doc.get('prix_haut', 0)),
            'low': float(doc.get('low') or doc.get('prix_bas', 0)),
            'close': float(doc.get('close') or doc.get('prix_cloture', 0)),
            'volume': int(doc.get('volume', 0)),
            'variation_pct': float(doc.get('variation_pct') or doc.get('variation', 0.0)),
            'is_complete': True,
            'is_restored': True,
            'restored_at': datetime.utcnow(),
            'restored_from': 'BRVM_AGGREGATED'
        }
        
        normalized.append(normalized_doc)
    
    return normalized

def extract_from_csv_historique(date_str):
    """Extraire depuis BRVM_CSV_HISTORIQUE (close + volume)"""
    docs = list(db.curated_observations.find({
        'source': 'BRVM_CSV_HISTORIQUE',
        'ts': date_str
    }))
    
    normalized = []
    for doc in docs:
        symbol = doc.get('ticker')
        if not symbol:
            continue
        
        attrs = doc.get('attrs', {})
        close_price = float(doc.get('value') or attrs.get('close', 0))
        
        # Format simplifié (OHLC approximé)
        normalized_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': close_price,    # Approximation
            'high': close_price,    # Approximation
            'low': close_price,     # Approximation
            'close': close_price,
            'volume': int(attrs.get('volume', 0)),
            'variation_pct': float(attrs.get('variation', 0.0)),
            'is_complete': False,   # Pas OHLC réel
            'is_restored': True,
            'restored_at': datetime.utcnow(),
            'restored_from': 'BRVM_CSV_HISTORIQUE'
        }
        
        normalized.append(normalized_doc)
    
    return normalized

def extract_from_csv_restauration(date_str):
    """Extraire depuis BRVM_CSV_RESTAURATION (janvier 2026)"""
    docs = list(db.curated_observations.find({
        'source': 'BRVM_CSV_RESTAURATION',
        'ts': date_str
    }))
    
    normalized = []
    for doc in docs:
        symbol = doc.get('key')
        if not symbol or symbol in ['BRVM', 'BRVM_30', 'BRVM_C', 'BRVM_PRES']:
            continue
        
        attrs = doc.get('attrs', {})
        close_price = float(doc.get('value') or attrs.get('cours', 0))
        open_price = float(attrs.get('ouverture', close_price))
        
        normalized_doc = {
            'symbol': symbol,
            'date': date_str,
            'open': open_price,
            'high': close_price,    # Approximation
            'low': close_price,     # Approximation
            'close': close_price,
            'volume': int(attrs.get('volume', 0)),
            'variation_pct': float(attrs.get('variation_pct', 0.0)),
            'is_complete': False,
            'is_restored': True,
            'restored_at': datetime.utcnow(),
            'restored_from': 'BRVM_CSV_RESTAURATION'
        }
        
        normalized.append(normalized_doc)
    
    return normalized

def validate_quality(doc):
    """Contrôles qualité avant insertion"""
    # Règle 1: high >= low
    if doc['high'] < doc['low']:
        return False, "high < low"
    
    # Règle 2: close > 0
    if doc['close'] <= 0:
        return False, "close <= 0"
    
    # Règle 3: open > 0
    if doc['open'] <= 0:
        return False, "open <= 0"
    
    # Règle 4: prix réaliste < 1M
    if doc['close'] > 1_000_000:
        return False, "close > 1M (aberrant)"
    
    # Règle 5: variation réaliste < 50%
    if abs(doc['variation_pct']) > 50:
        return False, f"variation {doc['variation_pct']}% aberrante"
    
    return True, "OK"

# ============================================================================
# ÉTAPE 3: RESTAURATION DATE PAR DATE
# ============================================================================

print(f"\nETAPE 3: RESTAURATION ({len(missing_dates)} JOURS)")
print("-"*80 + "\n")

for i, date_str in enumerate(missing_dates, 1):
    print(f"[{i}/{len(missing_dates)}] {date_str}")
    
    # Collecter toutes les sources pour cette date
    all_docs = []
    
    # Priorité 1: BRVM_AGGREGATED
    aggregated = extract_from_aggregated(date_str)
    all_docs.extend(aggregated)
    
    # Priorité 2: CSV_HISTORIQUE (si symboles manquants)
    existing_symbols = {d['symbol'] for d in all_docs}
    csv_hist = extract_from_csv_historique(date_str)
    for doc in csv_hist:
        if doc['symbol'] not in existing_symbols:
            all_docs.append(doc)
            existing_symbols.add(doc['symbol'])
    
    # Priorité 3: CSV_RESTAURATION (si symboles manquants)
    csv_resto = extract_from_csv_restauration(date_str)
    for doc in csv_resto:
        if doc['symbol'] not in existing_symbols:
            all_docs.append(doc)
            existing_symbols.add(doc['symbol'])
    
    print(f"  Sources: AGGR({len(aggregated)}) + CSV_HIST({len(csv_hist) - len([d for d in csv_hist if d['symbol'] in existing_symbols])}) + CSV_RESTO({len([d for d in csv_resto if d['symbol'] not in existing_symbols])})")
    print(f"  Total: {len(all_docs)} symboles")
    
    # Insérer avec contrôles qualité
    inserted_count = 0
    skipped_count = 0
    
    for doc in all_docs:
        # Validation qualité
        is_valid, reason = validate_quality(doc)
        if not is_valid:
            print(f"    ⚠  {doc['symbol']}: {reason}")
            stats['skipped_quality'] += 1
            skipped_count += 1
            continue
        
        # Insertion sécurisée (upsert)
        try:
            result = db.prices_daily.update_one(
                {'symbol': doc['symbol'], 'date': doc['date']},
                {'$set': doc},
                upsert=True
            )
            
            if result.upserted_id:
                stats['inserted'] += 1
                inserted_count += 1
            elif result.modified_count > 0:
                stats['updated'] += 1
            
            stats['processed_symbols'] += 1
            
        except Exception as e:
            print(f"    ERREUR {doc['symbol']}: {e}")
            stats['errors'] += 1
    
    print(f"  OK Insérés: {inserted_count} | ⚠  Ignorés: {skipped_count}")
    stats['processed_dates'] += 1

# ============================================================================
# ÉTAPE 4: VÉRIFICATION POST-RESTAURATION
# ============================================================================

print("\n\nETAPE 4: VERIFICATION POST-RESTAURATION")
print("-"*80)

# Compter nouveau total
new_daily_count = db.prices_daily.count_documents({})
new_daily_dates = sorted(db.prices_daily.distinct('date'))
new_daily_symbols = db.prices_daily.distinct('symbol')

print(f"\nprices_daily APRÈS restauration:")
print(f"  Total observations: {new_daily_count:,}")
print(f"  Dates uniques: {len(new_daily_dates)}")
print(f"  Symboles uniques: {len(new_daily_symbols)}")
if new_daily_dates:
    print(f"  Période: {new_daily_dates[0]} → {new_daily_dates[-1]}")

# Vérifier couverture
restored_docs = db.prices_daily.count_documents({'is_restored': True})
print(f"\n  Documents restaurés: {restored_docs}")
print(f"  Documents originaux: {new_daily_count - restored_docs}")

# Calcul période en jours de bourse
from datetime import datetime as dt
if len(new_daily_dates) >= 2:
    first_date = dt.strptime(new_daily_dates[0], '%Y-%m-%d')
    last_date = dt.strptime(new_daily_dates[-1], '%Y-%m-%d')
    total_days = (last_date - first_date).days
    print(f"  Durée calendaire: {total_days} jours")
    print(f"  Jours de bourse: {len(new_daily_dates)}")
    coverage = len(new_daily_dates) / total_days * 100 if total_days > 0 else 0
    print(f"  Couverture: {coverage:.1f}%")

# ============================================================================
# ÉTAPE 5: RÉSUMÉ STATISTIQUES
# ============================================================================

print("\n\nETAPE 5: STATISTIQUES DE RESTAURATION")
print("-"*80)

print(f"\nTraitement:")
print(f"  Dates traitées: {stats['processed_dates']}")
print(f"  Symboles traités: {stats['processed_symbols']}")

print(f"\nRésultats:")
print(f"  OK Insérés: {stats['inserted']}")
print(f"   Mis à jour: {stats['updated']}")
print(f"  ⚠  Ignorés (qualité): {stats['skipped_quality']}")
print(f"  ERREUR Erreurs: {stats['errors']}")

# Taux de succès
total_processed = stats['inserted'] + stats['updated'] + stats['skipped_quality']
if total_processed > 0:
    success_rate = (stats['inserted'] + stats['updated']) / total_processed * 100
    print(f"\n  Taux de succès: {success_rate:.1f}%")

# ============================================================================
# ÉTAPE 6: VALIDATION FINALE
# ============================================================================

print("\n\nETAPE 6: VALIDATION FINALE")
print("-"*80)

validation_ok = True

# Vérif 1: Au moins 65 jours
if len(new_daily_dates) < 65:
    print(f"ERREUR Seulement {len(new_daily_dates)} jours (besoin >= 65)")
    validation_ok = False
else:
    print(f"OK {len(new_daily_dates)} jours (>= 65)")

# Vérif 2: Au moins 60 symboles
if len(new_daily_symbols) < 60:
    print(f"⚠  Seulement {len(new_daily_symbols)} symboles (attendu >= 60)")
else:
    print(f"OK {len(new_daily_symbols)} symboles")

# Vérif 3: Cohérence OHLC
inconsistent = db.prices_daily.count_documents({
    '$expr': {'$gt': ['$low', '$high']}
})
if inconsistent > 0:
    print(f"ERREUR {inconsistent} documents avec low > high")
    validation_ok = False
else:
    print(f"OK Cohérence OHLC vérifiée")

# Vérif 4: Prix aberrants
aberrant_prices = db.prices_daily.count_documents({
    '$or': [
        {'close': {'$lte': 0}},
        {'close': {'$gte': 1000000}}
    ]
})
if aberrant_prices > 0:
    print(f"⚠  {aberrant_prices} prix aberrants détectés")
else:
    print(f"OK Tous les prix sont réalistes")

# ============================================================================
# ÉTAPE 7: INSTRUCTIONS POST-RESTAURATION
# ============================================================================

print("\n\nETAPE 7: PROCHAINES ETAPES OBLIGATOIRES")
print("-"*80)

print("\n⚠  IMPORTANT: Reconstruire WEEKLY maintenant\n")

print("Étape 1: Supprimer ancien WEEKLY")
print("  db.prices_weekly.delete_many({})")

print("\nÉtape 2: Rebuild WEEKLY depuis DAILY restauré")
print("  python brvm_pipeline/pipeline_weekly.py --rebuild")

print("\nÉtape 3: Calculer indicateurs")
print("  python brvm_pipeline/pipeline_weekly.py --indicators")

weeks_estimate = len(new_daily_dates) // 5
print(f"\n Estimation semaines WEEKLY: ~{weeks_estimate}")

if weeks_estimate >= 14:
    print("OK MODE PRODUCTION possible (>= 14 semaines)")
    print("   - RSI(14) calculable")
    print("   - ATR(8) fiable")
    print("   - SMA(5/10) stable")
else:
    print(f"⏳ Mode démarrage ({weeks_estimate}/14 semaines)")
    print("   - Continuer collecte quotidienne")

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print("\n\n" + "="*80)
print("RESTAURATION TERMINÉE")
print("="*80)

if validation_ok:
    print("\nOK SUCCÈS - Toutes les validations passent")
    print(f"   {stats['inserted']} nouvelles observations insérées")
    print(f"   {len(new_daily_dates)} jours disponibles")
    print(f"   Période: {new_daily_dates[0]} → {new_daily_dates[-1]}")
else:
    print("\n⚠  ATTENTION - Certaines validations ont échoué")
    print("   Vérifier les messages ci-dessus")

print("\n📋 Fichiers de logs:")
print("   - Rapport sauvegardé dans ce terminal")
print("   - État MongoDB: centralisation_db.prices_daily")

print("\n Lancer rebuild WEEKLY maintenant:")
print("   python brvm_pipeline/pipeline_weekly.py --rebuild")
print("   python brvm_pipeline/pipeline_weekly.py --indicators")

print("\n" + "="*80 + "\n")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST CALIBRATION ATR BRVM PRO
Vérifier rapidement que la nouvelle formule fonctionne correctement
"""
from pymongo import MongoClient
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("TEST CALIBRATION ATR BRVM PRO")
print("="*80 + "\n")

# Fonctions de test (copie du pipeline)
def is_dead_week(week_data):
    """Détecter semaines mortes"""
    if week_data.get('volume', 0) == 0:
        return True
    
    high = week_data.get('high', 0)
    low = week_data.get('low', 0)
    close = week_data.get('close', 0)
    
    if high == low == close:
        return True
    
    open_price = week_data.get('open', close)
    if open_price > 0:
        variation_pct = abs((close - open_price) / open_price * 100)
        if variation_pct < 0.1:
            return True
    
    return False

def calculate_atr_pct_brvm(weekly_data, period=5):
    """ATR BRVM PRO"""
    if len(weekly_data) < period + 1:
        return None
    
    # Filtrer semaines mortes
    active_weeks = [w for w in weekly_data if not is_dead_week(w)]
    
    if len(active_weeks) < period + 1:
        return None
    
    # Calculer True Range
    true_ranges = []
    for i in range(1, len(active_weeks)):
        high = active_weeks[i].get('high', 0)
        low = active_weeks[i].get('low', 0)
        prev_close = active_weeks[i-1].get('close', 0)
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    # ATR = moyenne 5W
    atr_5w = sum(true_ranges[-period:]) / period
    
    # Normaliser en %
    current_price = active_weeks[-1].get('close', 0)
    
    if current_price <= 0:
        return None
    
    atr_pct = (atr_5w / current_price) * 100
    
    # Plafonner outliers
    if atr_pct > 40:
        return None
    
    return round(atr_pct, 2)

# Tester sur échantillon d'actions
print("Échantillon de calcul ATR:\n")

symbols_test = ['SNTS', 'SGBC', 'BOAC', 'PALC', 'ETIT', 'TTLS', 'BICC', 'ORGT', 'ABJC', 'NEIC']

for symbol in symbols_test:
    # Récupérer historique weekly
    weekly_docs = list(db.prices_weekly.find(
        {'symbol': symbol}
    ).sort('week', 1))
    
    if len(weekly_docs) < 6:
        continue
    
    # Calculer ATR
    atr_pct = calculate_atr_pct_brvm(weekly_docs)
    
    # Récupérer ATR stocké en DB (après recalcul)
    last_week = db.prices_weekly.find_one(
        {'symbol': symbol},
        sort=[('week', -1)]
    )
    
    atr_db = last_week.get('atr_pct') if last_week else None
    tradable = last_week.get('tradable') if last_week else None
    
    # Classification
    if atr_pct:
        if atr_pct < 4:
            cat = "MORT"
        elif atr_pct < 8:
            cat = "LENT"
        elif atr_pct <= 18:
            cat = "IDEAL"
        elif atr_pct <= 28:
            cat = "SPEC"
        else:
            cat = "DANGER"
    else:
        cat = "N/A"
    
    print(f"{symbol:6s}  ATR={atr_pct:>6}%  DB={atr_db:>6}%  [{cat:6s}]  Tradable={tradable}")

# Statistiques globales
print("\n" + "="*80)
print("STATISTIQUES GLOBALES")
print("="*80 + "\n")

# Tous les ATR stockés en DB
all_weekly = list(db.prices_weekly.find({'atr_pct': {'$exists': True, '$ne': None}}))

if all_weekly:
    atr_values = [doc['atr_pct'] for doc in all_weekly if doc.get('atr_pct') is not None]
    
    if atr_values:
        avg_atr = sum(atr_values) / len(atr_values)
        max_atr = max(atr_values)
        min_atr = min(atr_values)
        
        # Compter par catégorie
        dead = len([a for a in atr_values if a < 4])
        slow = len([a for a in atr_values if 4 <= a < 8])
        ideal = len([a for a in atr_values if 8 <= a <= 18])
        spec = len([a for a in atr_values if 18 < a <= 28])
        danger = len([a for a in atr_values if a > 28])
        
        print(f"Total observations: {len(atr_values):,}")
        print(f"ATR moyen: {avg_atr:.2f}%")
        print(f"ATR min: {min_atr:.2f}%")
        print(f"ATR max: {max_atr:.2f}%")
        print()
        print("Distribution:")
        print(f"  Marche mort (<4%):    {dead:4d} ({dead/len(atr_values)*100:.1f}%)")
        print(f"  Lent (4-8%):          {slow:4d} ({slow/len(atr_values)*100:.1f}%)")
        print(f"  IDEAL (8-18%):        {ideal:4d} ({ideal/len(atr_values)*100:.1f}%)")
        print(f"  Speculatif (18-28%):  {spec:4d} ({spec/len(atr_values)*100:.1f}%)")
        print(f"  Dangereux (>28%):     {danger:4d} ({danger/len(atr_values)*100:.1f}%)")
        print()
        
        # Validation finale
        print("="*80)
        print("VALIDATION FINALE")
        print("="*80)
        
        if 6 <= avg_atr <= 14:
            print(f"OK ATR moyen univers: {avg_atr:.2f}% (entre 6% et 14%)")
        else:
            print(f"ATTENTION ATR moyen: {avg_atr:.2f}% (hors plage 6-14%)")
        
        if max_atr < 25:
            print(f"OK Max ATR: {max_atr:.2f}% (< 25%)")
        else:
            print(f"ATTENTION Max ATR: {max_atr:.2f}% (>= 25%)")
        
        outliers = len([a for a in atr_values if a > 40])
        if outliers == 0:
            print(f"OK Aucun ATR > 40%")
        else:
            print(f"ATTENTION {outliers} ATR > 40% (calcul casse)")
        
        # Tradables
        tradable_count = db.prices_weekly.count_documents({'tradable': True})
        total_count = db.prices_weekly.count_documents({})
        
        print()
        print(f"Actions tradables (ATR 6-25%): {tradable_count}/{total_count} ({tradable_count/total_count*100:.1f}%)")

print("\n" + "="*80 + "\n")

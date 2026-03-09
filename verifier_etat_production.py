#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VÉRIFICATION ÉTAT PRODUCTION - BRVM
====================================
Vérifier que toutes les données sont prêtes pour mode PRODUCTION
"""
from pymongo import MongoClient
from datetime import datetime
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("VERIFICATION ETAT PRODUCTION - BRVM")
print("="*80 + "\n")

# 1. PRICES_DAILY
daily_count = db.prices_daily.count_documents({})
daily_dates = sorted(db.prices_daily.distinct('date'))
daily_symbols = db.prices_daily.distinct('symbol')

print("1. PRICES_DAILY (Source de verite)")
print("-"*80)
print(f"Observations: {daily_count:,}")
print(f"Dates: {len(daily_dates)} jours")
print(f"Symboles: {len(daily_symbols)}")
if daily_dates:
    print(f"Periode: {daily_dates[0]} -> {daily_dates[-1]}")

# Vérifier données restaurées
restored_count = db.prices_daily.count_documents({'is_restored': True})
print(f"Donnees restaurees: {restored_count:,}")

status_daily = "OK" if len(daily_dates) >= 65 else "INCOMPLET"
print(f"\nStatut: {status_daily} {'✓' if status_daily == 'OK' else '✗'}")

# 2. PRICES_WEEKLY
weekly_count = db.prices_weekly.count_documents({})
weekly_weeks = sorted([w for w in db.prices_weekly.distinct('week') if w])
weekly_symbols = db.prices_weekly.distinct('symbol')

print(f"\n2. PRICES_WEEKLY (Indicateurs)")
print("-"*80)
print(f"Observations: {weekly_count:,}")
print(f"Semaines: {len(weekly_weeks)}")
if weekly_weeks:
    print(f"Periode: {weekly_weeks[0]} -> {weekly_weeks[-1]}")
print(f"Symboles: {len(weekly_symbols)}")

# Indicateurs calculés
with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
print(f"Avec indicateurs: {with_indicators}/{weekly_count}")

status_weekly = "OK" if len(weekly_weeks) >= 14 else "INSUFFISANT"
print(f"\nStatut: {status_weekly} {'✓' if status_weekly == 'OK' else '✗'}")

# 3. QUALITÉ ATR/VOLATILITÉ
print(f"\n3. QUALITE INDICATEURS")
print("-"*80)

if with_indicators > 0:
    # Échantillon ATR
    sample_atr = list(db.prices_weekly.find(
        {'indicators_computed': True, 'atr_pct': {'$exists': True}},
        {'symbol': 1, 'week': 1, 'atr_pct': 1, 'volatility': 1}
    ).limit(10))
    
    if sample_atr:
        atr_values = [doc.get('atr_pct', 0) for doc in sample_atr if doc.get('atr_pct')]
        vol_values = [doc.get('volatility', 0) for doc in sample_atr if doc.get('volatility')]
        
        if atr_values:
            avg_atr = sum(atr_values) / len(atr_values)
            max_atr = max(atr_values)
            print(f"ATR moyen: {avg_atr:.2f}%")
            print(f"ATR max: {max_atr:.2f}%")
            
            atr_status = "OK" if 5 <= avg_atr <= 18 else "ANORMAL"
            print(f"Statut ATR: {atr_status} {'✓' if atr_status == 'OK' else '✗'}")
        
        if vol_values:
            avg_vol = sum(vol_values) / len(vol_values)
            max_vol = max(vol_values)
            print(f"\nVolatilite moyenne: {avg_vol:.2f}%")
            print(f"Volatilite max: {max_vol:.2f}%")
            
            vol_status = "OK" if max_vol <= 35 else "ANORMAL"
            print(f"Statut Volatilite: {vol_status} {'✓' if vol_status == 'OK' else '✗'}")

# 4. TOP5
top5_count = db.top5_weekly_brvm.count_documents({})
print(f"\n4. TOP5 HEBDOMADAIRE")
print("-"*80)
print(f"TOP5 generes: {top5_count} semaines")

if top5_count > 0:
    top5_weeks = sorted([w for w in db.top5_weekly_brvm.distinct('week') if w])
    print(f"Semaines avec TOP5: {', '.join(top5_weeks) if len(top5_weeks) <= 5 else f'{top5_weeks[0]} ... {top5_weeks[-1]}'}")

# 5. OPPORTUNITÉS
opp_count = db.opportunities_brvm.count_documents({})
print(f"\n5. OPPORTUNITES")
print("-"*80)
print(f"Opportunites detectees: {opp_count}")

# 6. SYNTHÈSE MODE
print(f"\n" + "="*80)
print("SYNTHESE - READINESS PRODUCTION")
print("="*80 + "\n")

checks = {
    "DAILY >= 65 jours": len(daily_dates) >= 65,
    "WEEKLY >= 14 semaines": len(weekly_weeks) >= 14,
    "Indicateurs calcules": with_indicators > 0,
    "ATR coherent (5-18%)": False,  # À déterminer
    "Volatilite < 35%": False  # À déterminer
}

# Vérifier ATR et Vol
if sample_atr and atr_values and vol_values:
    checks["ATR coherent (5-18%)"] = 5 <= avg_atr <= 18
    checks["Volatilite < 35%"] = max_vol <= 35

all_ok = all(checks.values())

for check, status in checks.items():
    print(f"{'✓' if status else '✗'} {check}")

print(f"\n{'='*80}")
if all_ok:
    print("STATUS: PRET POUR PRODUCTION ✓")
    print("="*80)
    print("\nPROCHAINES ETAPES:")
    print("  A - Recalibrer ATR BRVM (mode production)")
    print("  B - Rebuild moteur opportuniste daily")
    print("  C - Recalculer Top5 avec 14 semaines")
    print("  D - Activer auto-learning")
else:
    print("STATUS: PREPARATION INCOMPLETE ✗")
    print("="*80)
    print("\nACTIONS REQUISES:")
    if not checks["DAILY >= 65 jours"]:
        print(f"  - Restaurer DAILY (actuellement {len(daily_dates)} jours)")
    if not checks["WEEKLY >= 14 semaines"]:
        print(f"  - Rebuild WEEKLY (actuellement {len(weekly_weeks)} semaines)")
    if not checks["Indicateurs calcules"]:
        print("  - Calculer indicateurs WEEKLY")
    if not checks["ATR coherent (5-18%)"]:
        print("  - Recalibrer ATR (anormal detecte)")
    if not checks["Volatilite < 35%"]:
        print("  - Corriger calcul volatilite")

print(f"\n{'='*80}\n")

# Sauvegarder rapport
with open('ETAT_PRODUCTION_BRVM.txt', 'w', encoding='utf-8') as f:
    f.write("ETAT PRODUCTION BRVM\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date verification: {datetime.now()}\n\n")
    f.write(f"DAILY: {daily_count:,} obs, {len(daily_dates)} jours\n")
    f.write(f"WEEKLY: {weekly_count:,} obs, {len(weekly_weeks)} semaines\n")
    f.write(f"Indicateurs: {with_indicators}/{weekly_count}\n")
    f.write(f"TOP5: {top5_count} semaines\n")
    f.write(f"Opportunites: {opp_count}\n\n")
    
    f.write("CHECKS:\n")
    for check, status in checks.items():
        f.write(f"  {'✓' if status else '✗'} {check}\n")
    
    f.write(f"\nSTATUS: {'PRET' if all_ok else 'INCOMPLET'}\n")

print("Rapport sauvegarde: ETAT_PRODUCTION_BRVM.txt")

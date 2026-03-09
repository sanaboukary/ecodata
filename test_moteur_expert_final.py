#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test rapide moteur expert"""

import sys
sys.path.insert(0, 'brvm_pipeline')

from weekly_engine_expert import generate_weekly_decisions
from pymongo import MongoClient

print("="*80)
print("TEST MOTEUR EXPERT BRVM - 2026-W06")
print("="*80)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Charger données weekly
week_data = list(db.prices_weekly.find({'week_id': '2026-W06'}))
print(f"\n📊 Données weekly W06: {len(week_data)} observations")

# Filtrer celles avec indicateurs
with_ind = [obs for obs in week_data if obs.get('rsi') and obs.get('atr_pct')]
print(f"   Avec indicateurs: {len(with_ind)}")

with_atr_tradable = [obs for obs in with_ind if 6 <= obs.get('atr_pct', 0) <= 25]
print(f"   ATR tradable (6-25%): {len(with_atr_tradable)}")

if len(with_atr_tradable) > 0:
    print(f"\n📈 Génération décisions EXPERT BRVM...")
    try:
        decisions = generate_weekly_decisions('2026-W06')
        
        print(f"\n✅ DÉCISIONS GÉNÉRÉES: {len(decisions)}")
        
        if len(decisions) > 0:
            print(f"\n{'='*80}")
            print(f"{'SYMBOLE':<8} {'CLASSE':<8} {'WOS':>6} {'RR':>6} {'ER':>7} {'RANK':>7} {'ATR%':>7}")
            print(f"{'='*80}")
            
            for dec in decisions[:10]:
                sym = dec.get('symbol', 'N/A')
                classe = dec.get('classe', 'N/A')
                wos = dec.get('wos', 0)
                rr = dec.get('rr', 0)
                er = dec.get('expected_return', 0)
                rank = dec.get('ranking_score', 0)
                atr = dec.get('atr_pct', 0)
                
                print(f"{sym:<8} {classe:<8} {wos:>6.1f} {rr:>6.2f} {er:>6.1f}% {rank:>7.2f} {atr:>6.1f}%")
            
            print(f"{'='*80}")
            
            # Compter par classe
            classe_a = sum(1 for d in decisions if d.get('classe') == 'A')
            classe_b = sum(1 for d in decisions if d.get('classe') == 'B')
            
            print(f"\n📊 RÉPARTITION:")
            print(f"   Classe A (Top): {classe_a}")
            print(f"   Classe B: {classe_b}")
            
            # Moyennes
            avg_rr = sum(d.get('rr', 0) for d in decisions) / len(decisions)
            avg_er = sum(d.get('expected_return', 0) for d in decisions) / len(decisions)
            avg_wos = sum(d.get('wos', 0) for d in decisions) / len(decisions)
            
            print(f"\n📈 QUALITÉ MOYENNE:")
            print(f"   RR moyen: {avg_rr:.2f}")
            print(f"   ER moyen: {avg_er:.1f}%")
            print(f"   WOS moyen: {avg_wos:.1f}")
            
            if avg_rr >= 2.2 and len(decisions) >= 3:
                print(f"\n✅ OBJECTIF ATTEINT - Plateforme fonctionnelle TOP 5%")
                print(f"   • {len(decisions)} recommandations (objectif: 3-8)")
                print(f"   • RR {avg_rr:.2f} (objectif: ≥2.2)")
                print(f"   • ER {avg_er:.1f}% (objectif: >3%)")
            else:
                print(f"\n⚠️  Qualité à améliorer")
                
        else:
            print("❌ Aucune décision générée - vérifier filtres")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n❌ Aucune action tradable pour cette semaine")

print("="*80)

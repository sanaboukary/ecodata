#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Générateur recommandations BRVM - TOLÉRANCE ZÉRO
Pour gros clients - Qualité maximale uniquement
"""

import sys
sys.path.insert(0, 'brvm_pipeline')

from weekly_engine_expert import generate_weekly_decisions
from pymongo import MongoClient
from datetime import datetime

print("="*80)
print("MODE EXPERT BRVM - GÉNÉRATION RECOMMANDATIONS")
print("TOLÉRANCE ZÉRO - QUALITÉ MAXIMALE POUR GROS CLIENTS")
print("="*80)

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Dernière semaine disponible
weeks = sorted(db.prices_weekly.distinct('week'))
if not weeks:
    print("\n❌ ERREUR : Aucune donnée weekly disponible")
    print("   → Exécuter rebuild_weekly_direct.py d'abord")
    exit(1)

last_week = weeks[-1]
print(f"\n📅 Semaine à analyser : {last_week}")
print(f"   Semaines disponibles : {len(weeks)} ({weeks[0]} → {last_week})")

# Vérifier données weekly
week_data = list(db.prices_weekly.find({'week': last_week}))
print(f"\n📊 Données weekly {last_week} : {len(week_data)} observations")

if len(week_data) == 0:
    print("\n❌ ERREUR : Aucune observation pour cette semaine")
    exit(1)

# Vérifier ATR
with_atr = [obs for obs in week_data if (obs.get('atr_pct') or 0) > 0]
tradable = [obs for obs in with_atr if 6 <= (obs.get('atr_pct') or 0) <= 25]

print(f"   Avec ATR calculé : {len(with_atr)}/{len(week_data)}")
print(f"   Tradables (6-25%) : {len(tradable)}/{len(week_data)}")

if len(tradable) == 0:
    print("\n⚠️  AUCUNE action tradable cette semaine")
    print("   RECOMMANDATION : Attendre semaine prochaine (TOLÉRANCE ZÉRO)")
    exit(0)

# Afficher actions tradables
print(f"\n📈 Actions tradables (ATR 6-25%) :")
for obs in sorted(tradable, key=lambda x: x.get('atr_pct', 0)):
    sym = obs.get('symbol', 'N/A')
    atr = obs.get('atr_pct', 0)
    rsi = obs.get('rsi', 0)
    vol = obs.get('volume', 0)
    print(f"   {sym:6} | ATR:{atr:6.2f}% | RSI:{rsi:5.1f} | Vol:{vol:>10,}")

# Génération décisions
print("\n" + "="*80)
print("GÉNÉRATION RECOMMANDATIONS EXPERT...")
print("="*80)

try:
    decisions = generate_weekly_decisions(last_week)
    
    if not decisions or len(decisions) == 0:
        print("\n⚠️  FILTRES STRICTS : Aucune recommandation cette semaine")
        print("\n💡 TOLÉRANCE ZÉRO pour gros clients :")
        print("   → Mieux AUCUNE recommandation qu'une MAUVAISE recommandation")
        print("   → Les filtres ont éliminé toutes les actions (qualité insuffisante)")
        print("   → Attendre opportunités de meilleure qualité la semaine prochaine")
        
    else:
        print(f"\n✅ SUCCÈS : {len(decisions)} recommandations générées")
        
        # Validation qualité STRICTE
        print("\n" + "="*80)
        print("VALIDATION QUALITÉ - TOLÉRANCE ZÉRO")
        print("="*80)
        
        # Statistiques
        classe_a = [d for d in decisions if d.get('classe') == 'A']
        classe_b = [d for d in decisions if d.get('classe') == 'B']
        
        avg_rr = sum(d.get('risk_reward', 0) for d in decisions) / len(decisions)
        avg_er = sum(d.get('expected_return', 0) for d in decisions) / len(decisions)
        avg_wos = sum(d.get('wos', 0) for d in decisions) / len(decisions)
        min_rr = min(d.get('risk_reward', 0) for d in decisions)
        min_er = min(d.get('expected_return', 0) for d in decisions)
        
        print(f"\n📊 RÉPARTITION :")
        print(f"   Classe A (Excellence) : {len(classe_a)}")
        print(f"   Classe B (Qualité)    : {len(classe_b)}")
        
        print(f"\n📈 QUALITÉ MOYENNE :")
        print(f"   RR moyen     : {avg_rr:.2f} (min: {min_rr:.2f})")
        print(f"   ER moyen     : {avg_er:.1f}% (min: {min_er:.1f}%)")
        print(f"   WOS moyen    : {avg_wos:.1f}")
        
        # Alertes qualité
        warnings = []
        
        if avg_rr < 2.3:
            warnings.append(f"⚠️  RR moyen {avg_rr:.2f} < 2.3 (objectif)")
        
        if min_rr < 2.0:
            warnings.append(f"⚠️  RR minimum {min_rr:.2f} < 2.0 (risque élevé)")
        
        if avg_er < 5.0:
            warnings.append(f"⚠️  ER moyen {avg_er:.1f}% < 5% (gain faible)")
        
        if len(decisions) > 10:
            warnings.append(f"⚠️  Trop de recommandations ({len(decisions)} > 10) - Dilution qualité")
        
        if len(classe_a) == 0:
            warnings.append(f"⚠️  Aucune classe A - Pas d'excellence cette semaine")
        
        if warnings:
            print(f"\n⚠️  ALERTES QUALITÉ ({len(warnings)}) :")
            for w in warnings:
                print(f"   {w}")
            
            print(f"\n💡 CONSEIL TOLÉRANCE ZÉRO :")
            print(f"   → Recommander UNIQUEMENT classe A (excellence)")
            print(f"   → Ignorer classe B cette semaine (qualité insuffisante)")
        else:
            print(f"\n✅ QUALITÉ VALIDÉE - Toutes métriques au-dessus des seuils")
        
        # Affichage recommandations
        print("\n" + "="*80)
        print(f"TOP RECOMMANDATIONS - {last_week}")
        print("="*80)
        print(f"\n{'#':<3} {'SYMBOLE':<8} {'CL':<3} {'WOS':<6} {'RR':<6} {'ER%':<6} {'STOP%':<7} {'TARGET%':<8} {'ATR%':<7}")
        print("-"*80)
        
        for i, dec in enumerate(decisions[:10], 1):
            sym = dec.get('symbol', '')
            classe = dec.get('classe', '')
            wos = dec.get('wos', 0)
            rr = dec.get('risk_reward', 0)
            er = dec.get('expected_return', 0)
            stop = dec.get('stop_pct', 0)
            target = dec.get('target_pct', 0)
            atr = dec.get('atr_pct', 0)
            
            # Marqueur qualité
            marker = "🟢" if classe == 'A' else "🟡"
            
            print(f"{i:<3} {sym:<8} {classe:<3} {wos:<6.1f} {rr:<6.2f} {er:<6.1f} {stop:<7.1f} {target:<8.1f} {atr:<7.1f} {marker}")
        
        # Conseil exécution
        print("\n" + "="*80)
        print("CONSEIL EXÉCUTION - GROS CLIENTS")
        print("="*80)
        
        if len(classe_a) > 0:
            print(f"\n✅ RECOMMANDATION PRINCIPALE :")
            print(f"   → Exécuter UNIQUEMENT classe A : {classe_a[0].get('symbol')} (Top 1)")
            print(f"   → RR = {classe_a[0].get('risk_reward'):.2f}, ER = {classe_a[0].get('expected_return'):.1f}%")
            print(f"   → Stop = {classe_a[0].get('stop_pct'):.1f}%, Target = {classe_a[0].get('target_pct'):.1f}%")
        else:
            print(f"\n⚠️  AUCUNE classe A disponible")
            if len(classe_b) > 0:
                print(f"   → Option : Classe B top 1 ({classe_b[0].get('symbol')})")
                print(f"   → Mais qualité en-dessous de l'excellence")
                print(f"   → CONSEIL : Attendre meilleure opportunité")
        
        print(f"\n💡 RÈGLE TOLÉRANCE ZÉRO :")
        print(f"   • MAX 1-2 positions simultanées")
        print(f"   • Privilégier classe A uniquement")
        print(f"   • Si doute → NE PAS EXÉCUTER")
        print(f"   • Stop loss OBLIGATOIRE (non négociable)")
        
        # Sauvegarde
        print(f"\n📁 Sauvegarde MongoDB :")
        print(f"   Collection : decisions_brvm_weekly")
        print(f"   Décisions  : {len(decisions)} enregistrées")
        print(f"   Date       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
except Exception as e:
    print(f"\n❌ ERREUR lors de la génération :")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("✅ GÉNÉRATION TERMINÉE")
print("="*80)

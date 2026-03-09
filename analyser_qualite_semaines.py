#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE QUALITE SEMAINES - MODE PRO
====================================
Identifie les semaines avec donnees de qualite professionnelle
Critere: ≥70% des actions avec historique suffisant (≥14 semaines)
"""

import os, sys
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("=" * 80)
print("ANALYSE QUALITE SEMAINES - EXPERTISE PROFESSIONNELLE")
print("=" * 80)

# Recuperer toutes les semaines
all_weeks = sorted(db.prices_weekly.distinct('week'))
print(f"\nSemaines disponibles: {len(all_weeks)}")
print(f"  Premiere: {all_weeks[0]}")
print(f"  Derniere: {all_weeks[-1]}")

# Analyser chaque semaine
quality_by_week = {}

print("\n" + "=" * 80)
print("ANALYSE PAR SEMAINE")
print("=" * 80)
print(f"{'Semaine':<12} {'Actions':<8} {'Avec Indic':<12} {'%':<8} {'Qualite':<10}")
print("-" * 80)

for week in all_weeks:
    # Compter actions dans cette semaine
    total_actions = db.prices_weekly.count_documents({'week': week})
    
    # Compter actions avec indicateurs dans cette semaine
    with_indicators = db.prices_weekly.count_documents({
        'week': week,
        'indicators_computed': True
    })
    
    pct = (100 * with_indicators / total_actions) if total_actions > 0 else 0
    
    # Classification qualite
    if pct >= 90:
        quality = "EXCELLENT"
    elif pct >= 70:
        quality = "BON"
    elif pct >= 50:
        quality = "MOYEN"
    else:
        quality = "FAIBLE"
    
    quality_by_week[week] = {
        'total': total_actions,
        'with_indicators': with_indicators,
        'pct': pct,
        'quality': quality
    }
    
    print(f"{week:<12} {total_actions:<8} {with_indicators:<12} {pct:>6.1f}% {quality:<10}")

# Statistiques globales
print("\n" + "=" * 80)
print("STATISTIQUES GLOBALES")
print("=" * 80)

excellent = [w for w, d in quality_by_week.items() if d['quality'] == 'EXCELLENT']
bon = [w for w, d in quality_by_week.items() if d['quality'] == 'BON']
moyen = [w for w, d in quality_by_week.items() if d['quality'] == 'MOYEN']
faible = [w for w, d in quality_by_week.items() if d['quality'] == 'FAIBLE']

print(f"\nEXCELLENT (≥90%)  : {len(excellent)} semaines")
if excellent:
    print(f"  → {', '.join(excellent)}")

print(f"\nBON (70-89%)      : {len(bon)} semaines")
if bon:
    print(f"  → {', '.join(bon)}")

print(f"\nMOYEN (50-69%)    : {len(moyen)} semaines")
if moyen:
    print(f"  → {', '.join(moyen)}")

print(f"\nFAIBLE (<50%)     : {len(faible)} semaines")
if faible:
    print(f"  → {', '.join(faible)}")

# Recommandation professionnelle
print("\n" + "=" * 80)
print("RECOMMANDATION PROFESSIONNELLE")
print("=" * 80)

semaines_pro = excellent + bon
print(f"\nSEMAINES DE QUALITE PRO (≥70%): {len(semaines_pro)}")
print(f"  → {', '.join(semaines_pro) if semaines_pro else 'Aucune'}\n")

if len(semaines_pro) >= 8:
    print("[EXCELLENT] Vous avez ≥8 semaines de qualite PRO")
    print("            Historique suffisant pour analyse technique complete")
elif len(semaines_pro) >= 5:
    print("[BON] Vous avez ≥5 semaines de qualite PRO")
    print("      Suffisant pour analyse avec indicateurs adaptatifs")
else:
    print("[ATTENTION] Moins de 5 semaines de qualite PRO")
    print("            Continuer la collecte de donnees")

# Calcul historique disponible pour derniere semaine PRO
if semaines_pro:
    derniere_semaine_pro = semaines_pro[-1]
    index_derniere = all_weeks.index(derniere_semaine_pro)
    historique_disponible = index_derniere + 1
    
    print(f"\nDERNIERE SEMAINE PRO: {derniere_semaine_pro}")
    print(f"  Historique disponible: {historique_disponible} semaines")
    
    if historique_disponible >= 14:
        print(f"  [OK] ≥14 semaines → RSI(14), SMA(10) calculables")
    elif historique_disponible >= 7:
        print(f"  [!!] ≥7 semaines → Mode adaptatif requis")
    else:
        print(f"  [!] <7 semaines → Historique insuffisant")

print("\n" + "=" * 80)
print("PROCHAINES ETAPES")
print("=" * 80)

if semaines_pro:
    print("\n1. Configurer le systeme pour analyser UNIQUEMENT:")
    print(f"   {', '.join(semaines_pro)}")
    print("\n2. Recalculer indicateurs sur ces semaines de qualite")
    print("\n3. Executer pipeline_brvm.py")
    print("\n4. Generer recommandations fiables")
else:
    print("\n1. Continuer collecte de donnees")
    print("2. Recalculer tous les indicateurs")
    print("3. Attendre 14+ semaines pour qualite optimale")

print("\n" + "=" * 80)

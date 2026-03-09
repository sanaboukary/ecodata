#!/usr/bin/env python3
"""
Diagnostic Complet Système BRVM
================================

Vérifie état de toutes les collections et pipeline
"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

print("\n" + "="*80)
print(" DIAGNOSTIC SYSTEME BRVM ".center(80))
print("="*80)
print(f" Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("="*80 + "\n")

# 1. Analyses
analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
print(f"[1/4] ANALYSES TECHNIQUES (curated_observations)")
print("-" * 80)
print(f"  Total documents : {len(analyses)}")
if analyses:
    signals = {}
    for a in analyses:
        signal = a.get("attrs", {}).get("signal", "UNKNOWN")
        signals[signal] = signals.get(signal, 0) + 1
    
    print(f"  Distribution signaux :")
    for sig, count in sorted(signals.items(), key=lambda x: -x[1]):
        print(f"    - {sig:6} : {count:2}")
    
    # Exemple analyse
    exemple = analyses[0].get("attrs", {})
    print(f"\n  Exemple (premier document) :")
    print(f"    Symbol       : {exemple.get('symbol', 'N/A')}")
    print(f"    Signal       : {exemple.get('signal', 'N/A')}")
    print(f"    Score        : {exemple.get('score', 'N/A')}")
    print(f"    Volatility   : {exemple.get('volatility', 'N/A')}")
    print(f"    Prix actuel  : {exemple.get('prix_actuel', 'N/A')}")
else:
    print("  [ALERTE] Aucune analyse disponible !")
    print("  Action : Executer analyse_ia_simple.py")

print()

# 2. Décisions
decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))
print(f"[2/4] DECISIONS BUY (decisions_finales_brvm)")
print("-" * 80)
print(f"  Total decisions : {len(decisions)}")
if decisions:
    classes = {}
    for d in decisions:
        classe = d.get("classe", "?")
        classes[classe] = classes.get(classe, 0) + 1
    
    print(f"  Distribution classes :")
    for cls, count in sorted(classes.items()):
        print(f"    - Classe {cls} : {count}")
    
    print(f"\n  Liste decisions :")
    for d in decisions:
        sym = d.get("symbol", "?")
        cls = d.get("classe", "?")
        conf = d.get("confidence", 0)
        wos = d.get("wos", 0)
        rr = d.get("rr", 0)
        gain = d.get("gain_attendu", 0)
        print(f"    {sym:6} | Classe {cls} | Conf {conf:4.0f}% | WOS {wos:4.1f} | RR {rr:.2f} | Gain {gain:4.1f}%")
else:
    print("  [ALERTE] Aucune decision generee !")
    print("  Action : Executer decision_finale_brvm.py")

print()

# 3. TOP5
top5 = list(db.top5_weekly_brvm.find().sort([("rank", 1)]))
print(f"[3/4] TOP5 WEEKLY (top5_weekly_brvm)")
print("-" * 80)
print(f"  Total TOP5 : {len(top5)}")
if top5:
    print(f"\n  Classement :")
    for t in top5:
        rank = t.get("rank", 0)
        sym = t.get("symbol", "?")
        cls = t.get("classe", "?")
        score = t.get("top5_score", 0)
        conf = t.get("confidence", 0)
        gain = t.get("gain_attendu", 0)
        print(f"    #{rank} {sym:6} | Classe {cls} | Score {score:5.1f} | Conf {conf:4.0f}% | Gain {gain:4.1f}%")
else:
    print("  [ALERTE] Aucun TOP5 genere !")
    print("  Action : Executer top5_engine_final.py")

print()

# 4. Track Record
week_id = datetime.now().strftime("%Y-W%U")
track = list(db.track_record_weekly.find({"week_id": week_id}))
print(f"[4/4] TRACK RECORD (track_record_weekly)")
print("-" * 80)
print(f"  Semaine courante : {week_id}")
print(f"  Recommandations figees : {len(track)}")
if track:
    print(f"\n  Details :")
    for t in track:
        sym = t.get("symbol", "?")
        statut = t.get("statut", "?")
        figee = t.get("figee_le")
        figee_str = figee.strftime("%d/%m %H:%M") if figee else "N/A"
        print(f"    {sym:6} | {statut:10} | Figee: {figee_str}")
else:
    print("  [INFO] Aucune recommandation figee pour cette semaine")
    print("  Action : Executer workflow_production_django.py")

print()

# 5. État général
print("="*80)
print(" ETAT GENERAL ".center(80))
print("="*80)

statut_pipeline = "OK"
alertes = []

if not analyses:
    statut_pipeline = "CRITIQUE"
    alertes.append("Aucune analyse technique")
elif len(analyses) < 10:
    statut_pipeline = "DEGRADE"
    alertes.append(f"Peu d'analyses ({len(analyses)} < 10)")

if not decisions:
    statut_pipeline = "CRITIQUE"
    alertes.append("Aucune decision generee")

if not top5:
    if statut_pipeline == "OK":
        statut_pipeline = "DEGRADE"
    alertes.append("TOP5 non genere")

if decisions:
    wos_moyen = sum(d.get("wos", 0) for d in decisions) / len(decisions)
    if wos_moyen < 50:
        if statut_pipeline == "OK":
            statut_pipeline = "DEGRADE"
        alertes.append(f"WOS moyen faible ({wos_moyen:.1f} < 50) - Enrichir donnees")

print(f"  Statut pipeline : {statut_pipeline}")
if alertes:
    print(f"\n  Alertes :")
    for alerte in alertes:
        print(f"    - {alerte}")
else:
    print(f"  Aucune alerte - Systeme operationnel")

print()

# 6. Recommandations
print("="*80)
print(" RECOMMANDATIONS ".center(80))
print("="*80)

if statut_pipeline == "CRITIQUE":
    print("  1. Regenerer analyses : .venv/Scripts/python.exe analyse_ia_simple.py")
    print("  2. Lancer workflow    : .venv/Scripts/python.exe workflow_production_django.py")
elif statut_pipeline == "DEGRADE":
    if not top5:
        print("  1. Generer TOP5    : .venv/Scripts/python.exe top5_engine_final.py")
        print("  2. Figer semaine   : .venv/Scripts/python.exe workflow_production_django.py")
    elif wos_moyen < 50:
        print("  1. Enrichir donnees (prix historiques, SMA, RSI)")
        print("  2. Regenerer workflow complet")
else:
    print("  Systeme operationnel - Dashboard disponible dans dashboard_output.txt")
    if not track:
        print("  Optionnel : Figer semaine pour track record")

print("\n" + "="*80 + "\n")

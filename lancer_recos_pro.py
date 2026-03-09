#!/usr/bin/env python3
"""
LAUNCHER RECOMMANDATIONS PRO — Formule restaurée 07/02/2026
============================================================
Pipeline : analyse_ia → decision_finale → top5
Formule  : stop = 0.9 × ATR | target = 2.4 × ATR | RR ≈ 2.67
"""

import subprocess
import sys
import os
from datetime import datetime

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def safe_print(text):
    """Affiche du texte en gérant les problèmes d'encodage Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

def run(script, label):
    safe_print(f"\n{'='*60}")
    safe_print(f"  {label}")
    safe_print(f"{'='*60}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [PYTHON, os.path.join(BASE_DIR, script)],
        capture_output=True, text=True,
        encoding='utf-8', errors='replace',
        env=env
    )
    if result.stdout:
        safe_print(result.stdout)
    if result.returncode != 0:
        safe_print(f"[ERREUR] {result.stderr[-500:] if result.stderr else 'inconnue'}")
        return False
    return True

def verifier_donnees():
    """Vérifie que les données prices_weekly sont disponibles (source principale)."""
    try:
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = c["centralisation_db"]

        n_weekly = db.prices_weekly.count_documents({})
        symbols_weekly = db.prices_weekly.distinct("symbol")
        last_week = db.prices_weekly.find_one(sort=[("week", -1)])
        semaine = last_week["week"] if last_week else "N/A"

        print(f"  prices_weekly   : {n_weekly:,} docs | {len(symbols_weekly)} symboles | dernière : {semaine}")

        if n_weekly < 10:
            print("  [BLOQUANT] Pas assez de données prices_weekly.")
            print("  → Lancez d'abord : .venv/Scripts/python.exe build_weekly.py")
            return False

        n_daily = db.prices_daily.count_documents({})
        print(f"  prices_daily    : {n_daily:,} docs (référence secondaire)")

        return True

    except Exception as e:
        print(f"  [ERREUR] MongoDB inaccessible : {e}")
        print("  → Vérifiez que MongoDB est démarré.")
        return False

def afficher_top5():
    """Affiche le TOP5 généré avec sizing, liquidité et timing intraday."""
    try:
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/")
        db = c["centralisation_db"]

        top5 = list(db.top5_weekly_brvm.find({}, {"_id": 0}).sort("rank", 1))

        if not top5:
            print("\n  Aucune recommandation générée.")
            return

        print(f"\n{'='*70}")
        print("  TOP 5 RECOMMANDATIONS BRVM | Horizon : 4-8 semaines")
        print(f"{'='*70}")
        print(f"  {'#':<3} {'Symbol':<6} {'Cl.':<4} {'Entrée':>9} {'Gain':>7} {'Stop':>7} {'WOS':>5} {'ATR%':>5} {'RR':>5}  {'Alloc':>6}  {'Timing'}")
        print(f"  {'-'*68}")

        for r in top5:
            rank     = r.get("rank", "?")
            symbol   = r.get("symbol", "?")
            classe   = r.get("classe", "?")
            prix     = r.get("prix_entree", r.get("prix", 0))
            gain     = r.get("gain_attendu", 0)
            stop_abs = r.get("stop", 0)
            stop_pct = ((prix - stop_abs) / prix * 100) if prix and stop_abs else r.get("stop_pct", 0)
            wos      = r.get("wos", r.get("wos_score", 0))
            atr      = r.get("atr_pct", 0)
            rr       = r.get("rr", 0)
            alloc    = r.get("allocation_max", 5.0)
            timing   = r.get("timing_signal", "N/A")
            liq      = r.get("position_size_factor", 1.0) or 1.0

            # Tag liquidité
            liq_tag = "" if liq >= 1.0 else " [LIQ-]"

            # Tag timing visuel
            if timing == "CONFIRME":
                timing_tag = "OK-ENTRER"
            elif timing == "ATTENDRE":
                timing_tag = "ATTENDRE!"
            elif timing == "NEUTRE":
                timing_tag = "NEUTRE"
            else:
                timing_tag = "N/A"

            print(f"  #{rank:<2} {symbol:<6} {classe:<4} {prix:>9,.0f} {gain:>+6.1f}% {stop_pct:>-6.1f}% {wos:>5.1f} {atr:>4.1f}% {rr:>5.2f}  {alloc:>4.0f}%{'':<2}  {timing_tag}{liq_tag}")

        print(f"\n  Générées le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"\n  {'─'*66}")
        print(f"  REGLES DE GESTION OBLIGATOIRES")
        print(f"  {'─'*66}")
        print(f"  > Horizon de détention : 4-8 semaines (ne pas sortir avant)")
        print(f"  > MAX 3 positions simultanées (liquidité BRVM limitée)")
        print(f"  > Alloc A=15% | B=10% | C=5% du portefeuille par position")
        print(f"  > Timing ATTENDRE! → différer l'entrée au lendemain")
        print(f"  > Stop obligatoire : ordre limite 1 tick sous le niveau indiqué")
        print(f"  {'─'*66}\n")

    except Exception as e:
        print(f"  [ERREUR affichage] {e}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PIPELINE RECOMMANDATIONS PRO — FORMULE 07/02")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*60)

    # 0. Vérification données
    print("\n[0/3] Vérification données...")
    if not verifier_donnees():
        sys.exit(1)

    # 1. Analyse IA (scores techniques + sentiment)
    ok = run("analyse_ia_simple.py", "[1/3] Analyse IA — Scores techniques + sentiment")
    if not ok:
        print("[STOP] Erreur étape 1")
        sys.exit(1)

    # 2. Décisions BUY (formule restaurée : stop=0.9×ATR, target=2.4×ATR)
    ok = run("decision_finale_brvm.py", "[2/3] Décisions BUY — Stop=0.9×ATR | Target=2.4×ATR | RR=2.67")
    if not ok:
        print("[STOP] Erreur étape 2")
        sys.exit(1)

    # 3. Classement TOP5
    ok = run("top5_engine_final.py", "[3/3] Classement TOP5")
    if not ok:
        print("[STOP] Erreur étape 3")
        sys.exit(1)

    # Affichage résultat final
    afficher_top5()

    print("\n" + "="*60)
    print("  PIPELINE TERMINÉ")
    print("="*60 + "\n")

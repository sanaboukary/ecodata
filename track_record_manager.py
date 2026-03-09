#!/usr/bin/env python3
"""
TRACK RECORD MANAGER — BRVM
============================
Système de track record live horodaté pour les recommandations TOP5.

Différenciateur clé vs Sika Finance / RichBourse :
  Toutes les recommandations passées sont conservées avec prix d'entrée,
  stop, cible, et résultat réel — vérifiables publiquement.

Usage :
  python track_record_manager.py --snapshot        # Prendre snapshot TOP5 du jour
  python track_record_manager.py --update          # Mettre à jour les positions ouvertes
  python track_record_manager.py --report          # Rapport de performance complet
  python track_record_manager.py --snapshot --update  # Les deux (usage pipeline quotidien)

Intégration pipeline :
  Ajouter en fin de lancer_recos_daily.py après top5_engine_final.py.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

# ─── Constantes ──────────────────────────────────────────────────────────────
COLLECTION_TR    = "track_record_weekly"   # collection track record
COLLECTION_TOP5D = "top5_daily_brvm"
COLLECTION_TOP5W = "top5_weekly_brvm"
HORIZON_JOURS    = 25                      # horizon cible optimal (calibré 2020-2026)

# Seuils de sortie (en %)
TP1_PCT  = 7.5    # TP1 : vendre 50% de la position
TP2_PCT  = 15.0   # TP2 : vendre 30%
TP3_PCT  = 27.5   # Runner : vendre les 20% restants


# ─── MODE CLI ────────────────────────────────────────────────────────────────
MODE_SNAPSHOT = "--snapshot" in sys.argv
MODE_UPDATE   = "--update"   in sys.argv
MODE_REPORT   = "--report"   in sys.argv
MODE_DAILY    = "--mode" in sys.argv and "daily" in sys.argv

if not (MODE_SNAPSHOT or MODE_UPDATE or MODE_REPORT):
    MODE_REPORT = True  # par défaut : afficher le rapport


# ─── Snapshot : enregistrer le TOP5 courant ──────────────────────────────────

def prendre_snapshot(db) -> int:
    """
    Enregistre le TOP5 courant dans track_record_weekly.
    Chaque recommandation est horodatée et devient une référence immuable.
    Ne crée PAS de doublon si une recommandation identique (symbol + week_id) existe déjà.
    Retourne le nombre de nouvelles positions créées.
    """
    # Lire le TOP5 depuis la collection appropriée
    collection = COLLECTION_TOP5D if MODE_DAILY else COLLECTION_TOP5W
    top5 = list(db[collection].find({}).sort("rank", 1))

    if not top5:
        print(f"  [SNAPSHOT] Aucune recommandation dans {collection}")
        return 0

    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"
    today_str = now.strftime("%Y-%m-%d")

    created = 0
    for t in top5:
        symbol = t.get("symbol")
        if not symbol:
            continue

        # Vérifier si une position existe déjà pour ce symbole et cette semaine
        existing = db[COLLECTION_TR].find_one({
            "symbol": symbol,
            "week_id": week_id,
        })

        if existing:
            # Position déjà enregistrée cette semaine — ne pas écraser
            print(f"  [SNAPSHOT] {symbol:<8} déjà enregistré (week={week_id}) — ignoré")
            continue

        # Récupérer le prix de clôture le plus récent comme prix d'entrée réel
        dernier_prix = db.prices_daily.find_one(
            {"symbol": symbol, "close": {"$gt": 0}},
            {"close": 1, "date": 1},
            sort=[("date", -1)]
        ) if db is not None else None
        prix_entree_reel = t.get("prix_entree") or (dernier_prix.get("close") if dernier_prix else None)
        date_entree = (dernier_prix.get("date") if dernier_prix else today_str)

        # Calculer les niveaux réels depuis le prix d'entrée réel
        stop_reel   = t.get("stop")
        cible_tp1   = round(prix_entree_reel * (1 + TP1_PCT / 100)) if prix_entree_reel else t.get("prix_cible")
        cible_tp2   = round(prix_entree_reel * (1 + TP2_PCT / 100)) if prix_entree_reel else None
        cible_runner= round(prix_entree_reel * (1 + TP3_PCT / 100)) if prix_entree_reel else None
        date_expiry = (now + timedelta(days=HORIZON_JOURS)).strftime("%Y-%m-%d")

        doc = {
            # Identification
            "symbol":            symbol,
            "week_id":           week_id,
            "rank":              t.get("rank"),
            "mode":              "DAILY" if MODE_DAILY else "WEEKLY",

            # Émission
            "emis_le":           now,
            "date_entree":       date_entree,
            "prix_entree":       prix_entree_reel,
            "prix_entree_signal": t.get("prix_entree"),

            # Niveaux de sortie
            "stop":              stop_reel,
            "cible_tp1":         cible_tp1,      # +7.5%  → vendre 50%
            "cible_tp2":         cible_tp2,      # +15.0% → vendre 30%
            "cible_runner":      cible_runner,   # +27.5% → vendre 20%
            "date_expiry":       date_expiry,    # J+25 par défaut

            # Scores au moment de l'émission (immuables)
            "score_total_mf":    t.get("score_total_mf"),
            "mf_label":          t.get("mf_label"),
            "setup_type":        t.get("setup_type"),
            "prob_win":          t.get("prob_win"),
            "top5_score":        t.get("top5_score"),
            "confidence":        t.get("confidence"),
            "gain_attendu":      t.get("gain_attendu"),
            "atr_pct":           t.get("atr_pct"),
            "regime":            t.get("market_regime"),
            "vcp_pattern":       t.get("vcp_pattern"),
            "signal_explosion":  t.get("signal_explosion"),

            # Suivi en temps réel (mis à jour quotidiennement)
            "statut":            "EN_COURS",       # EN_COURS | TP1 | TP2 | RUNNER | STOP | EXPIRE
            "prix_actuel":       prix_entree_reel,
            "performance_pct":   0.0,
            "max_favorable_pct": 0.0,             # MAE favorable (highwater mark)
            "nb_jours_ouverts":  0,
            "tp1_atteint":       False,
            "tp2_atteint":       False,
            "stop_atteint":      False,
            "updated_at":        now,
        }

        db[COLLECTION_TR].insert_one(doc)
        created += 1
        print(f"  [SNAPSHOT] {symbol:<8} #{t.get('rank')} | MF={t.get('score_total_mf',0):.1f} {t.get('mf_label','?'):<12}"
              f" | entree={prix_entree_reel:,.0f} stop={stop_reel or 0:,.0f} TP1={cible_tp1 or 0:,.0f}"
              f" | expiry={date_expiry}")

    print(f"  [SNAPSHOT] {created} nouvelle(s) position(s) enregistrée(s) → {COLLECTION_TR}")
    return created


# ─── Update : mettre à jour les positions ouvertes ───────────────────────────

def mettre_a_jour_positions(db) -> dict:
    """
    Met à jour toutes les positions EN_COURS avec le prix du jour.
    Detects TP1, TP2, RUNNER ou STOP selon les niveaux définis à l'émission.
    Une position peut atteindre TP1 (partielle) puis continuer vers TP2.
    """
    positions_ouvertes = list(db[COLLECTION_TR].find({"statut": "EN_COURS"}))

    if not positions_ouvertes:
        print("  [UPDATE] Aucune position EN_COURS à mettre à jour")
        return {"updated": 0, "tp1": 0, "tp2": 0, "stop": 0, "expire": 0}

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    stats = {"updated": 0, "tp1": 0, "tp2": 0, "stop": 0, "expire": 0}

    for pos in positions_ouvertes:
        symbol = pos["symbol"]

        # Prix actuel depuis prices_daily (dernier close disponible)
        prix_doc = db.prices_daily.find_one(
            {"symbol": symbol, "close": {"$gt": 0}},
            {"close": 1, "high": 1, "low": 1, "date": 1},
            sort=[("date", -1)]
        )
        if not prix_doc:
            continue

        prix_actuel = prix_doc.get("close", 0)
        high_jour   = prix_doc.get("high", prix_actuel)
        low_jour    = prix_doc.get("low", prix_actuel)
        date_cours  = prix_doc.get("date", today_str)

        # Calcul performance
        prix_entree = pos.get("prix_entree") or 0
        if not prix_entree or prix_entree <= 0:
            continue

        perf_pct = (prix_actuel - prix_entree) / prix_entree * 100

        # Highwater mark intraday (favorise le calcul de max_favorable)
        perf_high = (high_jour - prix_entree) / prix_entree * 100
        max_fav   = max(pos.get("max_favorable_pct", 0), perf_high)

        # Nb jours ouverts
        emis_le = pos.get("emis_le")
        nb_jours = 0
        if emis_le:
            nb_jours = (now - (emis_le if emis_le.tzinfo else emis_le.replace(tzinfo=timezone.utc))).days

        # Déterminer le nouveau statut
        stop       = pos.get("stop", 0) or 0
        cible_tp1  = pos.get("cible_tp1") or (prix_entree * 1.075)
        cible_tp2  = pos.get("cible_tp2") or (prix_entree * 1.15)
        cible_run  = pos.get("cible_runner") or (prix_entree * 1.275)
        date_exp   = pos.get("date_expiry", "")
        tp1_deja   = pos.get("tp1_atteint", False)
        tp2_deja   = pos.get("tp2_atteint", False)

        nouveau_statut = "EN_COURS"
        tp1_atteint = tp1_deja
        tp2_atteint = tp2_deja

        # Test dans l'ordre de priorité : STOP > TP2 > TP1 > EXPIRY
        # (utilise high/low du jour pour détecter les franchissements intraday)
        if stop > 0 and low_jour <= stop:
            nouveau_statut = "STOP"
            prix_sortie = stop  # sorti au stop
            stats["stop"] += 1
        elif high_jour >= cible_run and tp1_deja and tp2_deja:
            nouveau_statut = "RUNNER"
            prix_sortie = cible_run
        elif high_jour >= cible_tp2:
            nouveau_statut = "TP2"
            tp2_atteint = True
            prix_sortie = cible_tp2
            stats["tp2"] += 1
        elif high_jour >= cible_tp1:
            if not tp1_deja:
                nouveau_statut = "TP1"
                tp1_atteint = True
                prix_sortie = cible_tp1
                stats["tp1"] += 1
            else:
                nouveau_statut = "EN_COURS"  # TP1 déjà atteint, position partielle en cours
                prix_sortie = None
        elif date_exp and today_str >= date_exp:
            nouveau_statut = "EXPIRE"
            prix_sortie = prix_actuel
            stats["expire"] += 1
        else:
            prix_sortie = None

        fields = {
            "prix_actuel":       prix_actuel,
            "performance_pct":   round(perf_pct, 2),
            "max_favorable_pct": round(max_fav, 2),
            "nb_jours_ouverts":  nb_jours,
            "tp1_atteint":       tp1_atteint,
            "tp2_atteint":       tp2_atteint,
            "statut":            nouveau_statut,
            "date_cours":        date_cours,
            "updated_at":        now,
        }

        if prix_sortie is not None:
            perf_sortie = (prix_sortie - prix_entree) / prix_entree * 100
            fields["prix_sortie"]       = prix_sortie
            fields["performance_reelle"] = round(perf_sortie, 2)
            fields["date_sortie"]        = date_cours
        else:
            fields["performance_reelle"] = round(perf_pct, 2)

        db[COLLECTION_TR].update_one(
            {"_id": pos["_id"]},
            {"$set": fields}
        )
        stats["updated"] += 1

        statut_str = f" → {nouveau_statut}" if nouveau_statut != "EN_COURS" else ""
        print(f"  [UPDATE] {symbol:<8} {date_cours} | prix={prix_actuel:,.0f} | perf={perf_pct:+.1f}%"
              f" | max={max_fav:+.1f}% | j={nb_jours}{statut_str}")

    print(f"  [UPDATE] {stats['updated']} mises à jour | TP1:{stats['tp1']} TP2:{stats['tp2']}"
          f" STOP:{stats['stop']} EXPIRE:{stats['expire']}")
    return stats


# ─── Rapport de performance ──────────────────────────────────────────────────

def generer_rapport(db):
    """
    Génère un rapport de performance complet depuis track_record_weekly.
    Calcule WR, PF, Gain moyen, MaxDD — avec décomposition par label MF et setup_type.
    """
    print("\n" + "=" * 80)
    print("  TRACK RECORD LIVE — RAPPORT DE PERFORMANCE")
    print("=" * 80 + "\n")

    all_docs = list(db[COLLECTION_TR].find({}))
    if not all_docs:
        print("  Aucune recommandation dans le track record.")
        return

    total   = len(all_docs)
    en_cours= sum(1 for d in all_docs if d.get("statut") == "EN_COURS")
    fermes  = [d for d in all_docs if d.get("statut") not in ("EN_COURS",)]

    print(f"  Total recommandations : {total}")
    print(f"  En cours              : {en_cours}")
    print(f"  Clôturées             : {len(fermes)}")

    if not fermes:
        print("\n  Pas encore de positions clôturées — track record en construction.")
        print("  Ajouter --update chaque soir pour mettre à jour les positions ouvertes.")
        # Afficher les positions en cours
        print("\n  POSITIONS EN COURS :")
        print(f"  {'Symbol':<8} {'Semaine':<10} {'Entree':>8} {'Actuel':>8} {'Perf%':>7} {'Stop':>8} {'TP1':>8} {'J':>4}")
        print("  " + "-" * 70)
        for d in sorted(all_docs, key=lambda x: x.get("emis_le") or datetime.min, reverse=True):
            entree = d.get("prix_entree") or 0
            actuel = d.get("prix_actuel") or entree
            perf   = d.get("performance_pct") or 0
            stop   = d.get("stop") or 0
            tp1    = d.get("cible_tp1") or 0
            jours  = d.get("nb_jours_ouverts") or 0
            semaine= d.get("week_id", "?")
            print(f"  {d.get('symbol','?'):<8} {semaine:<10} {entree:>8,.0f} {actuel:>8,.0f} "
                  f"{perf:>+6.1f}% {stop:>8,.0f} {tp1:>8,.0f} {jours:>4}j")
        return

    # Métriques sur les positions clôturées
    perfs = [d.get("performance_reelle") or d.get("performance_pct") or 0 for d in fermes]
    gains = [p for p in perfs if p > 0]
    pertes= [p for p in perfs if p <= 0]

    wr = len(gains) / len(fermes) if fermes else 0
    gain_moy = sum(gains) / len(gains) if gains else 0
    perte_moy= sum(pertes) / len(pertes) if pertes else 0
    pf = abs(gain_moy * len(gains) / (perte_moy * len(pertes))) if pertes and perte_moy != 0 else float('inf')

    print(f"\n  ─── MÉTRIQUES GLOBALES ({len(fermes)} positions clôturées) ───")
    print(f"  Win Rate       : {wr*100:.1f}%  ({len(gains)} gagnants / {len(pertes)} perdants)")
    print(f"  Gain moyen W   : +{gain_moy:.1f}%")
    print(f"  Perte moyenne L: {perte_moy:.1f}%")
    print(f"  Profit Factor  : {pf:.2f}")

    print(f"\n  ─── PAR LABEL MF ───")
    from collections import defaultdict
    by_label = defaultdict(list)
    for d in fermes:
        label = d.get("mf_label", "?")
        perf  = d.get("performance_reelle") or d.get("performance_pct") or 0
        by_label[label].append(perf)

    for label in ["EXPLOSION", "SWING_FORT", "SWING_MOYEN", "IGNORER"]:
        ps = by_label.get(label, [])
        if not ps:
            continue
        wr_l = sum(1 for p in ps if p > 0) / len(ps)
        gm   = sum(p for p in ps if p > 0) / len([p for p in ps if p > 0]) if [p for p in ps if p > 0] else 0
        print(f"  {label:<14}: {len(ps):>4} trades | WR={wr_l*100:.0f}% | Gain moy={gm:+.1f}%")

    print(f"\n  ─── PAR STATUT DE SORTIE ───")
    by_statut = defaultdict(list)
    for d in fermes:
        by_statut[d.get("statut", "?")].append(d.get("performance_reelle") or 0)

    for statut, ps in sorted(by_statut.items()):
        moy = sum(ps) / len(ps) if ps else 0
        print(f"  {statut:<12}: {len(ps):>4} | perf moy={moy:+.1f}%")

    print(f"\n  ─── DERNIÈRES 10 POSITIONS ───")
    print(f"  {'Symbol':<8} {'Semaine':<10} {'Statut':<10} {'Entree':>8} {'Sortie':>8} {'Perf%':>7} {'Label':<12}")
    print("  " + "-" * 75)
    recents = sorted(fermes, key=lambda d: d.get("updated_at") or datetime.min, reverse=True)[:10]
    for d in recents:
        entree = d.get("prix_entree") or 0
        sortie = d.get("prix_sortie") or d.get("prix_actuel") or 0
        perf   = d.get("performance_reelle") or d.get("performance_pct") or 0
        print(f"  {d.get('symbol','?'):<8} {d.get('week_id','?'):<10} {d.get('statut','?'):<10}"
              f" {entree:>8,.0f} {sortie:>8,.0f} {perf:>+6.1f}% {d.get('mf_label','?'):<12}")

    print("\n" + "=" * 80 + "\n")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  TRACK RECORD MANAGER — BRVM")
    mode_str = []
    if MODE_SNAPSHOT: mode_str.append("SNAPSHOT")
    if MODE_UPDATE:   mode_str.append("UPDATE")
    if MODE_REPORT:   mode_str.append("RAPPORT")
    print(f"  Mode : {' + '.join(mode_str) if mode_str else 'RAPPORT'}")
    print("=" * 70 + "\n")

    _, db = get_mongo_db()

    if MODE_SNAPSHOT:
        print("─" * 60)
        print("  SNAPSHOT — Enregistrement TOP5 courant")
        print("─" * 60)
        prendre_snapshot(db)
        print()

    if MODE_UPDATE:
        print("─" * 60)
        print("  UPDATE — Mise à jour des positions ouvertes")
        print("─" * 60)
        mettre_a_jour_positions(db)
        print()

    if MODE_REPORT or not (MODE_SNAPSHOT or MODE_UPDATE):
        generer_rapport(db)


if __name__ == "__main__":
    main()

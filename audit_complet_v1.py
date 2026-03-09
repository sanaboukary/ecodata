#!/usr/bin/env python3
"""
AUDIT COMPLET SYSTÈME V1 PRODUCTION
===================================
Analyse exhaustive de la plateforme actuelle (10,000 clients)
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import statistics
import json

def print_section(title):
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90 + "\n")

def audit_architecture():
    """SECTION 1: Architecture et Pipeline"""
    print_section("1. ARCHITECTURE ET PIPELINE V1")
    
    pipeline_steps = [
        ("ÉTAPE 1", "collecter_publications_brvm.py", "Collecte publications BRVM"),
        ("ÉTAPE 2", "analyse_semantique_brvm_v3.py", "Analyse sémantique + filtre risque"),
        ("ÉTAPE 3", "agregateur_semantique_actions.py", "Agrégation par action"),
        ("ÉTAPE 4", "analyse_ia_simple.py", "Analyse technique (RS, ATR, percentiles)"),
        ("ÉTAPE 5", "decision_finale_brvm.py", "Scoring ALPHA + décision investissement"),
        ("ÉTAPE 6", "top5_engine_brvm.py", "Classement TOP 5 surperformance"),
        ("ÉTAPE 7", "propagation_sector_to_action.py", "Ajustement sectoriel"),
        ("ÉTAPE 8", "backtest_reporting_monitoring.py", "Monitoring + alertes"),
    ]
    
    print("📊 PIPELINE COMPLET (8 étapes):")
    for step, script, desc in pipeline_steps:
        print(f"  {step}: [{script:40s}] → {desc}")
    
    print("\n✅ MODES OPÉRATOIRES:")
    print("  • MODE_INSTITUTIONAL = True (SGI-level scoring)")
    print("  • MODE_ELITE_MINIMALISTE = True (14 semaines données, filtres percentiles)")

def audit_formules(db):
    """SECTION 2: Formules et Calculs"""
    print_section("2. FORMULES ALPHA SCORE V1 (INSTITUTIONAL)")
    
    print("🧮 FORMULE ALPHA_SCORE ADAPTATIVE:")
    print("""
    ALPHA_V1 = 
        w_rs × RS_percentile +
        w_accel × Acceleration +
        w_vol × Volume_percentile +
        w_breakout × Breakout_strength +
        w_sent × Sentiment_normalisé +
        w_voleff × Volatility_efficiency
    
    Avec normalisation 0-100
    """)
    
    print("\n📊 PONDÉRATIONS DYNAMIQUES PAR RÉGIME:")
    print("""
    RÉGIME BULL:
      • RS: 30% | Accel: 25% ↑ | Vol: 10% | Breakout: 20% ↑ | Sent: 5-20% | VolEff: 5%
    
    RÉGIME BEAR:
      • RS: 40% ↑ | Accel: 10% | Vol: 25% ↑ | Breakout: 5% | Sent: 5-20% | VolEff: 10% ↑
    
    RÉGIME RANGE:
      • RS: 35% | Accel: 20% | Vol: 15% | Breakout: 15% | Sent: 5-20% | VolEff: 5%
    """)
    
    print("\n🔥 SENTIMENT DYNAMIQUE (INNOVATION V1):")
    print("""
    Poids ajusté selon activité publications:
      • < 3 publications/semaine  → 5% (bruit minimal)
      • 3-8 publications/semaine  → 10% (accélérateur)
      • Événement majeur (RESULTATS, DIVIDENDE) → 20% (moteur)
    
    Détection auto événements: RESULTATS, DIVIDENDE, ACQUISITION, FUSION, CONSEIL
    """)
    
    print("\n⚙️ COMPOSANTS ALPHA:")
    print("""
    1. RS_percentile: Position relative 4 semaines (0-100)
    2. Acceleration: (RS_2w - RS_4w) / RS_4w (normalisation -10% à +10%)
    3. Volume_percentile: Position relative volume 8 semaines (0-100)
    4. Breakout_strength: (Prix - Max_3w) / Max_3w (tolérance -2%)
    5. Sentiment: score_sémantique -100 à +100 (multi-sources)
    6. VolEfficiency: perf_4w / ATR% (rendement/risque)
    """)

def audit_filtres():
    """SECTION 3: Filtres Elite"""
    print_section("3. FILTRES ELITE MINIMALISTE (14 SEMAINES)")
    
    print("🎯 FILTRES PERCENTILE-BASED (Priorité vs seuils absolus):\n")
    
    filtres = [
        ("1. RS PERCENTILE", "≥ P75 (Top 25% univers)", "Ou fallback: RS ≥ -43.3% (P70 empirique)"),
        ("2. VOLUME PERCENTILE", "≥ P30 (Bloquer bottom 30%)", "P30-40: Position 50% | P40+: Position 100%"),
        ("3. ACCÉLERATION", "≥ 2.0%", "BRVM: <1%=bruit, 2-4%=mouvement, >4%=explosion"),
        ("4. BREAKOUT", "Prix ≥ Max_3w - 2%", "Tolérance -2% pour spread BRVM"),
        ("5. TENDANCE", "Tolérance DOWN court terme", "Down acceptable si momentum ailleurs"),
        ("6. ATR%", "8% ≤ ATR ≤ 30%", "<8%=mort | >30%=micro-cap instable"),
    ]
    
    for num, condition, note in filtres:
        print(f"  {num:20s} : {condition:30s} | {note}")
    
    print("\n⚠️ POSITION SIZING ADAPTATIF:")
    print("  • Volume P60+   → 100% position (top liquidité)")
    print("  • Volume P40-60 → 100% position (volume correct)")
    print("  • Volume P30-40 → 50% position (peu liquide)")
    print("  • Volume <P30   → REJETÉ (bottom 30% trop risqué)")

def audit_donnees(db):
    """SECTION 4: Données et Qualité"""
    print_section("4. DONNÉES MONGODB - ÉTAT ACTUEL")
    
    # Prices weekly
    count_weekly = db.prices_weekly.count_documents({})
    if count_weekly > 0:
        sample_weekly = db.prices_weekly.find_one()
        distinct_symbols = db.prices_weekly.distinct("symbol")
        print(f"📦 prices_weekly:")
        print(f"  • Total documents: {count_weekly}")
        print(f"  • Actions distinctes: {len(distinct_symbols)}")
        print(f"  • Moyenne docs/action: {count_weekly / len(distinct_symbols):.1f} semaines")
        print(f"  • Structure: {list(sample_weekly.keys())}")
    
    # Curated observations
    count_curated = db.curated_observations.count_documents({})
    datasets = db.curated_observations.distinct("dataset")
    print(f"\n📦 curated_observations:")
    print(f"  • Total documents: {count_curated}")
    print(f"  • Datasets distincts: {len(datasets)}")
    for ds in datasets:
        count = db.curated_observations.count_documents({"dataset": ds})
        print(f"    - {ds}: {count} documents")
    
    # Decisions finales
    count_decisions = db.decisions_finales_brvm.count_documents({})
    if count_decisions > 0:
        recent = list(db.decisions_finales_brvm.find().sort("date_generation", -1).limit(5))
        print(f"\n📦 decisions_finales_brvm:")
        print(f"  • Total décisions: {count_decisions}")
        print(f"  • Génération récente: {recent[0].get('date_generation', 'N/A')}")
        print(f"  • Derniers signaux:")
        for d in recent[:3]:
            sym = d.get("symbol", "N/A")
            signal = d.get("signal", "N/A")
            score = d.get("score", 0)
            print(f"    - {sym}: {signal} (score: {score:.1f})")

def audit_performance(db):
    """SECTION 5: Performance et Résultats"""
    print_section("5. PERFORMANCE SYSTEME V1")
    
    # Dernière exécution pipeline
    recent_decisions = list(db.decisions_finales_brvm.find().sort("date_generation", -1).limit(20))
    
    if not recent_decisions:
        print("⚠️ Aucune décision récente trouvée")
        return
    
    print(f"📊 DERNIÈRE EXÉCUTION ({recent_decisions[0].get('date_generation', 'N/A')}):\n")
    
    # Distribution signaux
    signals = [d.get("signal", "N/A") for d in recent_decisions]
    signal_counts = {s: signals.count(s) for s in set(signals)}
    print("  Signaux générés:")
    for sig, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {sig:10s}: {count:2d} actions ({count/len(signals)*100:.1f}%)")
    
    # Distribution scores
    scores = [d.get("score", 0) for d in recent_decisions if d.get("score")]
    if scores:
        print(f"\n  Scores (sur {len(scores)} actions):")
        print(f"    • Moyenne: {statistics.mean(scores):.1f}")
        print(f"    • Médiane: {statistics.median(scores):.1f}")
        print(f"    • Min-Max: {min(scores):.1f} - {max(scores):.1f}")
    
    # TOP performers
    buy_decisions = [d for d in recent_decisions if d.get("signal") == "BUY"]
    if buy_decisions:
        buy_decisions.sort(key=lambda x: x.get("score", 0), reverse=True)
        print(f"\n  TOP 5 BUY (par score):")
        for i, d in enumerate(buy_decisions[:5], 1):
            sym = d.get("symbol", "N/A")
            score = d.get("score", 0)
            conf = d.get("confidence", 0)
            print(f"    {i}. {sym:6s} - Score: {score:5.1f} | Confiance: {conf:3.0f}%")

def audit_forces_faiblesses():
    """SECTION 6: Forces et Faiblesses"""
    print_section("6. FORCES ET FAIBLESSES SYSTÈME V1")
    
    print("✅ FORCES MAJEURES:\n")
    forces = [
        ("Architecture modulaire", "8 étapes pipeline séparées, maintenance facilitée"),
        ("Scoring institutional", "ALPHA multi-facteurs avec pondérations adaptatives"),
        ("Sentiment dynamique", "5-20% selon activité publications (INNOVATION)"),
        ("Filtres percentiles", "Adaptés marché BRVM (concentré, irrégulier, 14 semaines)"),
        ("Position sizing", "Ajustement automatique selon liquidité (P30-P40: 50%, P40+: 100%)"),
        ("Détection régime", "BULL/BEAR/RANGE → ajustement poids et seuils"),
        ("Allocation SGI", "Max 25%/action, 30%/secteur, exposition régime (50-100%)"),
        ("Multi-sources données", "Publications, prix, volumes, sémantique agrégée"),
        ("Mode Elite", "Filtres stricts pour 14 semaines données (professionnalisme)"),
        ("Monitoring", "Alertes, backtests, capture rate, reporting"),
    ]
    
    for i, (titre, desc) in enumerate(forces, 1):
        print(f"  {i:2d}. {titre:25s}: {desc}")
    
    print("\n\n⚠️ FAIBLESSES IDENTIFIÉES:\n")
    faiblesses = [
        ("Complexité formule", "6 facteurs + normalisations → difficile à interpréter/debug"),
        ("Dépendances Django", "Setup lourd, scripts peuvent bloquer silencieusement"),
        ("Saturation scores", "Breakout/Event souvent 100 → peu de différenciation"),
        ("Données limitées", "14 semaines seulement (mode Elite) → historique court"),
        ("Calibration manuelle", "Seuils (P75, 2%, -43%) empiriques, pas optimisés"),
        ("Pas de backtest live", "Validation sur données passées, pas suivi performance réelle"),
        ("Divergence possible", "V1 optimisé pour leaders passés, peut rater nouveaux"),
        ("Volume faible BRVM", "Actions illiquides fréquentes → sizing réduit mais risque"),
        ("Event detection basique", "Keywords simples, pas NLP avancé"),
        ("Mono-horizon", "Hebdomadaire uniquement, pas multi-timeframes"),
    ]
    
    for i, (titre, desc) in enumerate(faiblesses, 1):
        print(f"  {i:2d}. {titre:25s}: {desc}")

def audit_risques():
    """SECTION 7: Risques et Points d'Attention"""
    print_section("7. RISQUES ET POINTS D'ATTENTION")
    
    print("🔴 RISQUES CRITIQUES (IMPACT CLIENTS 10K):\n")
    risques = [
        ("HAUT", "Données aberrantes", "Prix/volumes incorrects → faux signaux BUY/SELL"),
        ("HAUT", "Pipeline fail silent", "Django error silencieux → recommandations obsolètes"),
        ("MOYEN", "Overfitting calibration", "Seuils optimisés sur passé → dégradation future"),
        ("MOYEN", "Concentration liquidité", "Actions P30-40 (50% position) peuvent bloquer sortie"),
        ("MOYEN", "Régime detection lag", "Détection BEAR tardive → exposure trop élevée"),
        ("BAS", "Sentiment keywords", "Événements ratés si vocabulaire différent"),
        ("BAS", "Breakout false positive", "Tolérance -2% peut valider faux breakouts"),
    ]
    
    for risk, titre, desc in risques:
        icon = "🔴" if risk == "HAUT" else "🟡" if risk == "MOYEN" else "🟢"
        print(f"  {icon} [{risk:6s}] {titre:25s}: {desc}")
    
    print("\n\n📋 RECOMMANDATIONS OPÉRATIONNELLES:\n")
    recommandations = [
        "1. Monitoring quotidien données prix (alertes aberrations)",
        "2. Backup V1 complet avant toute modification",
        "3. Pipeline logs centralisés (détection erreurs silencieuses)",
        "4. Backtests hebdomadaires (validation performance réelle)",
        "5. Shadow deployment V2 (validation 4+ semaines avant migration)",
        "6. Review calibration trimest (re-optimisation seuils percentiles)",
        "7. Alertes clients si signal SELL brutal (communication transparente)",
        "8. Diversification forcée (max 3 actions même secteur)",
        "9. Stop-loss automatique (protection drawdown >10%)",
        "10. Documentation décisions (traçabilité recommandations)",
    ]
    
    for rec in recommandations:
        print(f"  • {rec}")

def audit_comparaison_v2():
    """SECTION 8: Comparaison V1 vs V2"""
    print_section("8. COMPARAISON V1 (PRODUCTION) VS V2 (SHADOW)")
    
    print("📊 DIFFÉRENCES ARCHITECTURALES:\n")
    
    comparison = [
        ("Facteurs", "6 facteurs adaptifs", "4 facteurs fixes"),
        ("Formule", "Poids dynamiques (régime)", "Poids fixes (35/25/20/20)"),
        ("Données", "prices_weekly + curated", "prices_weekly + AGREGATION"),
        ("Sentiment", "5-20% dynamique", "20% fixe"),
        ("Filtres", "6 filtres percentiles stricts", "Aucun (capture toute gamme)"),
        ("Momentum", "Acceleration + RS percentile", "RS 2w/8w ratio"),
        ("Volume", "Percentile + sizing adaptatif", "Spike relatif (latest/median)"),
        ("Event", "Absent (implicite sentiment)", "Explicite 20% (RESULTATS=100)"),
        ("Setup", "Django requis", "Sans Django (standalone)"),
        ("Complexité", "Haute (institutionnelle)", "Basse (4 facteurs simples)"),
    ]
    
    print(f"{'Aspect':<15} | {'V1 (Production)':<30} | {'V2 (Shadow)':<30}")
    print("-" * 80)
    for aspect, v1, v2 in comparison:
        print(f"{aspect:<15} | {v1:<30} | {v2:<30}")
    
    print("\n\n🎯 HYPOTHÈSES À VALIDER (Shadow 4+ semaines):\n")
    hypotheses = [
        "1. Simplicité V2 (4 facteurs) capture mieux opportunités que complexité V1",
        "2. Momentum précoce (2w/8w) détecte mouvements avant RS percentile",
        "3. Event explicite (20%) améliore timing vs sentiment implicite",
        "4. Absence filtres permet capture actions P50-P75 qui explosent",
        "5. Volume spike relatif plus pertinent que percentile absolu",
    ]
    
    for hyp in hypotheses:
        print(f"  {hyp}")
    
    print("\n\n📈 MÉTRIQUES DÉCISION (Après 4 semaines V2):\n")
    print("  ✅ Migration V1→V2 SI:")
    print("    • WinRate_V2 ≥ WinRate_V1 + 5%")
    print("    • Sharpe_V2 ≥ Sharpe_V1")
    print("    • Drawdown_V2 ≤ Drawdown_V1")
    print("    • Return_V2 ≥ Return_V1")
    print("\n  ❌ Maintien V1 SI:")
    print("    • UNE seule métrique échoue")
    print("    • Ou turnover V2 > 80% (instabilité)")

def main():
    """Audit complet V1"""
    print("\n" + "=" * 90)
    print(" " * 20 + "AUDIT COMPLET SYSTÈME V1 PRODUCTION")
    print(" " * 25 + f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" " * 28 + "Clients: 10,000 personnes")
    print("=" * 90)
    
    # Connexion MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["centralisation_db"]
    
    # Sections audit
    audit_architecture()
    audit_formules(db)
    audit_filtres()
    audit_donnees(db)
    audit_performance(db)
    audit_forces_faiblesses()
    audit_risques()
    audit_comparaison_v2()
    
    # Conclusion
    print_section("CONCLUSION AUDIT V1")
    print("""
    ✅ SYSTÈME V1 OPÉRATIONNEL ET PROFESSIONNEL
    
    Points forts majeurs:
      • Architecture institutional SGI-level
      • Sentiment dynamique (innovation 5-20%)
      • Filtres percentiles adaptés BRVM
      • Position sizing intelligent
    
    Points d'amélioration identifiés:
      • Complexité formule (6 facteurs → 4 facteurs V2 potentiel)
      • Dépendance Django (fiabilité exécution)
      • Validation performance réelle (backtests live manquants)
    
    🎯 RECOMMANDATION FINALE:
      → MAINTENIR V1 EN PRODUCTION
      → PARALLÈLE: Shadow deployment V2 (4 semaines)
      → DÉCISION MIGRATION: Basée métriques quantitatives strictes
      → ZÉRO RISQUE CLIENTS pendant validation
    
    📊 Prochaine étape: Semaine 2/4 shadow V2
    """)
    
    print("\n" + "=" * 90)
    print(" " * 30 + "FIN AUDIT V1")
    print("=" * 90 + "\n")
    
    client.close()

if __name__ == "__main__":
    main()

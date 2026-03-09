#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Version ultra simplifiée - Debug"""

import sys
import traceback

# Ouvrir fichier log
log = open('reco_log.txt', 'w', encoding='utf-8')

try:
    log.write("Début exécution\n")
    log.flush()
    
    from pymongo import MongoClient
    log.write("Import pymongo OK\n")
    log.flush()
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    log.write("Connexion MongoDB OK\n")
    log.flush()
    
    weeks = sorted(db.prices_weekly.distinct('week'))
    log.write(f"Semaines: {len(weeks)}\n")
    log.flush()
    
    if not weeks:
        log.write("ERREUR: Aucune semaine\n")
        log.close()
        exit(1)
    
    last = weeks[-1]
    log.write(f"Dernière semaine: {last}\n")
    log.flush()
    
    obs = list(db.prices_weekly.find({'week': last}))
    log.write(f"Observations {last}: {len(obs)}\n")
    log.flush()
    
    # Tradables
    tradable = []
    for o in obs:
        atr = o.get('atr_pct')
        rsi = o.get('rsi')
        
        if atr and rsi and 6 <= atr <= 25:
            tradable.append(o)
    
    log.write(f"Tradables: {len(tradable)}\n\n")
    log.flush()
    
    if len(tradable) == 0:
        log.write("AUCUNE action tradable cette semaine\n")
        log.write("TOLÉRANCE ZÉRO : Attendre semaine prochaine\n")
        log.close()
        
        print("⚠️  TOLÉRANCE ZÉRO : Aucune action tradable cette semaine")
        print("   → Voir reco_log.txt pour détails")
        exit(0)
    
    # Afficher tradables
    log.write("TOP TRADABLES:\n")
    for t in sorted(tradable, key=lambda x: x.get('atr_pct', 0))[:10]:
        line = f"  {t['symbol']:6} ATR={t.get('atr_pct'):6.2f}% RSI={t.get('rsi'):5.1f}\n"
        log.write(line)
    
    log.write("\n" + "="*70 + "\n")
    log.write("CALCUL RECOMMANDATIONS\n")
    log.write("="*70 + "\n\n")
    log.flush()
    
    # Calcul simplifié WOS pour chaque tradable
    recommendations = []
    
    for t in tradable:
        atr = t.get('atr_pct', 10)
        rsi = t.get('rsi', 50)
        close = t.get('close', 0)
        
        # Check RSI 25-55
        if not (25 <= rsi <= 55):
            continue
        
        # Calcul simple WOS (score RSI + ATR)
        if 40 <= rsi <= 50:
            score_rsi = 100
        elif 35 <= rsi < 40 or 50 < rsi <= 55:
            score_rsi = 80
        else:
            score_rsi = 60
        
        if 8 <= atr <= 18:
            score_atr = 100
        else:
            score_atr = 60
        
        wos = score_rsi * 0.5 + score_atr * 0.5
        
        # Stop/Target
        stop = max(1.0 * atr, 4.0)
        target = 2.6 * atr
        rr = round(target / stop, 2) if stop > 0 else 0
        
        # Filtres TOLÉRANCE ZÉRO
        if wos < 65:
            continue
        if rr < 2.3:
            continue
        
        # ER
        proba = min(0.80, 0.45 + (wos / 200))
        er = round((target * proba) - (stop * (1 - proba)), 2)
        
        if er < 5.0:
            continue
        
        # Classification
        if wos >= 75 and rr >= 2.5:
            classe = 'A'
        else:
            classe = 'B'
        
        recommendations.append({
            'symbol': t['symbol'],
            'classe': classe,
            'wos': round(wos, 1),
            'rr': rr,
            'er': er,
            'stop': round(stop, 2),
            'target': round(target, 2),
            'close': close,
            'atr': atr,
            'rsi': rsi
        })
    
    # Tri
    recommendations.sort(key=lambda x: x['er'], reverse=True)
    
    log.write(f"Recommandations générées: {len(recommendations)}\n\n")
    log.flush()
    
    if len(recommendations) == 0:
        log.write("⚠️  AUCUNE recommandation après filtres TOLÉRANCE ZÉRO\n")
        log.write("Filtres trop stricts ou qualité insuffisante\n")
        log.close()
        
        print("⚠️  TOLÉRANCE ZÉRO : Filtres stricts - Aucune recommandation")
        print("   → Voir reco_log.txt pour détails")
        exit(0)
    
    # Afficher
    log.write("="*70 + "\n")
    log.write(f"RECOMMANDATIONS BRVM - {last}\n")
    log.write("="*70 + "\n\n")
    
    log.write(f"{'#':<3} {'SYMBOLE':<8} {'CL':<3} {'WOS':<6} {'RR':<6} {'ER%':<6} {'STOP%':<7} {'TARGET%':<8}\n")
    log.write("-"*70 + "\n")
    
    for i, r in enumerate(recommendations, 1):
        line = (
            f"{i:<3} {r['symbol']:<8} {r['classe']:<3} {r['wos']:<6.1f} "
            f"{r['rr']:<6.2f} {r['er']:<6.1f} {r['stop']:<7.1f} {r['target']:<8.1f}\n"
        )
        log.write(line)
    
    log.write("\n" + "="*70 + "\n")
    log.write("CONSEIL EXÉCUTION GROS CLIENTS\n")
    log.write("="*70 + "\n\n")
    
    classe_a = [r for r in recommendations if r['classe'] == 'A']
    
    if len(classe_a) > 0:
        top = classe_a[0]
        log.write(f"✅ RECOMMANDATION PRINCIPALE (CLASSE A):\n")
        log.write(f"   Symbole    : {top['symbol']}\n")
        log.write(f"   Prix actuel: {top['close']:,.0f} FCFA\n")
        log.write(f"   Stop loss  : {top['stop']:.1f}%\n")
        log.write(f"   Objectif   : {top['target']:.1f}%\n")
        log.write(f"   Risk/Reward: {top['rr']:.2f}\n")
        log.write(f"   Gain estimé: {top['er']:.1f}%\n")
        log.write(f"   WOS        : {top['wos']:.1f}/100\n")
    else:
        log.write(f"AUCUNE classe A disponible cette semaine\n")
        log.write(f"→ Recommandation: Attendre meilleure opportunité\n")
    
    log.write("\n📜 RÈGLES TOLÉRANCE ZÉRO:\n")
    log.write("   1. MAX 1-2 positions\n")
    log.write("   2. STOP LOSS OBLIGATOIRE\n")
    log.write("   3. Privilégier CLASSE A uniquement\n")
    log.write("   4. Si doute → NE PAS EXÉCUTER\n")
    
    log.write("\n✅ GÉNÉRATION TERMINÉE\n")
    log.close()
    
    # Afficher résumé console
    print("="*80)
    print(f"✅ SUCCÈS - {len(recommendations)} RECOMMANDATIONS GÉNÉRÉES")
    print("="*80)
    print(f"\nSemaine : {last}")
    print(f"Classe A: {len(classe_a)}")
    print(f"Classe B: {len([r for r in recommendations if r['classe'] == 'B'])}")
    
    if len(classe_a) > 0:
        top = classe_a[0]
        print(f"\n🎯 TOP 1 RECOMMANDATION:")
        print(f"   {top['symbol']} | RR={top['rr']:.2f} | ER={top['er']:.1f}% | WOS={top['wos']:.1f}")
    
    print(f"\n📄 Détails complets → reco_log.txt")
    print("="*80)
    
except Exception as e:
    log.write(f"\n\nERREUR:\n{e}\n\n")
    log.write(traceback.format_exc())
    log.close()
    
    print(f"❌ ERREUR: {e}")
    print(f"   Voir reco_log.txt pour traceback")
    exit(1)

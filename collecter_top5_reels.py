#!/usr/bin/env python3
"""
📊 COLLECTE TOP 5 RÉELS - BRVM
==============================

Collecte les Top 5 hausses réelles de la semaine depuis RichBourse
pour alimenter le système d'auto-apprentissage

Sources:
- Résumé hebdomadaire RichBourse
- Bulletin officiel BRVM (si disponible)
"""

import os
import sys
import re
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from auto_learning_top5 import collect_ground_truth_top5, get_week_number


def extract_top5_from_richbourse(db):
    """
    Extrait les Top 5 hausses depuis les résumés RichBourse collectés
    
    Recherche dans curated_observations où :
    - source = "BRVM_PUBLICATION" ou "RICHBOURSE"
    - type contient "résumé" ou "top"
    - texte contient "meilleures hausses" ou "top 5"
    
    Returns:
        Liste de {symbol, gain, rank}
    """
    # Rechercher résumés hebdo récents (7 derniers jours)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    resumes = list(db.curated_observations.find({
        "$or": [
            {"source": "BRVM_PUBLICATION"},
            {"source": "RICHBOURSE"}
        ],
        "ts": {"$gte": week_ago.strftime("%Y-%m-%d")}
    }))
    
    print(f"📊 {len(resumes)} publications récentes analysées\n")
    
    top5_candidates = []
    
    for doc in resumes:
        attrs = doc.get("attrs", {})
        texte = attrs.get("contenu", "") or attrs.get("texte", "") or attrs.get("fulltext", "")
        titre = attrs.get("titre", "") or attrs.get("title", "")
        
        full_text = f"{titre} {texte}".lower()
        
        # Patterns pour détecter Top 5 hausses
        if any(kw in full_text for kw in ["meilleures hausses", "top 5", "top 10", "plus fortes hausse", "palmarès"]):
            
            # Extraction symboles + gains (patterns BRVM)
            # Ex: "BICC +12.4%", "SNTS : +8.6%", "AIRL	+15.2%"
            
            patterns = [
                r'([A-Z]{3,8})[:\s]+\+?(\d+[.,]\d+)%',  # BICC : +12.4%
                r'([A-Z]{3,8})\s+\+(\d+[.,]\d+)',       # BICC +12.4
                r'([A-Z]{3,8})[:\s]+hausse[:\s]+(\d+[.,]\d+)',  # BICC : hausse 12.4%
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, texte)
                for symbol, gain_str in matches:
                    gain = float(gain_str.replace(',', '.'))
                    if gain > 0 and len(symbol) >= 3:  # Filtrage basique
                        top5_candidates.append({
                            "symbol": symbol,
                            "gain": gain,
                            "source_doc": doc.get("_id")
                        })
    
    if not top5_candidates:
        print("⚠️  Aucun Top 5 détecté automatiquement dans les publications")
        print("   → Collecte manuelle requise\n")
        return []
    
    # Dédoublonner et garder gain max par symbol
    symbol_gains = {}
    for c in top5_candidates:
        sym = c["symbol"]
        if sym not in symbol_gains or c["gain"] > symbol_gains[sym]["gain"]:
            symbol_gains[sym] = c
    
    # Trier par gain descendant et limiter à 10 (on garde un peu plus au cas où)
    sorted_candidates = sorted(symbol_gains.values(), key=lambda x: x["gain"], reverse=True)[:10]
    
    print("📈 Top hausses détectées automatiquement :\n")
    for i, c in enumerate(sorted_candidates[:5], 1):
        print(f"   {i}. {c['symbol']:8s} : +{c['gain']:.1f}%")
    
    return sorted_candidates[:5]


def manual_input_top5():
    """
    Saisie manuelle des Top 5 (si extraction auto échoue)
    """
    print("\n📝 SAISIE MANUELLE DES TOP 5 HAUSSES")
    print("─" * 50)
    print("Entrez les données (ou ENTER pour terminer)\n")
    
    top5 = []
    
    for rank in range(1, 6):
        symbol = input(f"#{rank} - Symbole (ex: BICC) : ").strip().upper()
        if not symbol:
            break
        
        gain_str = input(f"#{rank} - Gain % (ex: 12.4) : ").strip()
        try:
            gain = float(gain_str.replace(',', '.'))
        except:
            print("   ⚠️  Gain invalide, action ignorée")
            continue
        
        top5.append({
            "symbol": symbol,
            "gain": gain,
            "rank": rank
        })
    
    return top5


if __name__ == "__main__":
    _, db = get_mongo_db()
    
    print("\n" + "="*70)
    print("📊 COLLECTE TOP 5 HAUSSES RÉELLES - BRVM")
    print("="*70 + "\n")
    
    week = get_week_number()
    print(f"Semaine à collecter : {week}\n")
    
    # Tentative extraction auto
    top5_auto = extract_top5_from_richbourse(db)
    
    if top5_auto:
        print(f"\n✅ {len(top5_auto)} hausses détectées automatiquement")
        validation = input("\nValider ces données ? (o/N) : ").strip().lower()
        
        if validation == 'o':
            # Ajouter rang
            for i, t in enumerate(top5_auto, 1):
                t["rank"] = i
                t["source"] = "RICHBOURSE_AUTO"
            
            collect_ground_truth_top5(db, week, top5_auto)
            print("\n✅ Top 5 réels sauvegardés pour apprentissage\n")
        else:
            print("\n→ Passage en mode manuel")
            top5_manual = manual_input_top5()
            if top5_manual:
                for t in top5_manual:
                    t["source"] = "MANUAL"
                collect_ground_truth_top5(db, week, top5_manual)
                print("\n✅ Top 5 manuels sauvegardés\n")
    else:
        print("\n→ Extraction auto impossible, mode manuel")
        top5_manual = manual_input_top5()
        if top5_manual:
            for t in top5_manual:
                t["source"] = "MANUAL"
            collect_ground_truth_top5(db, week, top5_manual)
            print("\n✅ Top 5 manuels sauvegardés\n")
    
    print("="*70 + "\n")

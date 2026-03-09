#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC AGRÉGATION SÉMANTIQUE
Identifie pourquoi les résultats varient
"""
import os
import sys
from datetime import datetime
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSTIC PUBLICATIONS BRVM - EXTRACTION SYMBOLES")
    print("=" * 80 + "\n")
    
    # Requête identique à agregateur_semantique_actions.py
    docs = list(db.curated_observations.find({
        "$and": [
            {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}},
            {"$or": [
                {"attrs.semantic_scores": {"$exists": True}},
                {"attrs.semantic_score_base": {"$exists": True}}
            ]},
            {"$or": [
                {"attrs.emetteur": {"$exists": True, "$ne": None}},
                {"attrs.symboles": {"$exists": True, "$ne": []}}
            ]}
        ]
    }))
    
    print(f"📰 {len(docs)} publications trouvées avec analyse sémantique\n")
    
    # Statistiques
    stats = {
        "avec_emetteur": 0,
        "avec_symboles": 0,
        "avec_les_deux": 0,
        "sans_symbole": 0,
        "symboles_multiples": 0
    }
    
    symboles_extraits = Counter()
    publications_par_symbole = defaultdict(list)
    symboles_ignores = defaultdict(int)  # Symboles dans liste mais pas utilisés
    
    for doc in docs:
        attrs = doc.get("attrs", {})
        emetteur = attrs.get("emetteur")
        symboles = attrs.get("symboles", [])
        titre = attrs.get("titre", "Sans titre")[:60]
        score_base = attrs.get("semantic_score_base", 0)
        
        # Statistiques structure
        if emetteur and symboles:
            stats["avec_les_deux"] += 1
        elif emetteur:
            stats["avec_emetteur"] += 1
        elif symboles:
            stats["avec_symboles"] += 1
        else:
            stats["sans_symbole"] += 1
        
        # Symboles multiples
        if len(symboles) > 1:
            stats["symboles_multiples"] += 1
        
        # Logique ACTUELLE d'extraction (identique au script)
        symbol = emetteur
        if not symbol:
            symbol = symboles[0] if symboles else None
        
        if symbol:
            symboles_extraits[symbol] += 1
            publications_par_symbole[symbol].append({
                "titre": titre,
                "score": score_base,
                "emetteur": emetteur,
                "symboles": symboles
            })
            
            # Détecter symboles ignorés (présents dans liste mais pas comme emetteur)
            if symboles and len(symboles) > 1:
                for sym_ignore in symboles[1:]:  # Tous sauf le premier
                    symboles_ignores[sym_ignore] += 1
    
    # AFFICHAGE DIAGNOSTIQUE
    print("=" * 80)
    print("📊 STATISTIQUES STRUCTURE DES PUBLICATIONS")
    print("=" * 80)
    print(f"Publications avec emetteur uniquement    : {stats['avec_emetteur']}")
    print(f"Publications avec symboles[] uniquement  : {stats['avec_symboles']}")
    print(f"Publications avec les deux               : {stats['avec_les_deux']}")
    print(f"Publications sans symbole identifiable   : {stats['sans_symbole']}")
    print(f"Publications multi-symboles (>1)         : {stats['symboles_multiples']}")
    
    print("\n" + "=" * 80)
    print("🎯 SYMBOLES EXTRAITS (TOP 20)")
    print("=" * 80)
    for symbol, count in symboles_extraits.most_common(20):
        print(f"{symbol:6s} : {count:3d} publications")
    
    print("\n" + "=" * 80)
    print("⚠️  SYMBOLES IGNORÉS (présents mais pas comptés car pas en 1ère position)")
    print("=" * 80)
    if symboles_ignores:
        for symbol, count in sorted(symboles_ignores.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"{symbol:6s} : {count:3d} fois ignoré")
    else:
        print("✅ Aucun symbole ignoré")
    
    # Exemples de publications multi-symboles
    print("\n" + "=" * 80)
    print("📰 EXEMPLES PUBLICATIONS MULTI-SYMBOLES (Potentiel perte d'information)")
    print("=" * 80)
    multi_count = 0
    for doc in docs:
        attrs = doc.get("attrs", {})
        symboles = attrs.get("symboles", [])
        if len(symboles) > 1:
            multi_count += 1
            if multi_count <= 5:
                titre = attrs.get("titre", "Sans titre")[:70]
                emetteur = attrs.get("emetteur", "None")
                print(f"\nPublication: {titre}")
                print(f"  Émetteur  : {emetteur}")
                print(f"  Symboles  : {', '.join(symboles)}")
                print(f"  → Extrait : {emetteur if emetteur else symboles[0]}")
                print(f"  → Ignorés : {', '.join(symboles[1:]) if not emetteur and len(symboles) > 1 else 'N/A'}")
    
    print(f"\n⚠️  Total publications multi-symboles: {multi_count}")
    
    # Comparaison dates
    print("\n" + "=" * 80)
    print("📅 DISTRIBUTION TEMPORELLE")
    print("=" * 80)
    today = datetime.now()
    recent_7d = 0
    recent_30d = 0
    old_30d = 0
    
    for doc in docs:
        ts = doc.get("ts")
        try:
            if isinstance(ts, str):
                pub_date = datetime.fromisoformat(ts.split('T')[0])
            else:
                pub_date = ts if isinstance(ts, datetime) else today
        except:
            pub_date = today
        
        days_old = (today - pub_date).days
        
        if days_old <= 7:
            recent_7d += 1
        elif days_old <= 30:
            recent_30d += 1
        else:
            old_30d += 1
    
    print(f"Publications ≤ 7 jours  (poids ×2.0) : {recent_7d}")
    print(f"Publications ≤ 30 jours (poids ×1.0) : {recent_30d}")
    print(f"Publications > 30 jours (poids ×0.5) : {old_30d}")
    
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)
    
    if stats["symboles_multiples"] > 0:
        print(f"⚠️  {stats['symboles_multiples']} publications mentionnent plusieurs symboles")
        print("   → Seul le 1er symbole est compté (perte d'information)")
        print("   → Solution: Compter TOUS les symboles mentionnés")
    
    if symboles_ignores:
        total_ignores = sum(symboles_ignores.values())
        print(f"\n⚠️  {total_ignores} références à des symboles sont ignorées")
        print("   → Ces symboles perdent du score de sentiment")
    
    if stats["avec_les_deux"] > 0:
        print(f"\n✅ {stats['avec_les_deux']} publications ont emetteur ET symboles[] (bonne cohérence)")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()

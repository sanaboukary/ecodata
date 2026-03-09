#!/usr/bin/env python3
"""
🔄 ENRICHISSEMENT PUBLICATIONS EXISTANTES - EXTRACTION SYMBOLES
================================================================

Objectif : Trading hebdomadaire prédictif
- Enrichir les 364+ publications existantes avec symboles d'actions
- Permettre l'agrégation sémantique par action
- Détecter les signaux pour position Lundi/Mardi

Exécution : Une seule fois pour mise à jour de la base
"""

import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Import des fonctions d'extraction depuis collecter_publications_brvm.py
from collecter_publications_brvm import extraire_symboles, detecter_type_event


def enrichir_publications():
    """
    Enrichit toutes les publications existantes avec :
    - symboles : liste des actions mentionnées
    - emetteur : symbole principal
    - type_event : DIVIDENDE, RESULTATS, NOTATION, AG, COMMUNIQUE, AUTRE
    """
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("🔄 ENRICHISSEMENT PUBLICATIONS EXISTANTES - EXTRACTION SYMBOLES")
    print("=" * 80)
    
    # Récupérer toutes les publications BRVM et RichBourse
    pubs = list(db.curated_observations.find({
        "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}
    }))
    
    print(f"\n📊 {len(pubs)} publications à enrichir")
    
    if not pubs:
        print("❌ Aucune publication trouvée")
        return
    
    # Statistiques
    stats = {
        "total": len(pubs),
        "enrichies": 0,
        "sans_symbole": 0,
        "multi_actions": 0,
        "par_type": {}
    }
    
    count_enrichi = 0
    count_sans_symbole = 0
    symboles_stats = {}
    
    for pub in pubs:
        attrs = pub.get("attrs", {})
        
        # Si déjà enrichi, skip (sauf si on force)
        if attrs.get("symboles") is not None:
            continue
        
        # Texte complet
        titre = attrs.get("titre", "")
        contenu = attrs.get("contenu", "")
        texte = f"{titre} {contenu}"
        
        # Extraction
        symboles = extraire_symboles(texte)
        type_event = detecter_type_event(texte)
        emetteur = symboles[0] if symboles else None
        
        # Mise à jour
        db.curated_observations.update_one(
            {"_id": pub["_id"]},
            {"$set": {
                "attrs.symboles": symboles,
                "attrs.emetteur": emetteur,
                "attrs.nb_symboles": len(symboles),
                "attrs.type_event": type_event,
                "attrs.is_multi_action": len(symboles) > 1,
                "attrs.full_text": texte[:10000],
                "attrs.description": titre,
                "attrs.enrichi_at": datetime.now().isoformat()
            }}
        )
        
        if symboles:
            count_enrichi += 1
            for s in symboles:
                symboles_stats[s] = symboles_stats.get(s, 0) + 1
            print(f"✓ {emetteur:6s} | {type_event:12s} | {titre[:50]}")
        else:
            count_sans_symbole += 1
    
    print("\n" + "=" * 80)
    print(f"✅ ENRICHISSEMENT TERMINÉ")
    print(f"   • Publications enrichies : {count_enrichi}")
    print(f"   • Publications sans symbole : {count_sans_symbole}")
    print("=" * 80)
    
    if symboles_stats:
        print("\n📊 TOP 10 ACTIONS LES PLUS MENTIONNÉES :\n")
        for symbole, count in sorted(symboles_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {symbole:6s} : {count:3d} publications")
    
    print()


if __name__ == "__main__":
    enrichir_publications()

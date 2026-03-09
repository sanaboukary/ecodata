#!/usr/bin/env python3
"""
🔄 ENRICHISSEMENT PUBLICATIONS EXISTANTES - EXPERT BRVM 30 ANS
===============================================================
Objectif Trading Hebdomadaire : Identifier les actions du Top 5 pour position Lundi/Mardi
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import re

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# ============ DICTIONNAIRE ACTIONS BRVM (47 ACTIONS) ============
ACTIONS_BRVM = {
    "ABJC": ["SUCRIVOIRE", "SUCRE", "ABIDJAN JAMBO CACAO"],
    "BICC": ["BIC", "BICI", "BANQUE INTERNATIONALE POUR LE COMMERCE"],
    "BNBC": ["BERNABE", "BERNABÉ", "USINE SUCRE"],
    "BOAB": ["BOA BENIN", "BOA BN", "BANK OF AFRICA BENIN"],
    "BOABF": ["BOA BURKINA", "BOA BF", "BANK OF AFRICA BURKINA"],
    "BOAC": ["BOA CI", "BOA COTE D'IVOIRE", "BOA CÔTE D'IVOIRE", "BANK OF AFRICA CI"],
    "BOAM": ["BOA MALI", "BOA ML", "BANK OF AFRICA MALI"],
    "BOAN": ["BOA NIGER", "BOA NE", "BANK OF AFRICA NIGER"],
    "BOAS": ["BOA SENEGAL", "BOA SN", "BANK OF AFRICA SENEGAL"],
    "BOAG": ["BOA GUINEE", "BOA GN", "BANK OF AFRICA GUINEE"],
    "CBIBF": ["CORIS BANK", "CORIS BF", "CORIS BURKINA"],
    "CFAC": ["CFAO", "CFAO MOTORS"],
    "CIEC": ["CIE", "COMPAGNIE IVOIRIENNE ELECTRICITE", "CIE CI"],
    "ECOC": ["ECOBANK CI", "ETI", "ECOBANK TRANSNATIONAL"],
    "ETIT": ["ECOBANK TG", "ECOBANK TOGO"],
    "FTSC": ["FILTISAC", "SACS INDUSTRIELS"],
    "NEIC": ["NEI", "NSIA BANQUE CI", "NEI CEDA"],
    "NTLC": ["NESTLE", "NESTLE CI", "NESTLÉ"],
    "NSBC": ["NSIA BANQUE", "NSIA CI"],
    "ONTBF": ["ONATEL", "ONATEL BF", "ONATEL BURKINA"],
    "ORGT": ["ORAGROUP TOGO", "ORAGROUP TG"],
    "PALC": ["PALM CI", "PALMCI", "SICOR", "PALM COTE D'IVOIRE"],
    "PRSC": ["TRACTAFRIC", "TRACTAFRIC MOTORS"],
    "SAFC": ["SIFCA", "SIFCA CI"],
    "SAFH": ["SAFCA HOLDING", "SAFCA"],
    "SGBC": ["SOCIETE GENERALE CI", "SGCI", "SG COTE D'IVOIRE", "SG CI", "SOCIETE GENERALE"],
    "SHEC": ["SHELL CI", "VIVO ENERGY"],
    "SIBC": ["SIB", "SOCIETE IVOIRIENNE DE BANQUE"],
    "SICC": ["SICABLE", "CABLES ELECTRIQUES"],
    "SDCC": ["SODE CI", "SODECI", "SOCIETE DISTRIBUTION EAU"],
    "SDSC": ["SOLIBRA", "BRASSERIE", "BIERE"],
    "SEMC": ["SERVAIR ABIDJAN", "SERVAIR"],
    "SGOC": ["SOGB", "SOCIETE GENERALE BURKINA"],
    "SIVC": ["AIR LIQUIDE", "AIR LIQUIDE CI"],
    "SLBC": ["SETAO", "SLBC CI"],
    "SMBC": ["SMB", "SOCIETE MINIERE BOUKE"],
    "SNTS": ["SONATEL", "ORANGE SENEGAL", "ORANGE SN"],
    "SOGC": ["SOGC"],
    "SPHC": ["SAPH", "PALMAFRIQUE", "HUILE DE PALME"],
    "STAC": ["SITAB", "TABAC"],
    "STBC": ["STBCI", "STANDARD CHARTERED", "STANBIC"],
    "SVOC": ["MOVIS", "MOOV CI"],
    "TTLC": ["TOTAL CI", "TOTALENERGIES CI"],
    "TTLS": ["TOTAL SN", "TOTALENERGIES SENEGAL"],
    "UNXC": ["UNIWAX", "UNIWAX CI", "TEXTILE"],
    "TTRC": ["TRITURAF", "TRITURATION"],
    "CABC": ["CORIS BANK CI", "CORIS COTE IVOIRE"],
}

# Mapping inverse : nom → symbole
NOM_VERS_SYMBOLE = {}
for symbole, variantes in ACTIONS_BRVM.items():
    for variante in variantes:
        NOM_VERS_SYMBOLE[variante.upper()] = symbole

# ============ FONCTIONS EXTRACTION ============

def extraire_symboles(texte: str) -> list:
    """Extrait les symboles d'actions BRVM mentionnés"""
    if not texte:
        return []
    
    texte_upper = texte.upper()
    symboles_trouves = set()
    
    # 1. Codes boursiers (4 lettres)
    codes_pattern = r'\b(' + '|'.join(ACTIONS_BRVM.keys()) + r')\b'
    for match in re.finditer(codes_pattern, texte_upper):
        symboles_trouves.add(match.group(1))
    
    # 2. Noms d'entreprises
    for nom, symbole in NOM_VERS_SYMBOLE.items():
        if nom in texte_upper:
            symboles_trouves.add(symbole)
    
    return sorted(list(symboles_trouves))


def detecter_type_event(texte: str) -> str:
    """Détecte le type d'événement financier"""
    if not texte:
        return "AUTRE"
    
    texte_lower = texte.lower()
    
    if any(kw in texte_lower for kw in ["dividende", "distribution", "coupon"]):
        return "DIVIDENDE"
    
    if any(kw in texte_lower for kw in ["résultat", "resultat", "bénéfice", "benefice", "chiffre d'affaires", "ca ", "trimestre", "semestriel", "annuel"]):
        return "RESULTATS"
    
    if any(kw in texte_lower for kw in ["notation", "rating", "note", "dégradation", "amélioration note"]):
        return "NOTATION"
    
    if any(kw in texte_lower for kw in ["assemblée générale", "assemblee generale", "ag ", "convocation", "ago", "age"]):
        return "AG"
    
    if any(kw in texte_lower for kw in ["communiqué", "communique", "annonce"]):
        return "COMMUNIQUE"
    
    return "AUTRE"

# ============ ENRICHISSEMENT ============

def enrichir_base():
    """Enrichit les 364 publications existantes avec extraction symboles"""
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("🔄 ENRICHISSEMENT PUBLICATIONS - EXPERT BRVM 30 ANS")
    print("🎯 Objectif : Identifier actions Top 5 pour trading Lundi/Mardi")
    print("=" * 80)
    
    # Comptage total
    total_pubs = db.curated_observations.count_documents({
        "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}
    })
    
    print(f"\n📊 {total_pubs} publications à enrichir\n")
    
    # Traitement par batch (évite surcharge mémoire)
    batch_size = 100
    offset = 0
    
    stats = {
        "enrichies": 0,
        "avec_symboles": 0,
        "sans_symboles": 0,
        "par_type": {},
        "par_symbole": {}
    }
    
    while offset < total_pubs:
        pubs = list(db.curated_observations.find({
            "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}
        }).skip(offset).limit(batch_size))
        
        for pub in pubs:
            attrs = pub.get("attrs", {})
            
            # Texte complet
            titre = attrs.get("titre", "")
            contenu = attrs.get("contenu") or attrs.get("full_text") or attrs.get("description", "")
            texte_complet = f"{titre} {contenu}"
            
            # Extraction
            symboles = extraire_symboles(texte_complet)
            type_event = detecter_type_event(texte_complet)
            emetteur = symboles[0] if symboles else None
            
            # Mise à jour MongoDB
            db.curated_observations.update_one(
                {"_id": pub["_id"]},
                {"$set": {
                    "attrs.symboles": symboles,
                    "attrs.emetteur": emetteur,
                    "attrs.nb_symboles": len(symboles),
                    "attrs.type_event": type_event,
                    "attrs.is_multi_action": len(symboles) > 1,
                    "attrs.full_text": texte_complet[:10000],
                    "attrs.description": titre
                }}
            )
            
            # Stats
            stats["enrichies"] += 1
            if symboles:
                stats["avec_symboles"] += 1
                for s in symboles:
                    stats["par_symbole"][s] = stats["par_symbole"].get(s, 0) + 1
                print(f"✓ {emetteur:6s} | {type_event:12s} | {titre[:55]}")
            else:
                stats["sans_symboles"] += 1
            
            stats["par_type"][type_event] = stats["par_type"].get(type_event, 0) + 1
        
        offset += batch_size
        print(f"\n   [{offset}/{total_pubs}] publications traitées...")
    
    # ============ RAPPORT FINAL ============
    print("\n" + "=" * 80)
    print("📈 RAPPORT D'ENRICHISSEMENT - EXPERT BRVM")
    print("=" * 80)
    print(f"Publications enrichies      : {stats['enrichies']}")
    print(f"Avec symboles identifiés    : {stats['avec_symboles']}")
    print(f"Sans symbole                : {stats['sans_symboles']}")
    
    print("\n📊 Répartition par type d'événement :")
    for type_event, count in sorted(stats["par_type"].items(), key=lambda x: x[1], reverse=True):
        print(f"   {type_event:15s} : {count:4d}")
    
    print("\n🎯 TOP 10 ACTIONS LES PLUS MENTIONNÉES (Trading Hebdomadaire) :")
    top10 = sorted(stats["par_symbole"].items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (symbole, count) in enumerate(top10, 1):
        print(f"   {i:2d}. {symbole:6s} → {count:4d} publications")
    
    print("\n✅ Base enrichie - Prête pour agrégation sémantique")
    print("🚀 PROCHAINE ÉTAPE : Réparer agregateur_semantique_actions.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    enrichir_base()

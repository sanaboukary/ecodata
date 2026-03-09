#!/usr/bin/env python3
"""
Test rapide de l'extraction de symboles
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Test direct sans Django
import re

ACTIONS_BRVM = {
    "SNTS": ["SONATEL", "ORANGE SENEGAL", "ORANGE SN"],
    "SGBC": ["SOCIETE GENERALE CI", "SGCI", "SG COTE D'IVOIRE", "SG CI"],
    "BOAC": ["BOA CI", "BOA COTE D'IVOIRE", "BOA CÔTE D'IVOIRE", "BANK OF AFRICA CI"],
    "PALC": ["PALM CI", "PALMCI", "SICOR", "PALM COTE D'IVOIRE"],
    "BICC": ["BIC", "BICI", "BANQUE INTERNATIONALE POUR LE COMMERCE"],
}

NOM_VERS_SYMBOLE = {}
for symbole, variantes in ACTIONS_BRVM.items():
    for variante in variantes:
        NOM_VERS_SYMBOLE[variante.upper()] = symbole

def extraire_symboles(texte: str) -> list:
    if not texte:
        return []
    
    texte_upper = texte.upper()
    symboles_trouves = set()
    
    # 1. Recherche directe des codes boursiers (4 lettres)
    codes_pattern = r'\b(' + '|'.join(ACTIONS_BRVM.keys()) + r')\b'
    for match in re.finditer(codes_pattern, texte_upper):
        symboles_trouves.add(match.group(1))
    
    # 2. Recherche des noms d'entreprises
    for nom, symbole in NOM_VERS_SYMBOLE.items():
        if nom in texte_upper:
            symboles_trouves.add(symbole)
    
    return sorted(list(symboles_trouves))

# Tests
tests = [
    "SNTS annonce un dividende exceptionnel de 2000 FCFA",
    "Société Générale CI : résultats semestriels en hausse",
    "BOA CI et PALM CI signent un partenariat stratégique",
    "SGBC affiche une progression de 15%",
    "Rapport d'activité BICC - 2025",
]

print("\n=== TESTS D'EXTRACTION DE SYMBOLES ===\n")
for test in tests:
    symboles = extraire_symboles(test)
    print(f"Texte   : {test}")
    print(f"Symboles: {symboles}")
    print()

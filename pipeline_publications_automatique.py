#!/usr/bin/env python3
"""
PIPELINE AUTOMATISÉE : Collecte, Extraction Texte, Analyse Sentiment
==================================================================
Ce script lance en séquence :
- La collecte des publications (officielles + RichBourse)
- L'extraction du texte intégral (HTML & PDF)
- L'analyse de sentiment sur les publications enrichies
"""
import subprocess
import sys

def run_step(cmd, desc):
    print(f"\n=== {desc} ===\n")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[ERREUR] {desc} échoué.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    # Utilisation de sys.executable pour garantir le bon interpréteur Python
    py = sys.executable
    run_step(f'"{py}" collecter_publications_brvm.py', "Collecte des publications (officielles + RichBourse)")
    run_step(f'"{py}" fetch_and_parse_publications_fulltext.py', "Extraction du texte intégral (HTML & PDF)")
    run_step(f'"{py}" analyser_sentiment_publications.py', "Analyse de sentiment sur les publications")
    print("\n✅ Pipeline complet exécuté avec succès !")

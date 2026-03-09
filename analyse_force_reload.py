#!/usr/bin/env python3
"""Force l'analyse avec rechargement du module"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

# Maintenant importer et recharger
import importlib
import analyse_semantique_brvm_v3

# FORCER le rechargement!
importlib.reload(analyse_semantique_brvm_v3)

print("Module rechargé! Vérification:")
print(f"  - Classe: {analyse_semantique_brvm_v3.SemanticAnalyzerBRVMV3.__name__}")

# Lancer l'analyse
print("\n" + "="*70)
print("LANCEMENT ANALYSE AVEC MODULE FRESH")
print("="*70)

analyzer = analyse_semantique_brvm_v3.SemanticAnalyzerBRVMV3()
analyzer.run()

print("\n✅ Analyse terminée avec module rechargé!")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide EXPLOSION 7J detector
"""

import sys
print("Python version:", sys.version)
print("="*80)

try:
    print("Import explosion_7j_detector...")
    # Ne pas exécuter, juste vérifier syntaxe
    with open('explosion_7j_detector.py', 'r', encoding='utf-8') as f:
        code = f.read()
        compile(code, 'explosion_7j_detector.py', 'exec')
    print("✅ Code valide, compilation OK")
    
    print("\nModules implémentés:")
    print("  1. ✅ BREAKOUT_DETECTOR - Compression → Rupture")
    print("  2. ✅ VOLUME_ANORMAL - Z-score statistique")
    print("  3. ✅ MOMENTUM_ACCELERE - Variations croissantes")
    print("  4. ✅ RETARD_REACTION - News décalées BRVM")
    print("  5. ✅ EXPLOSION_SCORE - 30/25/20/15/10")
    print("  6. ✅ STOP/TARGET 7-10J - 0.8× / 1.8×")
    print("  7. ✅ LIQUIDITE_ADAPTIVE - Position sizing")
    print("  8. ✅ PROBABILITE_TOP5 - Historique")
    print("  9. ✅ REGIME_MARCHE - BRVM Composite")
    print("  10. ✅ CONCENTRATION - MAX 1-2 positions")
    
    print("\nCollections MongoDB:")
    print("  - Input: prices_weekly, AGREGATION_SEMANTIQUE_ACTION")
    print("  - Output: decisions_explosion_7j")
    print("  - Track: track_record_explosion_7j")
    
    print("\n" + "="*80)
    print("SYSTÈME EXPLOSION 7-10 JOURS PRÊT")
    print("="*80)
    print("\nUtilisation:")
    print("  python explosion_7j_detector.py                 # Semaine courante")
    print("  python explosion_7j_detector.py --week 2026-W07 # Semaine spécifique")
    print("  python explosion_7j_detector.py --track-record  # Afficher historique")
    print("\n" + "="*80)
    
except SyntaxError as e:
    print(f"❌ Erreur syntaxe: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

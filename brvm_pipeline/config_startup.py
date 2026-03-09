#!/usr/bin/env python3
"""
🟡 CONFIGURATION DÉMARRAGE - Indicateurs adaptés historique limité
À utiliser tant qu'on n'a pas 14+ semaines de données
"""

# Mode démarrage : indicateurs simplifiés
RSI_PERIOD_STARTUP = 5      # Au lieu de 14
ATR_PERIOD_STARTUP = 5      # Au lieu de 8
SMA_FAST_STARTUP = 3        # Au lieu de 5
SMA_SLOW_STARTUP = 5        # Au lieu de 10
VOLATILITY_PERIOD_STARTUP = 5  # Au lieu de 12
VOLUME_PERIOD_STARTUP = 5   # Au lieu de 8

# Seuil minimum de semaines pour calculer
MIN_WEEKS_STARTUP = 5

print("""
⚠️  MODE DÉMARRAGE ACTIVÉ

Configuration adaptée pour démarrer avec historique limité (5-8 semaines).
Les indicateurs seront moins précis mais permettront de générer TOP5.

Configuration:
- RSI: 5 semaines (au lieu de 14)
- ATR: 5 semaines (au lieu de 8)  
- SMA: 3/5 (au lieu de 5/10)
- Volatilité: 5 semaines (au lieu de 12)

🔄 Basculer vers config PRODUCTION une fois 14+ semaines accumulées
""")

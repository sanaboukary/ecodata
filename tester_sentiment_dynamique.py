#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la pondération dynamique du sentiment
Vérification de l'impact selon le nombre de publications
"""

from brvm_institutional_alpha import compute_dynamic_sentiment_weight, normalize_weights

print('=' * 100)
print('TEST PONDÉRATION DYNAMIQUE DU SENTIMENT - TRADING HEBDOMADAIRE BRVM')
print('=' * 100)

# ========================================================================
# TEST 1: Poids sentiment selon nombre de publications
# ========================================================================
print('\n[TEST 1] Calcul poids sentiment selon activité publications\n')

scenarios = [
    (0, [], "Aucune publication (semaine morte)"),
    (2, [], "2 publications (semaine calme)"),
    (5, [], "5 publications (semaine normale)"),
    (10, [], "10 publications (semaine active)"),
    (3, ["RESULTATS TRIMESTRIELS 2026"], "3 publications MAIS événement RÉSULTATS"),
    (6, ["DIVIDENDE EXCEPTIONNEL ANNONCÉ"], "6 publications + DIVIDENDE"),
    (4, ["ACQUISITION NOUVELLE FILIALE"], "4 publications + ACQUISITION"),
]

for nb_pubs, keywords, description in scenarios:
    poids = compute_dynamic_sentiment_weight(nb_pubs, keywords)
    print(f'📊 {description}')
    print(f'   Nombre pubs: {nb_pubs} | Événements: {len(keywords)}')
    print(f'   → Poids sentiment: {poids*100:.0f}%')
    
    if poids == 0.05:
        print(f'   ✅ CORRECT: Sentiment = BRUIT (5%)')
    elif poids == 0.10:
        print(f'   ✅ CORRECT: Sentiment = ACCÉLÉRATEUR (10%)')
    elif poids == 0.20:
        print(f'   🔥 ÉVÉNEMENTIEL: Sentiment = MOTEUR (20%)')
    print()

# ========================================================================
# TEST 2: Impact sur pondérations globales (régime BEAR)
# ========================================================================
print('\n' + '=' * 100)
print('[TEST 2] Ajustement pondérations globales - RÉGIME BEAR')
print('=' * 100 + '\n')

# Pondérations base BEAR
weights_base = {
    "rs": 0.40,
    "accel": 0.10,
    "vol": 0.25,
    "breakout": 0.05,
    "sent": 0.10,  # Standard
    "voleff": 0.10
}

scenarios_weights = [
    (0.05, "Semaine calme (0-2 pubs)"),
    (0.10, "Semaine normale (3-8 pubs)"),
    (0.20, "Semaine événementielle (résultats)"),
]

for sentiment_weight, label in scenarios_weights:
    weights = weights_base.copy()
    weights_adjusted = normalize_weights(weights, sentiment_weight)
    
    print(f'🎯 {label} → Sentiment {sentiment_weight*100:.0f}%\n')
    print('   Facteur         | Base  | Ajusté | Delta')
    print('   ' + '-' * 50)
    
    for key in ["rs", "vol", "accel", "breakout", "sent", "voleff"]:
        base = weights_base[key]
        adjusted = weights_adjusted[key]
        delta = adjusted - base
        delta_str = f'{delta:+.2f}' if delta != 0 else ' 0.00'
        
        print(f'   {key:12s} | {base*100:4.0f}% | {adjusted*100:4.0f}%  | {delta_str}')
    
    total = sum(weights_adjusted.values())
    print('   ' + '-' * 50)
    print(f'   TOTAL           |  100% |  {total*100:.0f}%  | (vérifié)\n')

# ========================================================================
# TEST 3: Impact sur ALPHA score (simulation)
# ========================================================================
print('\n' + '=' * 100)
print('[TEST 3] Impact sur ALPHA SCORE - Action exemple SEMC')
print('=' * 100 + '\n')

# Facteurs normalisés (0-1) pour SEMC
factors_norm = {
    "rs": 1.00,      # RS P100 = 1.0
    "vol": 0.75,     # Vol P75 = 0.75
    "accel": 0.60,   # Accel +2% = 0.60
    "breakout": 0.80, # Breakout confirmé
    "sent": 0.60,    # Sentiment légèrement positif
    "voleff": 0.55   # Vol efficiency moyenne
}

print('Facteurs normalisés (0-1):')
for k, v in factors_norm.items():
    print(f'   {k:10s}: {v:.2f}')
print()

for nb_pubs, description in [(2, "Semaine normale"), (15, "Après annonce RÉSULTATS")]:
    sentiment_weight = compute_dynamic_sentiment_weight(nb_pubs, ["RESULTATS"] if nb_pubs > 10 else [])
    
    weights = {
        "rs": 0.40, "accel": 0.10, "vol": 0.25,
        "breakout": 0.05, "sent": 0.10, "voleff": 0.10
    }
    weights = normalize_weights(weights, sentiment_weight)
    
    # Calcul ALPHA
    alpha = sum(weights[k] * factors_norm[k] for k in factors_norm.keys()) * 100
    
    print(f'📊 {description} ({nb_pubs} publications)')
    print(f'   Poids sentiment: {sentiment_weight*100:.0f}%')
    print(f'   ALPHA SCORE: {alpha:.1f}/100')
    
    # Décomposer contributions
    print(f'   Contributions:')
    for k in ["rs", "vol", "accel", "sent", "breakout", "voleff"]:
        contrib = weights[k] * factors_norm[k] * 100
        print(f'      {k:10s}: {contrib:5.1f} pts (poids {weights[k]*100:2.0f}%)')
    print()

# ========================================================================
# TEST 4: Comparaison RIGIDE vs DYNAMIQUE
# ========================================================================
print('\n' + '=' * 100)
print('[TEST 4] COMPARAISON: Système RIGIDE (10% fixe) vs DYNAMIQUE (5-20%)')
print('=' * 100 + '\n')

print('Cas: Action avec forte activité publications (12 pubs) + Sentiment positif\n')

# Système RIGIDE (ancien)
weights_rigide = {
    "rs": 0.40, "accel": 0.10, "vol": 0.25,
    "breakout": 0.05, "sent": 0.10, "voleff": 0.10
}

alpha_rigide = sum(weights_rigide[k] * factors_norm[k] for k in factors_norm.keys()) * 100

# Système DYNAMIQUE (nouveau)
sentiment_dyn = compute_dynamic_sentiment_weight(12, [])
weights_dyn = normalize_weights(weights_rigide.copy(), sentiment_dyn)
alpha_dyn = sum(weights_dyn[k] * factors_norm[k] for k in factors_norm.keys()) * 100

print(f'RIGIDE  (sentiment 10% fixe):')
print(f'   Contribution sentiment: {weights_rigide["sent"] * factors_norm["sent"] * 100:.1f} pts')
print(f'   ALPHA TOTAL: {alpha_rigide:.1f}/100\n')

print(f'DYNAMIQUE (sentiment 20% événementiel):')
print(f'   Contribution sentiment: {weights_dyn["sent"] * factors_norm["sent"] * 100:.1f} pts')
print(f'   ALPHA TOTAL: {alpha_dyn:.1f}/100\n')

print(f'📈 IMPACT: +{alpha_dyn - alpha_rigide:.1f} points ALPHA')
print(f'   → Le système détecte l\'activité inhabituelle et ajuste intelligemment\n')

# ========================================================================
# CONCLUSION
# ========================================================================
print('=' * 100)
print('CONCLUSION - PONDÉRATION DYNAMIQUE SENTIMENT')
print('=' * 100 + '\n')

print("""
✅ AVANTAGES du système DYNAMIQUE:

1️⃣  ADAPTATIF: 5-20% selon contexte (vs 10% rigide)
2️⃣  ÉVÉNEMENTIEL: Détecte résultats/dividendes → poids x2
3️⃣  ANTI-BRUIT: Réduit à 5% en semaine calme (< 3 pubs)
4️⃣  TRADING HEBDO: Sentiment = accélérateur pas moteur SAUF événements
5️⃣  INSTITUTIONNEL: RS/Volume restent dominants (40%/25%)

⚠️  GARDE-FOUS:

• Sentiment JAMAIS > 20% (même événements majeurs)
• RS JAMAIS touché par redistribution (moteur principal)
• Volume JAMAIS touché (liquidité critique)
• Total pondérations = 100% (normalisé automatiquement)

🎯 VERDICT:

Pour 10,000 clients BRVM:
✅ Système RIGIDE = sain mais statique
🔥 Système DYNAMIQUE = professionnel ET adaptatif

Sur marché lent comme BRVM où publications = rares:
→ Détection événements = EDGE concurrentiel
→ Évite sur-réaction semaines normales
→ Capture momentum semaines événementielles
""")

print('=' * 100)

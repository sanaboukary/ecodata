"""
TOP 5 RAPIDE - 22 DÉCEMBRE 2025
Génération recommandations sur données réelles du jour
"""
import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime
import json

client, db = get_mongo_db()

print("\n" + "="*80)
print("TOP 5 RECOMMANDATIONS - 22 DÉCEMBRE 2025")
print("="*80)

# Récupérer toutes les actions du 22/12
actions = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': '2025-12-22',
    'value': {'$gt': 0}  # Exclure prix = 0
}))

print(f"\n📊 {len(actions)} actions analysées")

# Calculer scores simples (momentum + volume)
scored = []
for obs in actions:
    symbol = obs['key']
    price = obs['value']
    variation = obs['attrs'].get('variation', 0)
    volume = obs['attrs'].get('volume', 0)
    quality = obs['attrs'].get('data_quality', 'UNKNOWN')
    
    # Score simple: variation positive = bon signal
    score = 0
    if variation > 5:
        score += 40  # Forte hausse
    elif variation > 2:
        score += 30  # Hausse modérée
    elif variation > 0:
        score += 20  # Légère hausse
    
    if volume > 500:
        score += 10  # Volume significatif
    
    if quality == 'REAL_SCRAPER':
        score += 5  # Bonus pour données scrapées (plus fiables)
    
    if score >= 30:  # Seuil minimum
        scored.append({
            'symbol': symbol,
            'score': score,
            'price': price,
            'variation': variation,
            'volume': volume,
            'quality': quality
        })

# Trier par score
scored.sort(key=lambda x: x['score'], reverse=True)

print(f"✅ {len(scored)} opportunités identifiées (score ≥30)\n")

# Top 5
top5 = scored[:5]

print(f"{'RANG':<6} {'SYMBOLE':<12} {'SCORE':>6} {'PRIX':>12} {'VAR':>8} {'VOLUME':>10}")
print(f"{'-'*6} {'-'*12} {'-'*6} {'-'*12} {'-'*8} {'-'*10}")

for i, action in enumerate(top5, 1):
    print(f"{i:<6} {action['symbol']:<12} {action['score']:>6} {action['price']:>12,.0f} {action['variation']:>+7.2f}% {action['volume']:>10,}")

# Sauvegarder JSON
output = {
    'date_generation': datetime.now().isoformat(),
    'date_marche': '2025-12-22',
    'total_actions': len(actions),
    'total_opportunites': len(scored),
    'top_5': top5
}

filename = f"top5_rapide_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n💾 Sauvegardé: {filename}")

client.close()

print(f"\n{'='*80}")
print(f"✅ TOP 5 GÉNÉRÉ AVEC DONNÉES DU 22/12/2025")
print(f"{'='*80}\n")

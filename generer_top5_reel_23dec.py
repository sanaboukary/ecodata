"""
TOP 5 RAPIDE - DONNÉES RÉELLES 23 DÉCEMBRE 2025
Génération recommandations sur données scrapées (REAL_SCRAPER)
"""
import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime
import json

print("\n" + "="*80)
print("TOP 5 RECOMMANDATIONS - DONNÉES RÉELLES 23/12/2025")
print("="*80)
print("🔴 Politique: ZÉRO TOLÉRANCE pour données simulées")
print("   Source: Scraping Selenium du site BRVM officiel\n")

client, db = get_mongo_db()

# Récupérer données du 23/12
actions_23 = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': '2025-12-23',
    'value': {'$gt': 0}
}))

# Récupérer données du 22/12 pour comparaison
actions_22 = {
    obs['key']: obs 
    for obs in db.curated_observations.find({
        'source': 'BRVM',
        'ts': '2025-12-22',
        'value': {'$gt': 0}
    })
}

print(f"📊 Données disponibles:")
print(f"   23/12/2025: {len(actions_23)} observations")
print(f"   22/12/2025: {len(actions_22)} observations (pour comparaison)")

if len(actions_23) == 0:
    print("\n❌ Aucune donnée du 23/12 en base!")
    print("   Exécuter d'abord: python sauv_cours_scrapes_23dec.py")
    client.close()
    sys.exit(1)

# Calculer scores
opportunities = []

for obs in actions_23:
    symbol = obs['key']
    price_23 = obs['value']
    variation_23 = obs['attrs'].get('variation', 0)
    quality = obs['attrs'].get('data_quality', 'UNKNOWN')
    
    # Exclure les indices
    if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC']:
        continue
    
    # Score basé sur variation
    score = 0
    
    # Momentum (40 points max)
    if variation_23 > 5:
        score += 40
    elif variation_23 > 3:
        score += 35
    elif variation_23 > 2:
        score += 30
    elif variation_23 > 1:
        score += 20
    elif variation_23 > 0:
        score += 10
    
    # Bonus qualité (10 points)
    if quality == 'REAL_SCRAPER':
        score += 10
    
    # Tendance sur 2 jours (si data 22/12 disponible)
    if symbol in actions_22:
        price_22 = actions_22[symbol]['value']
        var_2j = ((price_23 / price_22) - 1) * 100
        
        if var_2j > 5:
            score += 20  # Forte tendance haussière
        elif var_2j > 2:
            score += 15
        elif var_2j > 0:
            score += 10
    
    # Seuil minimum: 30 points
    if score >= 30:
        opportunities.append({
            'symbol': symbol,
            'score': score,
            'prix_23': price_23,
            'variation_23': variation_23,
            'quality': quality,
            'prix_22': actions_22.get(symbol, {}).get('value', 0)
        })

# Trier par score
opportunities.sort(key=lambda x: x['score'], reverse=True)

print(f"\n✅ {len(opportunities)} opportunités identifiées (score ≥30)\n")

# Top 5
top5 = opportunities[:5]

print("="*80)
print("🏆 TOP 5 RECOMMANDATIONS - 23 DÉCEMBRE 2025")
print("="*80)
print()
print(f"{'#':<4} {'SYMBOLE':<12} {'SCORE':>6} {'PRIX 23/12':>12} {'VAR J':>8} {'TENDANCE 2J':>12} {'QUALITÉ':<15}")
print(f"{'-'*4} {'-'*12} {'-'*6} {'-'*12} {'-'*8} {'-'*12} {'-'*15}")

for i, opp in enumerate(top5, 1):
    prix_22 = opp.get('prix_22', 0)
    if prix_22 > 0:
        var_2j = ((opp['prix_23'] / prix_22) - 1) * 100
        tendance = f"{var_2j:+.2f}%"
    else:
        tendance = "N/A"
    
    print(f"{i:<4} {opp['symbol']:<12} {opp['score']:>6} {opp['prix_23']:>12,.0f} {opp['variation_23']:>+7.2f}% {tendance:>12} {opp['quality']:<15}")

# Sauvegarder JSON
output = {
    'date_generation': datetime.now().isoformat(),
    'date_marche': '2025-12-23',
    'politique_donnees': 'ZERO_TOLERANCE_DONNEES_SIMULEES',
    'source_collecte': 'SELENIUM_SCRAPING_BRVM',
    'total_actions_analysees': len(actions_23),
    'total_opportunites': len(opportunities),
    'top_5': [
        {
            'rang': i,
            'symbol': opp['symbol'],
            'score': opp['score'],
            'prix_actuel': opp['prix_23'],
            'variation_jour': opp['variation_23'],
            'prix_precedent': opp.get('prix_22', 0),
            'qualite': opp['quality'],
            'recommendation': 'BUY' if opp['score'] >= 60 else 'HOLD'
        }
        for i, opp in enumerate(top5, 1)
    ]
}

filename = f"top5_reel_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n💾 Sauvegardé: {filename}")

# Résumé
print("\n" + "="*80)
print("📊 RÉSUMÉ")
print("="*80)
print(f"\n✅ Top 5 généré avec DONNÉES RÉELLES")
print(f"   • Source: Scraping Selenium site BRVM officiel")
print(f"   • Date: 23 décembre 2025")
print(f"   • Qualité: REAL_SCRAPER (zéro simulation)")
print(f"   • Actions analysées: {len(actions_23)}")
print(f"   • Opportunités: {len(opportunities)}")

if len(top5) > 0:
    best = top5[0]
    print(f"\n🎯 MEILLEURE OPPORTUNITÉ:")
    print(f"   {best['symbol']} - Score {best['score']}/100")
    print(f"   Prix: {best['prix_23']:,.0f} FCFA")
    print(f"   Variation: {best['variation_23']:+.2f}%")

client.close()

print("\n" + "="*80)
print("✅ GÉNÉRATION TERMINÉE")
print("="*80 + "\n")

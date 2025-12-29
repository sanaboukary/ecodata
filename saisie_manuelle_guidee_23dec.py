"""
GUIDE DE COLLECTE MANUELLE - BRVM 23 DÉCEMBRE 2025
🔴 DONNÉES RÉELLES UNIQUEMENT - Saisie guidée depuis site officiel

INSTRUCTIONS:
1. Ouvrir: https://www.brvm.org/fr/investir/cours-et-cotations
2. Pour CHAQUE action visible, noter:
   - Symbole
   - Cours de clôture
   - Variation %
   - Volume (si disponible)
3. Remplir le dictionnaire COURS_REELS_23DEC ci-dessous
4. Relancer ce script
"""
import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

print("\n" + "="*80)
print("SAISIE MANUELLE GUIDÉE - VRAIS COURS BRVM")
print("="*80)
print("\n🔴 POLITIQUE: ZÉRO TOLÉRANCE pour données inventées")
print("   Source OBLIGATOIRE: https://www.brvm.org/fr/investir/cours-et-cotations")

# 📋 TEMPLATE À REMPLIR AVEC LES VRAIS COURS DU SITE
COURS_REELS_23DEC = {
    # FORMAT: 'SYMBOLE': {'close': PRIX, 'variation': VAR%, 'volume': VOL},
    
    # === COPIER ICI LES VRAIS COURS DU SITE BRVM ===
    # Exemple (À REMPLACER par les vraies valeurs):
    # 'ECOC': {'close': 15100, 'variation': 0.67, 'volume': 1400},
    # 'SNTS': {'close': 17850, 'variation': 2.00, 'volume': 2800},
    # ... etc pour TOUTES les actions affichées sur le site
    
    # ⚠️ NE PAS INVENTER DE VALEURS - Copier uniquement ce qui est sur le site
}

print(f"\n📊 Actions configurées: {len(COURS_REELS_23DEC)}")

if len(COURS_REELS_23DEC) == 0:
    print("\n" + "="*80)
    print("⚠️  DICTIONNAIRE VIDE - AUCUNE DONNÉE À SAUVEGARDER")
    print("="*80)
    print("\n📋 INSTRUCTIONS:")
    print("\n1. Ouvrir le site BRVM:")
    print("   https://www.brvm.org/fr/investir/cours-et-cotations")
    print("\n2. Pour chaque action, noter:")
    print("   - Symbole (ex: ECOC, SNTS, BICC, etc.)")
    print("   - Cours de clôture")
    print("   - Variation en %")
    print("   - Volume de transactions")
    print("\n3. Remplir le dictionnaire COURS_REELS_23DEC dans ce fichier:")
    print(f"   {__file__}")
    print("\n4. Relancer ce script")
    print("\n" + "="*80)
    sys.exit(0)

# Demander confirmation
print("\n⚠️  VÉRIFICATION CRITIQUE:")
print(f"   • Avez-vous copié les VRAIS cours du site BRVM?")
print(f"   • Date: 23 décembre 2025")
print(f"   • Aucune valeur inventée?")

reponse = input("\n   Confirmer que les données sont RÉELLES (o/N): ").strip().lower()

if reponse not in ['o', 'oui', 'y', 'yes']:
    print("\n❌ Sauvegarde annulée - Vérifiez vos données")
    sys.exit(0)

# Sauvegarder
client, db = get_mongo_db()

today = '2025-12-23'
observations = []

for symbol, data in COURS_REELS_23DEC.items():
    # Normaliser le symbole
    if '.' not in symbol:
        symbol += '.BC'
    
    obs = {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'key': symbol,
        'ts': today,
        'value': data['close'],
        'attrs': {
            'close': data['close'],
            'variation': data.get('variation', 0),
            'volume': data.get('volume', 0),
            'data_quality': 'REAL_MANUAL',
            'collecte_method': 'SAISIE_MANUELLE_GUIDEE',
            'collecte_datetime': datetime.now().isoformat()
        }
    }
    observations.append(obs)

# Upsert
inserted = 0
updated = 0

print(f"\n💾 Sauvegarde de {len(observations)} observations...")

for obs in observations:
    result = db.curated_observations.update_one(
        {
            'source': obs['source'],
            'dataset': obs['dataset'],
            'key': obs['key'],
            'ts': obs['ts']
        },
        {'$set': obs},
        upsert=True
    )
    
    if result.upserted_id:
        inserted += 1
        print(f"   ✅ {obs['key']}: {obs['value']:,.0f} FCFA (nouveau)")
    elif result.modified_count > 0:
        updated += 1
        print(f"   🔄 {obs['key']}: {obs['value']:,.0f} FCFA (mis à jour)")

print(f"\n{'='*80}")
print(f"✅ SAUVEGARDE TERMINÉE")
print(f"{'='*80}")
print(f"\n📊 Résultats:")
print(f"   • {inserted} nouvelles observations")
print(f"   • {updated} observations mises à jour")
print(f"   • Total: {len(observations)} cours RÉELS saisis")

# Vérifier le total
total = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': '2025-12-23'
})

print(f"\n📈 Total observations BRVM du 23/12/2025: {total}")

client.close()

print(f"\n{'='*80}")
print(f"🎯 PROCHAINE ÉTAPE:")
print(f"   python generer_top5_nlp.py")
print(f"\n{'='*80}\n")

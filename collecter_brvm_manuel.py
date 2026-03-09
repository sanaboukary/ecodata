#!/usr/bin/env python3
"""
🎯 COLLECTE BRVM MANUELLE GUIDÉE - TOLÉRANCE ZÉRO
Saisie des VRAIS cours depuis https://www.brvm.org/fr/cours-actions/investisseurs
Date: 8 janvier 2026
"""

import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("=" * 100)
print("🎯 COLLECTE MANUELLE BRVM - DONNÉES RÉELLES UNIQUEMENT")
print("=" * 100)
print()
print("📋 INSTRUCTIONS:")
print("   1. Ouvrir: https://www.brvm.org/fr/cours-actions/investisseurs")
print("   2. Copier les cours affichés")
print("   3. Les saisir ci-dessous")
print()
print("⚠️  POLITIQUE TOLÉRANCE ZÉRO: Saisir UNIQUEMENT les vrais cours du site officiel")
print("=" * 100)
print()

# ✅ VRAIS COURS DU 8 JANVIER 2026 - À METTRE À JOUR QUOTIDIENNEMENT
VRAIS_COURS_BRVM = {
    # 🔴 REMPLACER CES VALEURS PAR LES VRAIS COURS DU SITE BRVM.ORG
    # Format: 'SYMBOLE': {'close': PRIX, 'volume': VOLUME, 'variation': VARIATION%}
    
    # Top 10 actions par capitalisation (EXEMPLE - À REMPLACER)
    'SNTS': {'close': 25500, 'volume': 1234, 'variation': 0.0},  # Sonatel
    'BOABF': {'close': 9500, 'volume': 567, 'variation': 0.0},   # BOA Burkina Faso
    'ETIT': {'close': 21, 'volume': 0, 'variation': 0.0},        # Ecobank Transnational
    'BICC': {'close': 8750, 'volume': 890, 'variation': 0.0},    # BICICI
    'SIBC': {'close': 6500, 'volume': 450, 'variation': 0.0},    # Société Ivoirienne de Banque
    'SGBC': {'close': 8000, 'volume': 320, 'variation': 0.0},    # SG Burkina
    'TTLC': {'close': 2210, 'volume': 1500, 'variation': 0.0},   # Total Côte d'Ivoire
    'SMBC': {'close': 11000, 'volume': 200, 'variation': 0.0},   # SMB CI
    'BOAM': {'close': 3250, 'volume': 600, 'variation': 0.0},    # BOA Mali
    'ORGT': {'close': 4750, 'volume': 800, 'variation': 0.0},    # Orange CI
}

def confirmer_saisie_manuelle():
    """Demander confirmation avant insertion"""
    print()
    print("=" * 100)
    print("📊 COURS À INSÉRER (vérifier qu'ils correspondent au site BRVM.org)")
    print("=" * 100)
    print()
    print(f"{'SYMBOLE':<12} {'COURS (FCFA)':>15} {'VOLUME':>12} {'VARIATION':>12}")
    print(f"{'-'*12} {'-'*15} {'-'*12} {'-'*12}")
    
    for symbole, data in sorted(VRAIS_COURS_BRVM.items()):
        var_icon = "🟢" if data['variation'] > 0 else ("🔴" if data['variation'] < 0 else "⚪")
        print(f"{symbole:<12} {data['close']:>15,.0f} {data['volume']:>12,} {var_icon} {data['variation']:>10.2f}%")
    
    print()
    print("=" * 100)
    print("⚠️  VÉRIFICATION CRITIQUE:")
    print("   - Ces cours proviennent-ils du site officiel BRVM.org?")
    print("   - Correspondent-ils à la séance d'aujourd'hui?")
    print("   - Aucune valeur simulée ou estimée?")
    print("=" * 100)
    print()
    
    reponse = input("✅ Confirmer que ce sont les VRAIS cours (oui/NON): ").strip().lower()
    
    return reponse in ['oui', 'yes']

def inserer_cours_reels():
    """Insérer les cours réels dans MongoDB"""
    
    if not confirmer_saisie_manuelle():
        print()
        print("❌ Insertion annulée - Politique tolérance zéro respectée")
        print()
        print("💡 Pour insérer les vrais cours:")
        print("   1. Modifier VRAIS_COURS_BRVM dans ce script")
        print("   2. Mettre les cours du site https://www.brvm.org/fr/cours-actions/investisseurs")
        print("   3. Relancer: python collecter_brvm_manuel.py")
        return
    
    print()
    print("=" * 100)
    print("💾 INSERTION DANS MONGODB")
    print("=" * 100)
    
    _, db = get_mongo_db()
    date_aujourd_hui = datetime.now().strftime('%Y-%m-%d')
    
    inserted = 0
    updated = 0
    
    for symbole, data in VRAIS_COURS_BRVM.items():
        try:
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbole,
                'ts': date_aujourd_hui,
                'value': data['close'],
                'attrs': {
                    'symbol': symbole,
                    'close': data['close'],
                    'volume': data['volume'],
                    'variation': data['variation'],
                    'data_quality': 'REAL_MANUAL',  # ✅ SAISIE MANUELLE VÉRIFIÉE
                    'source_url': 'https://www.brvm.org/fr/cours-actions/investisseurs',
                    'collecte_method': 'MANUAL_ENTRY_VERIFIED',
                    'collecte_datetime': datetime.now().isoformat(),
                }
            }
            
            result = db.curated_observations.update_one(
                {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbole,
                    'ts': date_aujourd_hui
                },
                {'$set': observation},
                upsert=True
            )
            
            if result.upserted_id:
                inserted += 1
                print(f"  ✅ {symbole:10s} = {data['close']:>10,.0f} FCFA (nouveau)")
            else:
                updated += 1
                print(f"  🔄 {symbole:10s} = {data['close']:>10,.0f} FCFA (mis à jour)")
                
        except Exception as e:
            print(f"  ❌ Erreur {symbole}: {e}")
    
    print()
    print("=" * 100)
    print("📊 RÉSULTAT")
    print("=" * 100)
    print(f"✅ Insérées    : {inserted}")
    print(f"🔄 Mises à jour: {updated}")
    print(f"📅 Date        : {date_aujourd_hui}")
    print(f"🎯 Qualité     : REAL_MANUAL (Saisie manuelle vérifiée)")
    print("=" * 100)
    print()
    print("🔍 Vérifier dashboard: http://127.0.0.1:8000/brvm/")
    print()

if __name__ == '__main__':
    inserer_cours_reels()

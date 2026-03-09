"""
Nettoyage des anciennes données BRVM simulées
Conserve uniquement les cours réels (data_quality='REAL_MANUAL')
"""
import sys
import os
import django

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def nettoyer_anciennes_donnees():
    """Supprime les anciennes données BRVM simulées"""
    print("\n" + "="*80)
    print("🗑️  NETTOYAGE DES DONNÉES BRVM SIMULÉES")
    print("="*80 + "\n")
    
    _, db = get_mongo_db()
    
    # Compter avant suppression
    total_avant = db.curated_observations.count_documents({'source': 'BRVM'})
    cours_reels = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': 'REAL_MANUAL'
    })
    cours_simules = total_avant - cours_reels
    
    print(f"📊 ÉTAT ACTUEL:\n")
    print(f"   Total BRVM: {total_avant}")
    print(f"   ✅ Cours réels: {cours_reels}")
    print(f"   ⚠️  Cours simulés à supprimer: {cours_simules}")
    
    if cours_simules == 0:
        print("\n✅ Aucune donnée simulée à supprimer !")
        return
    
    # Confirmation
    print(f"\n⚠️  ATTENTION: Cette opération va supprimer {cours_simules} observations simulées")
    print(f"   Les {cours_reels} cours réels seront conservés\n")
    
    input("   Appuyez sur ENTRÉE pour continuer (ou Ctrl+C pour annuler)...")
    
    # Suppression
    print("\n🗑️  Suppression en cours...")
    result = db.curated_observations.delete_many({
        'source': 'BRVM',
        'attrs.data_quality': {'$ne': 'REAL_MANUAL'}
    })
    
    print(f"\n✅ {result.deleted_count} observations simulées supprimées")
    
    # Vérification après suppression
    total_apres = db.curated_observations.count_documents({'source': 'BRVM'})
    
    print(f"\n📊 ÉTAT APRÈS NETTOYAGE:\n")
    print(f"   Total BRVM: {total_apres}")
    print(f"   ✅ Cours réels conservés: {total_apres}")
    print(f"   🗑️  Données supprimées: {result.deleted_count}")
    
    # Afficher les cours restants
    print(f"\n📋 COURS RÉELS CONSERVÉS:\n")
    
    cours = list(db.curated_observations.find(
        {'source': 'BRVM'},
        {'key': 1, 'value': 1, 'attrs.day_change_pct': 1}
    ).sort('key', 1))
    
    if cours:
        for c in cours:
            variation = c.get('attrs', {}).get('day_change_pct', 0)
            print(f"   {c['key']:8s} | {c['value']:8.0f} FCFA | {variation:+6.2f}%")
    
    print("\n" + "="*80)
    print("✅ NETTOYAGE TERMINÉ")
    print("="*80 + "\n")
    
    print("📍 Vérifiez les cours sur: http://localhost:8000/dashboard/brvm/")
    print("📝 Pour mettre à jour quotidiennement: python mettre_a_jour_cours_brvm.py\n")

if __name__ == "__main__":
    try:
        nettoyer_anciennes_donnees()
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")

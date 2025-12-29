"""
Script pour lancer plusieurs collectes BRVM rapidement
Permet de remplir la base de données avec des observations historiques
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# Configuration Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion

def collect_multiple_times(num_collections=10, interval_seconds=5):
    """
    Lance plusieurs collectes BRVM avec un intervalle
    
    Args:
        num_collections: Nombre de collectes à effectuer
        interval_seconds: Intervalle en secondes entre chaque collecte
    """
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║              📊 COLLECTE MULTIPLE BRVM - REMPLISSAGE RAPIDE                   ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

⚙️  Configuration:
   • Nombre de collectes: {num_collections}
   • Intervalle: {interval_seconds} secondes
   • Source: BRVM (47 actions)
   • Temps total estimé: {(num_collections * interval_seconds) / 60:.1f} minutes

🚀 Démarrage...

════════════════════════════════════════════════════════════════════════════════
    """)
    
    success_count = 0
    error_count = 0
    
    for i in range(num_collections):
        try:
            print(f"\n{'─' * 80}")
            print(f"📥 Collecte {i+1}/{num_collections} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'─' * 80}")
            
            # Lancer la collecte
            run_ingestion(source="brvm")
            
            success_count += 1
            print(f"✅ Collecte {i+1} réussie")
            
            # Attendre avant la prochaine collecte (sauf pour la dernière)
            if i < num_collections - 1:
                print(f"⏳ Attente de {interval_seconds} secondes avant la prochaine collecte...")
                time.sleep(interval_seconds)
                
        except Exception as e:
            error_count += 1
            print(f"❌ Erreur lors de la collecte {i+1}: {e}")
            
            # Continuer malgré l'erreur
            if i < num_collections - 1:
                print(f"⏳ Attente de {interval_seconds} secondes avant de réessayer...")
                time.sleep(interval_seconds)
    
    # Résumé final
    print(f"""
{'═' * 80}
📊 RÉSUMÉ DE LA COLLECTE MULTIPLE
{'═' * 80}

✅ Collectes réussies : {success_count}/{num_collections}
❌ Collectes échouées : {error_count}/{num_collections}
📈 Taux de réussite   : {(success_count/num_collections)*100:.1f}%

💾 Les données ont été ajoutées à MongoDB
🎯 Vous pouvez maintenant utiliser le tableau de bord pour l'analyse

{'═' * 80}
    """)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collecte multiple BRVM')
    parser.add_argument('-n', '--number', type=int, default=20, 
                       help='Nombre de collectes à effectuer (défaut: 20)')
    parser.add_argument('-i', '--interval', type=int, default=3,
                       help='Intervalle en secondes entre collectes (défaut: 3)')
    
    args = parser.parse_args()
    
    collect_multiple_times(args.number, args.interval)

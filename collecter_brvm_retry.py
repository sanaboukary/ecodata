#!/usr/bin/env python3
"""
Collecte BRVM avec retry automatique
Réessaye toutes les heures jusqu'à réussite
"""
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import du collecteur
from collecter_brvm_complet_maintenant import CollecteurBRVMComplet

def main():
    print("\n" + "="*80)
    print("🔄 COLLECTE BRVM AVEC RETRY AUTOMATIQUE")
    print("="*80)
    print(f"Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Politique: DONNÉES RÉELLES UNIQUEMENT - Pas de simulation")
    print("Stratégie: Réessayer toutes les heures jusqu'à réussite")
    print("="*80 + "\n")
    
    max_tentatives = 10
    delai_entre_tentatives = 3600  # 1 heure en secondes
    
    for tentative in range(1, max_tentatives + 1):
        print(f"\n{'='*80}")
        print(f"TENTATIVE {tentative}/{max_tentatives}")
        print(f"Heure: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}\n")
        
        try:
            collecteur = CollecteurBRVMComplet()
            
            # Tenter le scraping
            actions_data = collecteur.scraper_brvm_avec_tous_attributs()
            
            if actions_data and len(actions_data) > 0:
                # Sauvegarder
                count = collecteur.sauvegarder_complet(actions_data)
                
                if count > 0:
                    print(f"\n{'='*80}")
                    print(f"✅ SUCCÈS ! {count} actions collectées et sauvegardées")
                    print(f"Heure de réussite: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*80}\n")
                    return 0
                else:
                    print("\n⚠️  Données collectées mais aucune sauvegardée (problème data_quality)")
            else:
                print("\n❌ Aucune donnée collectée (site inaccessible ou erreur)")
        
        except Exception as e:
            print(f"\n❌ Erreur lors de la tentative: {e}")
        
        # Si ce n'est pas la dernière tentative, attendre
        if tentative < max_tentatives:
            prochaine = datetime.fromtimestamp(time.time() + delai_entre_tentatives)
            print(f"\n⏳ Prochaine tentative dans 1 heure: {prochaine.strftime('%H:%M:%S')}")
            print(f"   (Vous pouvez arrêter avec Ctrl+C)\n")
            
            # Attendre 1 heure
            try:
                time.sleep(delai_entre_tentatives)
            except KeyboardInterrupt:
                print("\n\n⚠️  Collecte arrêtée par l'utilisateur")
                print("Pour réessayer: python collecter_brvm_retry.py\n")
                return 1
    
    print(f"\n{'='*80}")
    print(f"❌ ÉCHEC après {max_tentatives} tentatives")
    print(f"Le site BRVM est probablement indisponible aujourd'hui")
    print(f"Action requise: Saisie manuelle via mettre_a_jour_cours_brvm.py")
    print(f"{'='*80}\n")
    return 1

if __name__ == '__main__':
    sys.exit(main())

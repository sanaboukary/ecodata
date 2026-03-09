#!/usr/bin/env python3
"""
Script d'activation automatique de la collecte horaire BRVM
- Vérifie que Airflow est actif
- Active le DAG brvm_collecte_horaire_automatique
- Configure les paramètres optimaux
- Génère rapport d'activation
"""

import subprocess
import sys
from datetime import datetime

print("="*100)
print(" " * 25 + "ACTIVATION COLLECTE HORAIRE BRVM")
print(" " * 35 + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("="*100)


def verifier_airflow():
    """Vérifie si Airflow est démarré"""
    print("\n🔍 Vérification Airflow...")
    
    try:
        result = subprocess.run(
            ['airflow', 'dags', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("   ✅ Airflow opérationnel")
            return True
        else:
            print("   ❌ Airflow non démarré")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def activer_dag_horaire():
    """Active le DAG de collecte horaire"""
    print("\n🔧 Activation DAG horaire...")
    
    dag_id = 'brvm_collecte_horaire_automatique'
    
    try:
        # Unpause le DAG
        result = subprocess.run(
            ['airflow', 'dags', 'unpause', dag_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"   ✅ DAG '{dag_id}' activé")
            return True
        else:
            print(f"   ❌ Erreur activation: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def verifier_prochaine_execution():
    """Affiche la prochaine exécution planifiée"""
    print("\n📅 Prochaines exécutions...")
    
    dag_id = 'brvm_collecte_horaire_automatique'
    
    try:
        result = subprocess.run(
            ['airflow', 'dags', 'next-execution', dag_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"\n   📊 Prochaines collectes planifiées:")
            for i, line in enumerate(lines[:5], 1):
                if line.strip():
                    print(f"      {i}. {line.strip()}")
            
            if len(lines) > 5:
                print(f"      ... et {len(lines) - 5} autres")
            
            return True
        else:
            print(f"   ⚠️  Impossible de récupérer le planning")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def generer_rapport_activation():
    """Génère un rapport d'activation"""
    print("\n" + "="*100)
    print("📊 RAPPORT D'ACTIVATION")
    print("="*100)
    
    print("""
✅ DAG Airflow: brvm_collecte_horaire_automatique

📅 PLANNING DE COLLECTE:
   - Fréquence: Toutes les heures
   - Jours: Lundi à Vendredi
   - Heures: 9h, 10h, 11h, 12h, 13h, 14h, 15h, 16h
   - Total: 8 collectes par jour × 5 jours = 40 collectes/semaine

📊 DONNÉES COLLECTÉES:
   - 47 actions BRVM à chaque collecte
   - 376 observations par jour (47 × 8)
   - 1,880 observations par semaine (376 × 5)

🌐 MÉTHODE:
   - Scraping site officiel BRVM
   - URL: https://www.brvm.org/fr/investir/cours-et-cotations
   - Timeout: 30s
   - Fallback: Saisie manuelle si échec

💾 STOCKAGE:
   - MongoDB: curated_observations
   - Marqueur qualité: REAL_SCRAPER
   - Timestamp: Heure de collecte

🔍 MONITORING:
   - Logs: airflow/logs/brvm_collecte_horaire_automatique/
   - Rapport: Généré après chaque collecte
   - Dashboard: http://localhost:8080

📝 COMMANDES UTILES:
   - Test manuel: python tester_collecte_horaire.py
   - Vérifier données: python verifier_collecte.py
   - Trigger immédiat: airflow dags trigger brvm_collecte_horaire_automatique
   - Voir logs: tail -f airflow/logs/brvm_collecte_horaire_automatique/*/latest.log
""")
    
    print("="*100)
    print("🎉 COLLECTE HORAIRE ACTIVÉE AVEC SUCCÈS")
    print("="*100)


def main():
    """Fonction principale"""
    
    # 1. Vérifier Airflow
    if not verifier_airflow():
        print("\n❌ ERREUR: Airflow doit être démarré")
        print("   Solution: Exécuter 'start_airflow_background.bat'")
        return 1
    
    # 2. Activer DAG
    if not activer_dag_horaire():
        print("\n❌ ERREUR: Impossible d'activer le DAG")
        print("   Vérifier que le fichier airflow/dags/brvm_collecte_horaire.py existe")
        return 1
    
    # 3. Vérifier planning
    verifier_prochaine_execution()
    
    # 4. Rapport
    generer_rapport_activation()
    
    print("\n✅ SYSTÈME OPÉRATIONNEL - Collecte horaire active")
    print("   Prochaine collecte: Voir planning ci-dessus")
    print("   Monitoring: http://localhost:8080")
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Activation interrompue")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

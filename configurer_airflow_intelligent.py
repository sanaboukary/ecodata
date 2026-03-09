#!/usr/bin/env python3
"""
Configuration et activation intelligente de tous les DAGs Airflow
- Vérifie santé Airflow
- Active/désactive DAGs selon priorités
- Configure horaires optimaux
- Génère rapport de santé
"""

import subprocess
import sys
import os
from datetime import datetime

print("="*100)
print(" " * 30 + "CONFIGURATION AIRFLOW INTELLIGENTE")
print(" " * 38 + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("="*100)


def verifier_airflow_actif():
    """Vérifie si Airflow est actif"""
    print("\n🔍 VÉRIFICATION AIRFLOW...")
    
    try:
        # Tenter de se connecter à l'API Airflow
        result = subprocess.run(
            ['airflow', 'dags', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            dags = [line.split('|')[0].strip() for line in result.stdout.split('\n') 
                    if '|' in line and not line.startswith('dag_id')]
            
            print(f"   ✅ Airflow actif - {len(dags)} DAGs détectés")
            return True, dags
        else:
            print(f"   ❌ Airflow non actif")
            print(f"      Erreur: {result.stderr}")
            return False, []
            
    except FileNotFoundError:
        print("   ❌ Commande 'airflow' non trouvée")
        print("      Solution: Activer environnement virtuel (.venv)")
        return False, []
        
    except subprocess.TimeoutExpired:
        print("   ⚠️  Timeout Airflow (peut être en démarrage)")
        return False, []
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False, []


def lister_dags_disponibles():
    """Liste tous les DAGs dans airflow/dags/"""
    print("\n📋 DAGS DISPONIBLES...")
    
    dags_dir = os.path.join(os.getcwd(), 'airflow', 'dags')
    
    if not os.path.exists(dags_dir):
        print(f"   ❌ Dossier {dags_dir} non trouvé")
        return []
    
    dags = {}
    
    for file in os.listdir(dags_dir):
        if file.endswith('_dag.py') or file.endswith('_collecte.py'):
            filepath = os.path.join(dags_dir, file)
            
            # Lire description du DAG
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    desc = "Pas de description"
                    schedule = "Non défini"
                    
                    for line in lines[:50]:  # Lire les 50 premières lignes
                        if 'description=' in line or 'description =' in line:
                            desc = line.split("'")[1] if "'" in line else line.split('"')[1]
                        if 'schedule_interval=' in line or 'schedule_interval =' in line:
                            schedule = line.split("'")[1] if "'" in line else "Variable"
                    
                    dags[file] = {
                        'description': desc,
                        'schedule': schedule,
                        'path': filepath
                    }
                    
            except Exception as e:
                print(f"   ⚠️  Erreur lecture {file}: {e}")
    
    print(f"   ✅ {len(dags)} DAGs trouvés\n")
    
    for file, info in dags.items():
        print(f"   📄 {file}")
        print(f"      Description: {info['description'][:60]}")
        print(f"      Planification: {info['schedule']}")
        print()
    
    return dags


def configurer_priorites_dags():
    """Définit les priorités et configuration optimale"""
    print("🎯 CONFIGURATION PRIORITÉS...\n")
    
    config = {
        'brvm_collecte_quotidienne_reelle': {
            'priorite': 1,
            'actif': True,
            'description': 'Données BRVM réelles (critiques)',
            'schedule': '0 17 * * 1-5',  # Lun-Ven 17h
            'retries': 3,
            'timeout': '1h',
            'notes': 'PRIORITÉ MAX - Données trading'
        },
        'worldbank_collecte_mensuelle': {
            'priorite': 2,
            'actif': True,
            'description': 'Indicateurs World Bank',
            'schedule': '0 2 15 * *',  # 15 de chaque mois à 2h
            'retries': 2,
            'timeout': '3h',
            'notes': 'Contexte macroéconomique'
        },
        'imf_collecte_mensuelle': {
            'priorite': 2,
            'actif': True,
            'description': 'Données IMF (inflation, PIB, chômage)',
            'schedule': '0 3 1 * *',  # 1er du mois à 3h
            'retries': 2,
            'timeout': '2h',
            'notes': 'Gestion timeout 30s + fallback mock'
        },
        'afdb_un_collecte_trimestrielle': {
            'priorite': 3,
            'actif': True,
            'description': 'AfDB + UN SDG (développement)',
            'schedule': '0 4 1 1,4,7,10 *',  # Trimestriel à 4h
            'retries': 1,
            'timeout': '3h',
            'notes': 'AfDB=mock, UN_SDG=API réelle'
        },
    }
    
    for dag_id, info in config.items():
        print(f"   {'⭐' * info['priorite']} {dag_id}")
        print(f"      Priorité: {info['priorite']} | Actif: {'✅' if info['actif'] else '❌'}")
        print(f"      Planification: {info['schedule']}")
        print(f"      Timeout: {info['timeout']} | Retries: {info['retries']}")
        print(f"      Note: {info['notes']}")
        print()
    
    return config


def activer_dags(dags_config):
    """Active les DAGs selon configuration"""
    print("🔧 ACTIVATION DES DAGS...\n")
    
    success_count = 0
    error_count = 0
    
    for dag_id, config in dags_config.items():
        if not config['actif']:
            print(f"   ⏭️  Ignoré: {dag_id} (désactivé)")
            continue
        
        try:
            # Unpause le DAG
            result = subprocess.run(
                ['airflow', 'dags', 'unpause', dag_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"   ✅ Activé: {dag_id}")
                success_count += 1
            else:
                print(f"   ❌ Erreur: {dag_id}")
                print(f"      {result.stderr.strip()}")
                error_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Timeout: {dag_id}")
            error_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {dag_id} - {e}")
            error_count += 1
    
    print(f"\n   Résumé: {success_count} activés, {error_count} erreurs")
    return success_count, error_count


def generer_rapport_configuration():
    """Génère rapport final de configuration"""
    print("\n" + "="*100)
    print("📊 RAPPORT DE CONFIGURATION")
    print("="*100)
    
    # Vérifier status DAGs
    try:
        result = subprocess.run(
            ['airflow', 'dags', 'list', '--output', 'table'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("\n📋 STATUT DES DAGS:\n")
            print(result.stdout)
            
    except Exception as e:
        print(f"\n⚠️  Impossible de lister les DAGs: {e}")
    
    print("\n📅 PLANNING DE COLLECTE:")
    print("┌────────────────────────────────────┬──────────────────────────┬────────────┐")
    print("│ DAG                                │ Planification            │ Priorité   │")
    print("├────────────────────────────────────┼──────────────────────────┼────────────┤")
    print("│ brvm_collecte_quotidienne_reelle   │ Lun-Ven 17h00           │ ⭐⭐⭐        │")
    print("│ worldbank_collecte_mensuelle       │ 15 de chaque mois 2h00  │ ⭐⭐          │")
    print("│ imf_collecte_mensuelle             │ 1er de chaque mois 3h00 │ ⭐⭐          │")
    print("│ afdb_un_collecte_trimestrielle     │ Trimestriel 4h00        │ ⭐            │")
    print("└────────────────────────────────────┴──────────────────────────┴────────────┘")
    
    print("\n🔗 ACCÈS AIRFLOW:")
    print("   Interface Web: http://localhost:8080")
    print("   User/Pass: admin/admin")
    
    print("\n📝 COMMANDES UTILES:")
    print("   Vérifier status: check_airflow_status.bat")
    print("   Logs: airflow/logs/")
    print("   Trigger manuel: airflow dags trigger <dag_id>")
    
    print("\n" + "="*100)


def main():
    """Fonction principale"""
    
    # 1. Vérification Airflow
    airflow_ok, dags_actifs = verifier_airflow_actif()
    
    if not airflow_ok:
        print("\n❌ ARRÊT: Airflow doit être démarré")
        print("   Solution: Exécuter 'start_airflow_background.bat'")
        return 1
    
    # 2. Lister DAGs disponibles
    dags_disponibles = lister_dags_disponibles()
    
    # 3. Configurer priorités
    config = configurer_priorites_dags()
    
    # 4. Activer DAGs
    success, errors = activer_dags(config)
    
    # 5. Rapport final
    generer_rapport_configuration()
    
    if errors > 0:
        print(f"\n⚠️  Configuration terminée avec {errors} erreurs")
        return 1
    else:
        print("\n✅ Configuration réussie - Tous les DAGs sont actifs")
        return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration interrompue")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

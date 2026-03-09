#!/usr/bin/env python3
"""
🔄 BASCULER VERS COLLECTE HORAIRE RÉELLE
Désactive DAG avec données simulées, active DAG avec données réelles
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

def basculer_vers_collecte_reelle():
    """Active le DAG de collecte réelle, désactive celui avec données simulées"""
    
    print("\n" + "="*80)
    print("BASCULEMENT VERS COLLECTE HORAIRE REELLE")
    print("="*80 + "\n")
    
    try:
        from airflow.models import DagModel
        from airflow import settings
        
        session = settings.Session()
        
        # 1. Désactiver ancien DAG (données simulées)
        print("1. Desactivation DAG avec donnees simulees...")
        
        old_dag = session.query(DagModel).filter(
            DagModel.dag_id == 'brvm_data_collection_hourly'
        ).first()
        
        if old_dag:
            old_dag.is_paused = True
            session.commit()
            print(f"   ✓ DAG 'brvm_data_collection_hourly' -> PAUSE")
        else:
            print(f"   ~ DAG 'brvm_data_collection_hourly' non trouve")
        
        print()
        
        # 2. Activer nouveau DAG (données réelles)
        print("2. Activation NOUVEAU DAG avec donnees REELLES...")
        
        new_dag = session.query(DagModel).filter(
            DagModel.dag_id == 'brvm_collecte_horaire_REELLE'
        ).first()
        
        if new_dag:
            new_dag.is_paused = False
            session.commit()
            print(f"   ✓ DAG 'brvm_collecte_horaire_REELLE' -> ACTIF")
        else:
            print(f"   ~ DAG 'brvm_collecte_horaire_REELLE' non trouve")
            print(f"   ~ Sera actif au prochain scan Airflow")
        
        print()
        
        # 3. Lister DAGs BRVM
        print("3. Etat des DAGs BRVM:")
        
        brvm_dags = session.query(DagModel).filter(
            DagModel.dag_id.like('%brvm%')
        ).all()
        
        if brvm_dags:
            print(f"\n   {'DAG_ID':<40} {'ÉTAT':<10}")
            print(f"   {'-'*40} {'-'*10}")
            
            for dag in brvm_dags:
                etat = "PAUSE" if dag.is_paused else "ACTIF"
                print(f"   {dag.dag_id:<40} {etat:<10}")
        else:
            print("   Aucun DAG BRVM trouve")
        
        session.close()
        
        print()
        print("="*80)
        print("BASCULEMENT TERMINE")
        print("="*80)
        print()
        print("ANCIEN DAG (donnees simulees):")
        print("  brvm_data_collection_hourly -> PAUSE")
        print()
        print("NOUVEAU DAG (donnees reelles):")
        print("  brvm_collecte_horaire_REELLE -> ACTIF")
        print("  Schedule: Toutes les heures 9h-16h, lun-ven")
        print("  Politique: Scraping reel ou rien (ZERO generation)")
        print()
        print("Interface Airflow: http://localhost:8080")
        print()
        
        return True
        
    except ImportError as e:
        print(f"✗ Airflow non disponible: {e}")
        print()
        print("ALTERNATIVE - Activation manuelle:")
        print("  1. Ouvrir: http://localhost:8080")
        print("  2. Mettre en PAUSE: brvm_data_collection_hourly")
        print("  3. ACTIVER: brvm_collecte_horaire_REELLE")
        print()
        return False
    
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    basculer_vers_collecte_reelle()

"""
DAG Airflow pour génération automatique de rapports PDF/Excel
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

# Ajouter le chemin Django au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../..'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from dashboard.export_service import export_service

default_args = {
    'owner': 'plateforme_cedeao',
    'depends_on_past': False,
    'email': ['admin@cedeao-data.org'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def generate_brvm_monthly_report(**context):
    """Générer rapport mensuel BRVM"""
    print("📄 Génération rapport mensuel BRVM...")
    
    try:
        pdf_buffer = export_service.generate_dashboard_pdf('BRVM', period='30d')
        
        # Sauvegarder dans répertoire rapports
        reports_dir = '/app/reports'  # Adapter selon environnement
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"BRVM_monthly_{datetime.now().strftime('%Y%m')}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Rapport sauvegardé: {filepath}")
        print(f"📊 Taille: {len(pdf_buffer.getvalue()):,} bytes")
        
        return filepath
    except Exception as e:
        print(f"❌ Erreur génération BRVM: {e}")
        raise

def generate_worldbank_quarterly_report(**context):
    """Générer rapport trimestriel Banque Mondiale"""
    print("📊 Génération rapport trimestriel Banque Mondiale...")
    
    try:
        excel_buffer = export_service.generate_dashboard_excel('WorldBank', period='90d')
        
        reports_dir = '/app/reports'
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"WorldBank_quarterly_{datetime.now().strftime('%Y_Q%m')}.xlsx"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(excel_buffer.getvalue())
        
        print(f"✅ Rapport sauvegardé: {filepath}")
        print(f"📊 Taille: {len(excel_buffer.getvalue()):,} bytes")
        
        return filepath
    except Exception as e:
        print(f"❌ Erreur génération WorldBank: {e}")
        raise

def generate_imf_monthly_report(**context):
    """Générer rapport mensuel FMI"""
    print("📄 Génération rapport mensuel FMI...")
    
    try:
        pdf_buffer = export_service.generate_dashboard_pdf('IMF', period='30d')
        
        reports_dir = '/app/reports'
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"IMF_monthly_{datetime.now().strftime('%Y%m')}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Rapport sauvegardé: {filepath}")
        
        return filepath
    except Exception as e:
        print(f"❌ Erreur génération IMF: {e}")
        raise

def generate_cedeao_comprehensive_report(**context):
    """Générer rapport comparatif complet CEDEAO"""
    print("🌍 Génération rapport comparatif CEDEAO...")
    
    try:
        # Tous les pays CEDEAO
        countries = ['BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB', 
                    'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO']
        
        # Indicateurs clés
        indicators = [
            'SP.POP.TOTL',           # Population
            'NY.GDP.MKTP.CD',        # PIB
            'NY.GDP.PCAP.CD',        # PIB par habitant
            'FP.CPI.TOTL.ZG',        # Inflation
        ]
        
        pdf_buffer = export_service.generate_comparison_report(
            countries, indicators, format='pdf', period='1y'
        )
        
        reports_dir = '/app/reports'
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"CEDEAO_comprehensive_{datetime.now().strftime('%Y%m')}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Rapport CEDEAO sauvegardé: {filepath}")
        print(f"📊 {len(countries)} pays, {len(indicators)} indicateurs")
        
        return filepath
    except Exception as e:
        print(f"❌ Erreur génération CEDEAO: {e}")
        raise

def send_email_notification(**context):
    """Envoyer notification email avec liens rapports"""
    # TODO: Implémenter envoi email avec Django
    print("📧 Notification email envoyée (fonctionnalité à implémenter)")
    
    task_instance = context['task_instance']
    
    # Récupérer chemins rapports générés
    brvm_path = task_instance.xcom_pull(task_ids='generate_brvm_report')
    wb_path = task_instance.xcom_pull(task_ids='generate_worldbank_report')
    imf_path = task_instance.xcom_pull(task_ids='generate_imf_report')
    cedeao_path = task_instance.xcom_pull(task_ids='generate_cedeao_report')
    
    print("\n📋 Rapports générés:")
    print(f"  - BRVM: {brvm_path}")
    print(f"  - WorldBank: {wb_path}")
    print(f"  - IMF: {imf_path}")
    print(f"  - CEDEAO: {cedeao_path}")

# Définition du DAG
dag = DAG(
    'automated_reports',
    default_args=default_args,
    description='Génération automatique de rapports PDF/Excel',
    schedule_interval='0 6 1 * *',  # 1er du mois à 6h00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['reports', 'exports', 'cedeao'],
    is_paused_upon_creation=False,  # Actif dès création
)

# Tâches du DAG
brvm_report = PythonOperator(
    task_id='generate_brvm_report',
    python_callable=generate_brvm_monthly_report,
    dag=dag,
)

worldbank_report = PythonOperator(
    task_id='generate_worldbank_report',
    python_callable=generate_worldbank_quarterly_report,
    dag=dag,
)

imf_report = PythonOperator(
    task_id='generate_imf_report',
    python_callable=generate_imf_monthly_report,
    dag=dag,
)

cedeao_report = PythonOperator(
    task_id='generate_cedeao_report',
    python_callable=generate_cedeao_comprehensive_report,
    dag=dag,
)

notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_email_notification,
    dag=dag,
)

# Dépendances: Générer tous rapports en parallèle, puis notifier
[brvm_report, worldbank_report, imf_report, cedeao_report] >> notification

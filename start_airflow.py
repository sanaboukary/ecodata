"""
Démarrage d'Airflow en arrière-plan pour collecte automatique
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.absolute()
AIRFLOW_HOME = PROJECT_ROOT / "airflow"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Variables d'environnement
env = os.environ.copy()
env['AIRFLOW_HOME'] = str(AIRFLOW_HOME)
env['PYTHONPATH'] = str(PROJECT_ROOT)

print("=" * 80)
print("  DÉMARRAGE AIRFLOW EN ARRIÈRE-PLAN")
print("=" * 80)

# Vérifier si Airflow est déjà initialisé
db_file = AIRFLOW_HOME / "airflow.db"
if not db_file.exists():
    print("\n⚙️  Initialisation d'Airflow (première fois)...")
    
    # Créer les dossiers
    (AIRFLOW_HOME / "logs").mkdir(parents=True, exist_ok=True)
    
    # Initialiser la DB
    subprocess.run(
        [str(VENV_PYTHON), "-m", "airflow", "db", "init"],
        env=env,
        check=True
    )
    print("✓ Base de données initialisée")
    
    # Créer l'utilisateur admin
    try:
        subprocess.run(
            [
                str(VENV_PYTHON), "-m", "airflow", "users", "create",
                "--username", "admin",
                "--firstname", "Admin",
                "--lastname", "User",
                "--role", "Admin",
                "--email", "admin@plateforme.local",
                "--password", "admin"
            ],
            env=env,
            check=True
        )
        print("✓ Utilisateur admin créé")
    except:
        print("⚠️  Utilisateur admin existe déjà")

# Démarrer le scheduler
print("\n[1/2] Démarrage du Scheduler Airflow...")
scheduler_log = AIRFLOW_HOME / "logs" / "scheduler.log"
scheduler_process = subprocess.Popen(
    [str(VENV_PYTHON), "-m", "airflow", "scheduler"],
    env=env,
    stdout=open(scheduler_log, "w"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
)
print(f"✓ Scheduler démarré (PID: {scheduler_process.pid})")
print(f"  Logs: {scheduler_log}")

# Attendre un peu
time.sleep(3)

# Démarrer le webserver
print("\n[2/2] Démarrage du Webserver Airflow...")
webserver_log = AIRFLOW_HOME / "logs" / "webserver.log"
webserver_process = subprocess.Popen(
    [str(VENV_PYTHON), "-m", "airflow", "webserver", "-p", "8080"],
    env=env,
    stdout=open(webserver_log, "w"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
)
print(f"✓ Webserver démarré (PID: {webserver_process.pid})")
print(f"  Logs: {webserver_log}")

print("\n" + "=" * 80)
print("  ✅ AIRFLOW DÉMARRÉ EN ARRIÈRE-PLAN")
print("=" * 80)

print(f"""
🌐 Interface Web: http://localhost:8080
   Login: admin / admin

📊 DAGs de collecte automatique:
   • BRVM          : Toutes les heures (9h-16h, lun-ven)
   • World Bank    : Le 15 du mois
   • IMF           : Le 1er du mois
   • AfDB + UN SDG : Trimestriel

📝 Logs: {AIRFLOW_HOME / "logs"}

🛑 Pour arrêter:
   python stop_airflow.py
   OU: Gestionnaire des tâches → Terminer python.exe

⏳ Attendez 30 secondes que l'interface soit prête...
""")

# Sauvegarder les PIDs
pids_file = PROJECT_ROOT / "airflow_pids.txt"
with open(pids_file, "w") as f:
    f.write(f"scheduler:{scheduler_process.pid}\n")
    f.write(f"webserver:{webserver_process.pid}\n")

print(f"PIDs sauvegardés dans: {pids_file}")
print("\n✓ Airflow tourne maintenant en arrière-plan!")

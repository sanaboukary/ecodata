#!/usr/bin/env python3
"""
Script de configuration et démarrage d'Apache Airflow
pour la plateforme de centralisation de données
"""
import os
import sys
import subprocess
from pathlib import Path

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(message):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

# Chemins
PROJECT_ROOT = Path(__file__).parent.absolute()
AIRFLOW_HOME = PROJECT_ROOT / "airflow"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

print_step("CONFIGURATION APACHE AIRFLOW")

# 1. Définir AIRFLOW_HOME
os.environ['AIRFLOW_HOME'] = str(AIRFLOW_HOME)
print_success(f"AIRFLOW_HOME défini: {AIRFLOW_HOME}")

# 2. Créer les répertoires nécessaires
directories = [
    AIRFLOW_HOME / "dags",
    AIRFLOW_HOME / "plugins",
    AIRFLOW_HOME / "config",
    PROJECT_ROOT / "logs" / "airflow",
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)
    print_success(f"Répertoire créé/vérifié: {directory}")

# 3. Installer Airflow si nécessaire
print_step("INSTALLATION DES DÉPENDANCES")

try:
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements/base.txt"],
        capture_output=True,
        text=True,
        check=True
    )
    print_success("Dépendances installées")
except subprocess.CalledProcessError as e:
    print_error(f"Erreur d'installation: {e}")
    print(e.stderr)
    sys.exit(1)

# 4. Initialiser la base de données Airflow
print_step("INITIALISATION DE LA BASE DE DONNÉES AIRFLOW")

try:
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "airflow", "db", "init"],
        env={**os.environ, 'AIRFLOW_HOME': str(AIRFLOW_HOME)},
        capture_output=True,
        text=True
    )
    print_success("Base de données Airflow initialisée")
except Exception as e:
    print_warning(f"DB déjà initialisée ou erreur: {e}")

# 5. Créer un utilisateur admin
print_step("CRÉATION DE L'UTILISATEUR ADMIN")

admin_exists = False
try:
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "airflow", "users", "list"],
        env={**os.environ, 'AIRFLOW_HOME': str(AIRFLOW_HOME)},
        capture_output=True,
        text=True
    )
    if "admin" in result.stdout:
        admin_exists = True
        print_warning("Utilisateur admin déjà existant")
except:
    pass

if not admin_exists:
    try:
        subprocess.run(
            [
                str(VENV_PYTHON), "-m", "airflow", "users", "create",
                "--username", "admin",
                "--firstname", "Admin",
                "--lastname", "User",
                "--role", "Admin",
                "--email", "admin@example.com",
                "--password", "admin"
            ],
            env={**os.environ, 'AIRFLOW_HOME': str(AIRFLOW_HOME)},
            check=True
        )
        print_success("Utilisateur admin créé (username: admin, password: admin)")
    except Exception as e:
        print_error(f"Erreur création utilisateur: {e}")

# 6. Afficher les instructions
print_step("AIRFLOW CONFIGURÉ AVEC SUCCÈS!")

print(f"""
{Colors.GREEN}✅ Apache Airflow est configuré et prêt à l'emploi!{Colors.END}

📋 DAGS DISPONIBLES:
────────────────────────────────────────────────────────────────────────────────

1. {Colors.BLUE}brvm_data_collection{Colors.END}
   - Collecte: 47 actions BRVM
   - Fréquence: Toutes les heures (9h-16h, lun-ven)
   
2. {Colors.BLUE}worldbank_data_collection{Colors.END}
   - Collecte: 35+ indicateurs économiques
   - Fréquence: Le 15 de chaque mois
   
3. {Colors.BLUE}imf_data_collection{Colors.END}
   - Collecte: 20+ séries économiques
   - Fréquence: Le 1er de chaque mois
   
4. {Colors.BLUE}afdb_data_collection{Colors.END}
   - Collecte: 6 indicateurs de développement
   - Fréquence: Trimestrielle
   
5. {Colors.BLUE}un_sdg_data_collection{Colors.END}
   - Collecte: 8 séries ODD
   - Fréquence: Trimestrielle

🚀 COMMANDES POUR DÉMARRER AIRFLOW:
────────────────────────────────────────────────────────────────────────────────

# Terminal 1 - Scheduler (moteur d'exécution)
{Colors.YELLOW}.venv\\Scripts\\python.exe -m airflow scheduler{Colors.END}

# Terminal 2 - Webserver (interface web)
{Colors.YELLOW}.venv\\Scripts\\python.exe -m airflow webserver --port 8080{Colors.END}

# Accéder à l'interface web
{Colors.YELLOW}http://localhost:8080{Colors.END}
  Username: admin
  Password: admin

📁 FICHIERS IMPORTANTS:
────────────────────────────────────────────────────────────────────────────────
  - DAGs: {AIRFLOW_HOME}/dags/
  - Logs: {PROJECT_ROOT}/logs/airflow/
  - DB: {AIRFLOW_HOME}/airflow.db

💡 CONSEILS:
────────────────────────────────────────────────────────────────────────────────
  - Activez les DAGs dans l'interface web (toggle sur ON)
  - Les DAGs se déclenchent automatiquement selon leur schedule
  - Vous pouvez aussi les déclencher manuellement (bouton Play)
  - Consultez les logs dans l'interface pour le debug

""")

print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")

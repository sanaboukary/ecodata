"""
Script pour arrêter Airflow
"""
import os
import sys
import signal
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
pids_file = PROJECT_ROOT / "airflow_pids.txt"

print("=" * 80)
print("  ARRÊT D'AIRFLOW")
print("=" * 80)

if not pids_file.exists():
    print("\n⚠️  Fichier PID introuvable. Airflow n'est peut-être pas démarré.")
    print("   Vérifiez dans le Gestionnaire des tâches: python.exe")
    sys.exit(1)

# Lire les PIDs
pids = {}
with open(pids_file, "r") as f:
    for line in f:
        if ":" in line:
            name, pid = line.strip().split(":")
            pids[name] = int(pid)

# Arrêter les processus
for name, pid in pids.items():
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"✓ {name.capitalize()} arrêté (PID: {pid})")
    except ProcessLookupError:
        print(f"⚠️  {name.capitalize()} (PID: {pid}) déjà arrêté")
    except Exception as e:
        print(f"✗ Erreur arrêt {name}: {e}")

# Supprimer le fichier de PIDs
pids_file.unlink()
print(f"\n✓ Fichier PID supprimé")

print("\n" + "=" * 80)
print("  ✅ AIRFLOW ARRÊTÉ")
print("=" * 80)

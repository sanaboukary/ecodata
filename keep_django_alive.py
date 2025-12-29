#!/usr/bin/env python3
"""
Serveur Django persistant avec redémarrage automatique
Lance le serveur Django et le redémarre automatiquement en cas d'arrêt
"""

import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = BASE_DIR / ".venv" / "Scripts" / "python.exe"
MANAGE_PY = BASE_DIR / "manage.py"

def clear_screen():
    """Efface l'écran du terminal"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Affiche la bannière de démarrage"""
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                  SERVEUR DJANGO - ACTIF EN PERMANENCE                         ║
║                 Plateforme de Centralisation de Données                        ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

🌐 Serveur accessible sur: http://127.0.0.1:8000

⚙️  Configuration:
   • Redémarrage automatique activé
   • Port: 8000
   • Mode: Production-ready
   
📊 Données disponibles:
   • BRVM: 1,146+ observations (50 actions)
   • WorldBank: 4,364+ observations
   • IMF: 60+ observations
   • UN SDG: 58+ observations
   • AfDB: 40+ observations
   
🛑 Pour arrêter: Appuyez sur Ctrl+C puis fermez la fenêtre

════════════════════════════════════════════════════════════════════════════════
""")

def start_server():
    """Démarre le serveur Django"""
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 🚀 Démarrage du serveur Django...")
        print("─" * 80)
        
        # Lancer le serveur
        process = subprocess.Popen(
            [str(PYTHON_EXE), str(MANAGE_PY), "runserver", "127.0.0.1:8000"],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Afficher les logs en temps réel
        for line in process.stdout:
            print(line, end='')
        
        # Attendre que le processus se termine
        process.wait()
        
        return process.returncode
        
    except KeyboardInterrupt:
        print(f"\n\n[{time.strftime('%H:%M:%S')}] ⏸️  Interruption par l'utilisateur...")
        if process:
            process.terminate()
            process.wait()
        return -1
    except Exception as e:
        print(f"\n[{time.strftime('%H:%M:%S')}] ❌ Erreur: {e}")
        return 1

def main():
    """Boucle principale avec redémarrage automatique"""
    restart_count = 0
    
    while True:
        clear_screen()
        print_banner()
        
        if restart_count > 0:
            print(f"♻️  Redémarrage #{restart_count}")
            print("─" * 80)
        
        return_code = start_server()
        
        # Si interruption par l'utilisateur (Ctrl+C), arrêter
        if return_code == -1:
            print(f"\n[{time.strftime('%H:%M:%S')}] 🛑 Arrêt du serveur...")
            break
        
        # Sinon, redémarrer après 3 secondes
        restart_count += 1
        print("\n" + "=" * 80)
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Le serveur s'est arrêté (code: {return_code})")
        print(f"[{time.strftime('%H:%M:%S')}] ♻️  Redémarrage automatique dans 3 secondes...")
        print("=" * 80)
        
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            print(f"\n[{time.strftime('%H:%M:%S')}] 🛑 Arrêt définitif du serveur...")
            break
    
    print(f"\n[{time.strftime('%H:%M:%S')}] ✅ Serveur arrêté proprement\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)

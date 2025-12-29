#!/usr/bin/env python
"""
Script pour démarrer le serveur Django proprement
"""
import os
import sys
import subprocess

# Aller dans le bon répertoire
os.chdir(r"E:\DISQUE C\Desktop\Implementation plateforme")

# S'assurer d'utiliser le bon settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'

print("=" * 80)
print("DÉMARRAGE DU SERVEUR DJANGO")
print("=" * 80)
print(f"Répertoire: {os.getcwd()}")
print(f"Settings: {os.environ['DJANGO_SETTINGS_MODULE']}")
print("=" * 80)
print()

# Démarrer le serveur
subprocess.run([sys.executable, "manage.py", "runserver"])

#!/usr/bin/env python3
"""
Guide pour garder le serveur Django actif en permanence
"""

print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║           GUIDE - GARDER LE SERVEUR DJANGO ACTIF EN PERMANENCE                ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

🎯 OBJECTIF
═══════════════════════════════════════════════════════════════════════════════

  Garder le serveur Django accessible 24/7 sur http://127.0.0.1:8000
  avec redémarrage automatique en cas d'arrêt inattendu.

🚀 SOLUTIONS DISPONIBLES (3 MÉTHODES)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  MÉTHODE 1: Script Batch Amélioré (RECOMMANDÉ pour Windows)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fichier: start_django.bat                                                  │
│                                                                              │
│  ✅ Avantages:                                                              │
│     • Redémarrage automatique en cas d'arrêt                               │
│     • Aucune installation supplémentaire requise                           │
│     • Interface visuelle claire                                            │
│     • Simple: double-clic pour démarrer                                    │
│                                                                              │
│  📋 Comment utiliser:                                                       │
│     1. Double-cliquez sur: start_django.bat                                │
│     2. Une fenêtre s'ouvre avec le serveur actif                          │
│     3. Minimisez la fenêtre (NE LA FERMEZ PAS !)                          │
│     4. Le serveur restera actif en permanence                             │
│                                                                              │
│  🛑 Pour arrêter:                                                           │
│     • Fermez la fenêtre du terminal                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  MÉTHODE 2: Script Python Persistant                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fichier: keep_django_alive.py                                             │
│                                                                              │
│  ✅ Avantages:                                                              │
│     • Logs détaillés et colorés                                            │
│     • Statistiques de redémarrage                                          │
│     • Meilleure gestion des erreurs                                        │
│     • Peut tourner en arrière-plan                                         │
│                                                                              │
│  📋 Comment utiliser:                                                       │
│     .venv\\Scripts\\python.exe keep_django_alive.py                         │
│                                                                              │
│  🛑 Pour arrêter:                                                           │
│     • Appuyez sur Ctrl+C dans le terminal                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  MÉTHODE 3: Tâche Planifiée Windows (Pour démarrage automatique au boot)  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Pour que le serveur démarre automatiquement quand vous allumez le PC:    │
│                                                                              │
│  📋 Étapes:                                                                 │
│                                                                              │
│  1. Ouvrir le Planificateur de tâches Windows:                            │
│     • Appuyez sur Win + R                                                  │
│     • Tapez: taskschd.msc                                                  │
│     • Appuyez sur Entrée                                                   │
│                                                                              │
│  2. Créer une nouvelle tâche:                                              │
│     • Cliquez sur "Créer une tâche de base..."                            │
│     • Nom: "Serveur Django Plateforme"                                     │
│     • Description: "Serveur web de la plateforme de centralisation"        │
│                                                                              │
│  3. Déclencheur:                                                            │
│     • Choisir: "Au démarrage de l'ordinateur"                             │
│                                                                              │
│  4. Action:                                                                 │
│     • Choisir: "Démarrer un programme"                                     │
│     • Programme: E:\\DISQUE C\\Desktop\\Implementation plateforme\\start_django.bat
│                                                                              │
│  5. Paramètres avancés:                                                     │
│     • ☑ Exécuter même si l'utilisateur n'est pas connecté                 │
│     • ☑ Exécuter avec les autorisations maximales                         │
│     • ☑ Si la tâche échoue, redémarrer toutes les 5 minutes              │
│                                                                              │
│  ✅ Résultat:                                                               │
│     Le serveur démarrera automatiquement au démarrage de Windows          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

💡 RECOMMANDATION
═══════════════════════════════════════════════════════════════════════════════

  Pour une utilisation quotidienne:
  
  ➡️  Utilisez start_django.bat (Méthode 1)
  
      • Double-cliquez sur le fichier
      • Minimisez la fenêtre dans la barre des tâches
      • Le serveur restera actif toute la journée
      • Fermez la fenêtre quand vous avez terminé

  Pour un serveur en production 24/7:
  
  ➡️  Configurez la Tâche Planifiée Windows (Méthode 3)
  
      • Le serveur démarrera automatiquement avec Windows
      • Redémarrage automatique en cas de problème
      • Aucune intervention manuelle requise

🔍 VÉRIFIER QUE LE SERVEUR EST ACTIF
═══════════════════════════════════════════════════════════════════════════════

  Méthode 1: Ouvrir votre navigateur
  ─────────────────────────────────────
  http://127.0.0.1:8000
  
  Si la page se charge ➡️ Le serveur est actif ✅
  Si erreur de connexion ➡️ Le serveur est arrêté ❌

  Méthode 2: Vérifier le terminal
  ─────────────────────────────────────
  Si vous voyez ce message:
  "Starting development server at http://127.0.0.1:8000/"
  ➡️ Le serveur est actif ✅

⚠️  IMPORTANT - RÈGLES À RESPECTER
═══════════════════════════════════════════════════════════════════════════════

  ❌ NE PAS:
     • Fermer le terminal où tourne le serveur
     • Exécuter d'autres commandes dans ce terminal
     • Arrêter le processus python.exe du serveur
  
  ✅ À FAIRE:
     • Garder le terminal du serveur ouvert (mais minimisé)
     • Utiliser un autre terminal pour d'autres commandes
     • Vérifier régulièrement que le serveur répond

📊 MONITORING DU SERVEUR
═══════════════════════════════════════════════════════════════════════════════

  Pour surveiller l'état du serveur:
  
  • Logs en direct: Regardez le terminal du serveur
  • Monitoring web: http://127.0.0.1:8000/administration/ingestion/
  • Test rapide: curl http://127.0.0.1:8000 (dans un autre terminal)

🔧 DÉPANNAGE
═══════════════════════════════════════════════════════════════════════════════

  Problème: "ERR_CONNECTION_REFUSED"
  ─────────────────────────────────────
  Solution: Le serveur n'est pas démarré
  ➡️ Double-cliquez sur start_django.bat

  Problème: "Port 8000 already in use"
  ─────────────────────────────────────
  Solution: Un autre processus utilise le port
  ➡️ Tuez le processus: 
     netstat -ano | findstr :8000
     taskkill /PID <numéro_du_processus> /F

  Problème: Le serveur s'arrête tout seul
  ─────────────────────────────────────
  Solution: Utilisez le script avec redémarrage auto
  ➡️ start_django.bat redémarre automatiquement

═══════════════════════════════════════════════════════════════════════════════

✅ DÉMARRAGE IMMÉDIAT
═══════════════════════════════════════════════════════════════════════════════

  Pour démarrer le serveur MAINTENANT:
  
  1. Double-cliquez sur: start_django.bat
  2. Ouvrez votre navigateur: http://127.0.0.1:8000
  3. Profitez de votre plateforme !

═══════════════════════════════════════════════════════════════════════════════

🎉 Votre serveur restera actif tant que le terminal est ouvert !

""")

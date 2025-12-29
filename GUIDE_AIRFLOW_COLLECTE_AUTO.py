"""
GUIDE RAPIDE - AIRFLOW POUR COLLECTE AUTOMATIQUE
=================================================

✅ AIRFLOW EST MAINTENANT ACTIF!

🌐 Interface Web
----------------
URL: http://localhost:8080
Login: admin
Password: admin

📊 DAGs de Collecte Automatique
--------------------------------

1. brvm_dag
   • Fréquence: Toutes les heures (9h-16h, lundi-vendredi)
   • Données: 47 actions BRVM
   • Observations/jour: ~350

2. worldbank_dag
   • Fréquence: Le 15 de chaque mois à 2h00
   • Données: 35 indicateurs × 15 pays
   • Observations/mois: ~5,250

3. imf_dag
   • Fréquence: Le 1er de chaque mois à 2h30
   • Données: 20+ séries × 7 pays
   • Observations/mois: ~1,200

4. afdb_un_dag
   • Fréquence: Trimestrielle (janvier, avril, juillet, octobre)
   • Données: 6 indicateurs AfDB + 8 séries UN
   • Observations/trimestre: ~336

📅 Prochaines Exécutions
------------------------
- BRVM: Prochaine heure (9h-16h si jour ouvrable)
- World Bank: 15 décembre 2025
- IMF: 1er décembre 2025
- AfDB/UN: Janvier 2026

🎮 Actions dans l'Interface Web
--------------------------------

1. ACTIVER UN DAG
   • Cliquer sur le toggle (OFF → ON) à gauche du nom
   • Le DAG se déclenchera automatiquement selon son schedule

2. DÉCLENCHER MANUELLEMENT
   • Cliquer sur le bouton ▶ (Play) à droite
   • Utile pour forcer une collecte immédiate

3. VOIR LES LOGS
   • Cliquer sur le nom du DAG
   • Graph View → Cliquer sur une tâche → Logs

4. HISTORIQUE D'EXÉCUTION
   • Colonne "Runs" montre les exécutions récentes
   • Vert = Succès, Rouge = Échec

📝 Vérifier que ça Fonctionne
------------------------------

# Méthode 1: Interface Web
http://localhost:8080 → Voir les runs en vert

# Méthode 2: Vérifier MongoDB
python verifier_dernieres_donnees.py

# Méthode 3: Logs Airflow
cat airflow/logs/scheduler.log

🛑 Arrêter Airflow
------------------
python stop_airflow.py

🚀 Redémarrer Airflow
---------------------
python start_airflow.py

⚙️ Fichiers de Configuration
-----------------------------
- DAGs: airflow/dags/*.py
- Logs: airflow/logs/
- Base de données: airflow/airflow.db
- PIDs des processus: airflow_pids.txt

💡 Conseils
-----------

1. Gardez l'interface web ouverte pour monitorer
2. Les DAGs s'exécutent SEULEMENT si ils sont activés (toggle ON)
3. Les logs sont votre meilleur ami pour déboguer
4. Un DAG peut être en pause (gris) = pas d'exécution automatique

🔧 Résolution de Problèmes
---------------------------

Problème: DAG ne s'exécute pas
Solution: 
  1. Vérifier que le toggle est ON
  2. Vérifier l'heure/date du schedule
  3. Consulter les logs du scheduler

Problème: Erreur dans un DAG
Solution:
  1. Cliquer sur le DAG → Task Instance → Logs
  2. Lire le message d'erreur
  3. Corriger le code dans airflow/dags/
  4. Le scheduler recharge automatiquement

Problème: Interface ne charge pas
Solution:
  1. Attendre 1 minute (démarrage lent)
  2. Vérifier les logs: airflow/logs/webserver.log
  3. Redémarrer: python stop_airflow.py && python start_airflow.py

📊 Surveillance des Données
----------------------------

Dashboard Django: http://127.0.0.1:8000/dashboards/brvm/
  → Vérifier que les dates sont à jour

Script de vérification:
  python verifier_dernieres_donnees.py
  → Affiche la dernière date de chaque source

🎯 Objectif Atteint
-------------------

✅ Collecte BRVM: Automatique toutes les heures en semaine
✅ Collecte World Bank: Automatique mensuellement
✅ Collecte IMF: Automatique mensuellement  
✅ Collecte AfDB/UN: Automatique trimestriellement

Votre plateforme collecte maintenant ~14,000+ observations/mois automatiquement!

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(__doc__)

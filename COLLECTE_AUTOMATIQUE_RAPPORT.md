# 🤖 COLLECTE AUTOMATIQUE BRVM - ÉTAT ET CONFIGURATION

## ✅ CE QUI EST CONFIGURÉ

### 1. DAG Airflow de Collecte Horaire
**Fichier**: `airflow/dags/brvm_collecte_horaire_REELLE.py`

**Configuration**:
- ⏰ **Fréquence**: Toutes les heures de 9h à 16h (heures de bourse)
- 📅 **Jours**: Lundi à Vendredi (jours ouvrables)  
- 🔴 **Politique**: DONNÉES RÉELLES UNIQUEMENT (zéro tolérance)
- ✅ **État**: Activé par défaut (`is_paused_upon_creation=False`)

**Méthodes de collecte** (dans l'ordre de priorité):
1. **Scraping automatique** du site BRVM officiel
2. **Vérification** des données manuelles déjà saisies
3. **Aucune génération** de données si échec (ne simule JAMAIS)

### 2. Script de Démarrage Airflow
**Fichier**: `start_airflow_background.bat`

**Ce qu'il fait**:
- Lance le **scheduler** Airflow en arrière-plan
- Lance le **webserver** Airflow sur http://localhost:8080
- Crée des processus Windows minimisés
- Logs dans `airflow/logs/`

## ⚠️ PROBLÈME ACTUEL

**Airflow N'EST PAS EN COURS D'EXÉCUTION**

Cela signifie que la collecte automatique ne fonctionne pas actuellement.

## 🚀 COMMENT ACTIVER LA COLLECTE AUTOMATIQUE

### Méthode 1 : Démarrage Simple (Recommandé)

1. **Double-cliquez** sur le fichier : `start_airflow_background.bat`
2. Attendez 30 secondes que les services démarrent
3. Ouvrez votre navigateur : http://localhost:8080
4. Login : `admin` / `admin`
5. Vérifiez que le DAG `brvm_collecte_horaire_REELLE` est activé (toggle vert)

### Méthode 2 : Ligne de Commande

```bash
# Ouvrir PowerShell ou CMD dans le répertoire du projet
cd "E:\DISQUE C\Desktop\Implementation plateforme"
.venv\Scripts\activate
set AIRFLOW_HOME=%CD%\airflow

# Démarrer Airflow
airflow standalone
```

### Méthode 3 : Services Windows Séparés

```bash
# Terminal 1 - Scheduler
.venv\Scripts\activate
set AIRFLOW_HOME=%CD%\airflow
airflow scheduler

# Terminal 2 - Webserver  
.venv\Scripts\activate
set AIRFLOW_HOME=%CD%\airflow
airflow webserver
```

## 📊 VÉRIFICATION

### 1. Vérifier qu'Airflow tourne

**Double-cliquez** sur : `VERIFIER_COLLECTE_AUTO.cmd`

Ce script affichera :
- ✅ Statut Airflow (actif/inactif)
- 📅 Date de la dernière collecte
- 📊 Statistiques des données d'aujourd'hui
- ⚠️ Actions recommandées

### 2. Interface Web Airflow

Ouvrez http://localhost:8080 et vérifiez :

- **DAGs** : `brvm_collecte_horaire_REELLE` doit être visible
- **Toggle** : Doit être sur ON (vert)
- **Runs** : Devrait montrer les exécutions horaires
- **Logs** : Cliquez sur une tâche pour voir les logs

### 3. Logs Airflow

Consultez les logs dans :
- `airflow/logs/scheduler.log` - Logs du scheduler
- `airflow/logs/webserver.log` - Logs du webserver
- `airflow/logs/dag_id=brvm_collecte_horaire_REELLE/` - Logs des exécutions

## 🔄 CALENDRIER D'EXÉCUTION

**Heures de collecte** (Lundi - Vendredi) :
- 09:00 - Ouverture BRVM
- 10:00 - Collecte horaire
- 11:00 - Collecte horaire
- 12:00 - Collecte horaire
- 13:00 - Collecte horaire
- 14:00 - Collecte horaire
- 15:00 - Collecte horaire
- 16:00 - Clôture BRVM

**Total** : 8 collectes par jour × 5 jours = **40 collectes par semaine**

## 🛠️ DÉPANNAGE

### Airflow ne démarre pas

**Causes possibles** :
1. Port 8080 déjà utilisé
2. Base de données Airflow non initialisée
3. Problème de permissions

**Solutions** :
```bash
# Réinitialiser Airflow
cd airflow
del airflow.db
del -r logs/*
cd ..
.venv\Scripts\activate
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

### Scraping échoue

Si le scraping du site BRVM échoue :

1. **Vérifier** : `scripts/connectors/brvm_scraper_production.py` existe
2. **Tester** : `python scripts/connectors/brvm_scraper_production.py`
3. **Fallback** : Saisie manuelle via `python mettre_a_jour_cours_brvm.py`

### Aucune donnée collectée

Le DAG ne génère **JAMAIS** de fausses données. Si aucune collecte :

1. **Vérifier** que le site BRVM est accessible
2. **Collecter manuellement** : `python collecter_quotidien_intelligent.py`
3. **Importer CSV** : `python collecter_csv_automatique.py`

## 📝 FICHIERS IMPORTANTS

| Fichier | Description |
|---------|-------------|
| `airflow/dags/brvm_collecte_horaire_REELLE.py` | DAG de collecte horaire |
| `start_airflow_background.bat` | Démarrage Airflow |
| `VERIFIER_COLLECTE_AUTO.cmd` | Vérifier l'état de la collecte |
| `collecter_quotidien_intelligent.py` | Collecte manuelle intelligente |
| `mettre_a_jour_cours_brvm.py` | Saisie manuelle guidée |
| `scripts/connectors/brvm_scraper_production.py` | Scraper site BRVM |

## ✅ CHECKLIST COLLECTE AUTOMATIQUE

- [ ] Airflow installé (`pip install apache-airflow`)
- [ ] Base de données initialisée (`airflow db init`)
- [ ] User admin créé
- [ ] Airflow démarré (`start_airflow_background.bat`)
- [ ] Interface accessible (http://localhost:8080)
- [ ] DAG `brvm_collecte_horaire_REELLE` activé
- [ ] Scraper fonctionnel OU saisie manuelle prête
- [ ] Données d'aujourd'hui en base (100% réelles)

## 🎯 RÉSUMÉ

**ACTUELLEMENT** : ❌ Collecte automatique INACTIVE (Airflow non démarré)

**POUR ACTIVER** : ✅ Double-cliquer sur `start_airflow_background.bat`

**FRÉQUENCE** : ⏰ Toutes les heures de 9h à 16h (lun-ven)

**QUALITÉ** : 🔴 100% données RÉELLES - Zéro tolérance pour simulation

**INTERFACE** : 🌐 http://localhost:8080 (admin/admin)

**VÉRIFICATION** : 📊 Exécuter `VERIFIER_COLLECTE_AUTO.cmd`

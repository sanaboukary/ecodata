# 🚀 AIRFLOW - COLLECTE AUTOMATIQUE COMPLÈTE

## ✅ Système Airflow Configuré

Votre plateforme dispose maintenant d'un **système de collecte automatique complet** utilisant **Apache Airflow** !

---

## 📊 DONNÉES COLLECTÉES AUTOMATIQUEMENT

### 1️⃣ BRVM (Bourse Régionale des Valeurs Mobilières)
- **Fréquence**: Toutes les heures de 9h à 16h (jours ouvrables)
- **Données**: **47 actions cotées**
- **Informations**: Prix (open, high, low, close), volume, secteur, pays
- **DAG**: `brvm_data_collection`

### 2️⃣ WorldBank (Banque Mondiale)
- **Fréquence**: Le 15 de chaque mois à 2h00
- **Données**: **35+ indicateurs économiques et sociaux**
  - Démographie (population, espérance de vie)
  - Économie (PIB, croissance, inflation, commerce)
  - Éducation (scolarisation, alphabétisation)
  - Santé (mortalité, médecins, dépenses santé)
  - Infrastructure (électricité, internet, téléphonie)
  - Environnement (CO2, forêts)
  - Dette & Aide
  - Emploi
- **Pays**: 15 pays d'Afrique de l'Ouest
- **DAG**: `worldbank_data_collection`

### 3️⃣ IMF (Fonds Monétaire International)
- **Fréquence**: Le 1er de chaque mois à 2h30
- **Données**: **20+ séries économiques**
  - Inflation (IPC mensuel) - 7 pays
  - Taux de change - 3 pays
  - Réserves internationales - 3 pays
  - PIB réel (annuel) - 7 pays
- **DAG**: `imf_data_collection`

### 4️⃣ AfDB (Banque Africaine de Développement)
- **Fréquence**: Trimestrielle (Jan/Avr/Jul/Oct) à 3h00
- **Données**: **6 indicateurs** × **8 pays** = 48 séries
  - Dette extérieure/intérieure
  - Croissance du PIB
  - IDE (Investissements Directs Étrangers)
  - Balance commerciale
  - Inflation
- **DAG**: `afdb_data_collection`

### 5️⃣ UN SDG (Nations Unies - ODD)
- **Fréquence**: Trimestrielle (Jan/Avr/Jul/Oct) à 3h15
- **Données**: **8 séries** Objectifs de Développement Durable
  - Taux de chômage
  - Pauvreté
  - Mortalité infantile
  - Éducation
  - Égalité des genres
  - Environnement
  - Eau & Assainissement
- **DAG**: `un_sdg_data_collection`

---

## 🎯 VOLUME TOTAL DE DONNÉES

| Source | Indicateurs | Pays | Obs. estimées/mois |
|--------|-------------|------|-------------------|
| BRVM | 47 actions | 8 | ~7,500 |
| WorldBank | 35 indicateurs | 15 | ~5,250 |
| IMF | 20 séries | 7 | ~1,200 |
| AfDB | 6 indicateurs | 8 | ~144 (trimestre) |
| UN SDG | 8 séries | 8 | ~192 (trimestre) |
| **TOTAL** | **116+** | **15+** | **~14,000+/mois** |

---

## 🚀 INSTALLATION & DÉMARRAGE

### Étape 1: Configuration initiale

```bash
# Windows
.venv\Scripts\python.exe setup_airflow.py
```

### Étape 2: Démarrer Airflow

**Option A: Script automatique (Windows)**
```cmd
start_airflow.bat
```

**Option B: Commandes manuelles**

Terminal 1 - Scheduler:
```bash
.venv\Scripts\python.exe -m airflow scheduler
```

Terminal 2 - Webserver:
```bash
.venv\Scripts\python.exe -m airflow webserver --port 8080
```

### Étape 3: Accéder à l'interface web

```
URL: http://localhost:8080
Username: admin
Password: admin
```

---

## 📋 GESTION DES DAGs

### Activer un DAG
1. Ouvrez l'interface web
2. Trouvez le DAG dans la liste
3. Cliquez sur le toggle pour l'activer (ON)
4. Le DAG s'exécutera automatiquement selon son planning

### Exécuter manuellement
1. Cliquez sur le nom du DAG
2. Cliquez sur le bouton "Play" (▶️)
3. Choisissez "Trigger DAG"

### Visualiser les logs
1. Cliquez sur le DAG
2. Cliquez sur le task
3. Onglet "Logs"

---

## 📂 STRUCTURE DES FICHIERS

```
Implementation plateforme/
├── airflow/
│   ├── dags/
│   │   ├── brvm_dag.py              # DAG BRVM
│   │   ├── worldbank_dag.py         # DAG WorldBank
│   │   ├── imf_dag.py               # DAG IMF
│   │   └── afdb_un_dag.py           # DAG AfDB & UN
│   ├── plugins/                     # Plugins personnalisés
│   ├── config/
│   │   └── airflow.env              # Configuration
│   └── airflow.db                   # Base de données Airflow
├── logs/
│   └── airflow/                     # Logs Airflow
├── setup_airflow.py                 # Script de configuration
└── start_airflow.bat                # Script de démarrage Windows
```

---

## 🔍 MONITORING

### Tableau de bord Airflow
- **DAG Runs**: Historique d'exécution
- **Task Duration**: Temps d'exécution par tâche
- **Success Rate**: Taux de réussite
- **Next Run**: Prochaine exécution planifiée

### Vérifier les données dans MongoDB

```python
python show_complete_data.py
```

---

## ⚙️ CONFIGURATION AVANCÉE

### Modifier la fréquence d'un DAG

Éditez le fichier DAG correspondant et changez `schedule_interval`:

```python
# Exemples:
schedule_interval='0 9-16 * * 1-5'    # Toutes les heures (9h-16h, lun-ven)
schedule_interval='0 2 15 * *'        # Le 15 de chaque mois à 2h
schedule_interval='30 2 1 * *'        # Le 1er de chaque mois à 2h30
schedule_interval='0 3 1 1,4,7,10 *'  # Trimestriel
schedule_interval='@daily'            # Quotidien
schedule_interval='@weekly'           # Hebdomadaire
```

### Ajouter de nouveaux indicateurs

1. Ouvrez le DAG concerné (ex: `worldbank_dag.py`)
2. Ajoutez l'indicateur dans le dictionnaire
3. Sauvegardez
4. Airflow détectera automatiquement le changement

---

## 🆘 DÉPANNAGE

### Le scheduler ne démarre pas
```bash
# Réinitialiser la base de données
.venv\Scripts\python.exe -m airflow db reset
.venv\Scripts\python.exe setup_airflow.py
```

### Un DAG n'apparaît pas
1. Vérifiez qu'il n'y a pas d'erreur de syntaxe Python
2. Regardez les logs: `logs/airflow/scheduler/`
3. Rafraîchissez la page web

### Une tâche échoue
1. Consultez les logs de la tâche
2. Vérifiez la connexion MongoDB
3. Vérifiez la connexion Internet (pour les API externes)

---

## ✨ AVANTAGES D'AIRFLOW

✅ **Interface Web**: Visualisation et contrôle complet
✅ **Retry automatique**: 2-3 tentatives en cas d'échec
✅ **Parallélisation**: Plusieurs tâches en même temps
✅ **Monitoring**: Historique et statistiques détaillées
✅ **Alertes**: Notifications en cas d'échec (configurable)
✅ **Flexible**: Modification facile des plannings
✅ **Robuste**: Gestion des erreurs et timeouts
✅ **Scalable**: Peut gérer des centaines de DAGs

---

## 📊 COMPARAISON: AVANT vs MAINTENANT

### AVANT (APScheduler simple)
- ⚠️ 1 indicateur par source
- ⚠️ Pas d'interface visuelle
- ⚠️ Logs basiques
- ⚠️ Pas de retry configuré
- ✅ 47 actions BRVM

### MAINTENANT (Airflow)
- ✅ **116+ indicateurs** toutes sources
- ✅ Interface web complète
- ✅ Logs détaillés par tâche
- ✅ Retry automatique
- ✅ Monitoring en temps réel
- ✅ ~14,000 observations/mois

---

## 🎓 PROCHAINES ÉTAPES

1. ✅ Démarrer Airflow (`start_airflow.bat`)
2. ✅ Activer tous les DAGs
3. ✅ Laisser la première exécution se terminer
4. ✅ Vérifier les données dans MongoDB
5. ✅ Configurer des alertes email (optionnel)
6. ✅ Ajouter d'autres sources si nécessaire

---

**🎉 Votre plateforme est maintenant totalement automatisée avec Airflow !**

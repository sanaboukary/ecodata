# 🚀 SYSTÈME DE COLLECTE AUTOMATIQUE COMPLÈTE

## Vue d'ensemble

Ce système collecte automatiquement **TOUTES** les données économiques et financières nécessaires depuis **5 sources** sans intervention humaine.

## 📊 Sources et Couverture

### 1. **World Bank** (35 indicateurs × 15 pays)
- **Démographie** : Population, espérance de vie, urbanisation
- **Économie** : PIB, croissance, commerce, IDE, dette
- **Éducation** : Scolarisation, alphabétisation, dépenses
- **Santé** : Mortalité, médecins, dépenses, eau potable
- **Infrastructure** : Électricité, Internet, téléphonie, routes
- **Environnement** : CO2, forêts, eau
- **Social** : Pauvreté, chômage, aide au développement

### 2. **FMI** (11 indicateurs × 7 pays)
- Inflation, croissance PIB, PIB nominal/par habitant
- Chômage, solde budgétaire, dette publique
- Balance courante, exportations, importations

### 3. **ONU SDG** (8 indicateurs × 8 pays)
- Objectifs de Développement Durable
- Chômage, pauvreté, santé, éducation
- Eau, électricité, émissions, genre

### 4. **BAD** (6 indicateurs × 8 pays)
- Dette extérieure, service de la dette
- Épargne, investissement
- Solde budgétaire et extérieur

### 5. **BRVM** (47 actions)
- Cotations **en temps réel** (collecte horaire 24/7)
- Volumes, variations, capitalisation
- 8 pays CEDEAO

---

## 🎯 Méthodes de Collecte

### Option 1 : **Collecte Immédiate Manuelle** (15-20 minutes)

Double-cliquez sur :
```
LANCER_COLLECTE_COMPLETE.bat
```

Ou en ligne de commande :
```bash
.venv\Scripts\python.exe collecte_automatique_complete.py
```

**Avantages** :
- ✅ Exécution immédiate
- ✅ Contrôle total
- ✅ Affichage détaillé de la progression

### Option 2 : **Airflow - Collecte Hebdomadaire Automatique** (Recommandé)

Le DAG `master_complete_collection` s'exécute **automatiquement chaque dimanche à 3h du matin**.

#### Démarrer Airflow :
```bash
start_airflow_background.bat
```

#### Vérifier le statut :
```bash
check_airflow_status.bat
```

#### Interface Web :
http://localhost:8080 (admin/admin)

**Avantages** :
- ✅ 100% automatique
- ✅ Tourne en arrière-plan
- ✅ Monitoring web
- ✅ Retry automatique en cas d'échec
- ✅ Parallélisation des collectes

---

## 📅 Planning de Collecte Airflow

| DAG | Schedule | Description |
|-----|----------|-------------|
| `brvm_data_collection_hourly` | ⏰ **Toutes les heures** | BRVM temps réel - 47 actions |
| `master_complete_collection` | 📅 Dimanche 3h | World Bank + IMF + UN + AfDB |
| `worldbank_data_collection` | 15 du mois 2h | World Bank seul (backup) |
| `imf_data_collection` | 1er du mois 2h30 | FMI mensuel (backup) |

**Note importante** : La BRVM est collectée **séparément toutes les heures** pour avoir des données de marché en temps réel.

---

## 🔧 Configuration

### Variables d'environnement (.env)
```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_NAME=centralisation_db
WB_BASE_URL=https://api.worldbank.org/v2
HTTP_TIMEOUT=30
```

### Pays CEDEAO (15 pays)
```
BEN (Bénin), BFA (Burkina Faso), CIV (Côte d'Ivoire),
GNB (Guinée-Bissau), MLI (Mali), NER (Niger), SEN (Sénégal),
TGO (Togo), GHA (Ghana), GMB (Gambie), GIN (Guinée),
LBR (Liberia), MRT (Mauritanie), NGA (Nigeria), SLE (Sierra Leone)
```

---

## 📊 Volumes de Données

| Source | Observations/mois | Total estimé |
|--------|-------------------|--------------|
| World Bank | ~5,250 | ~63,000/an |
| BRVM | ~7,500 | ~90,000/an |
| FMI | ~1,200 | ~14,400/an |
| ONU SDG | ~192 | ~2,304/an |
| BAD | ~144 | ~1,728/an |
| **TOTAL** | **~14,000+** | **~170,000+/an** |

---

## 🛠️ Gestion des Données

### Vérifier les données collectées :
```bash
python check_civ_population.py
python show_complete_data.py
```

### Historique des collectes :
```bash
python show_ingestion_history.py
```

### Vérifier MongoDB :
```bash
python verifier_connexion_db.py
```

---

## 🚨 Dépannage

### Problème : Airflow ne démarre pas
```bash
# Vérifier les PIDs
cat airflow_pids.txt

# Relancer
stop_airflow.bat
start_airflow_background.bat
```

### Problème : Données manquantes
1. Vérifier les logs Airflow : `airflow/logs/`
2. Vérifier la connexion MongoDB
3. Relancer la collecte manuellement

### Problème : Erreur API
- World Bank : Vérifier `WB_BASE_URL`
- FMI : Vérifier accès internet
- BRVM : Peut utiliser données mock si API indisponible

---

## 📈 Dashboards

Une fois les données collectées, elles sont **automatiquement disponibles** dans :

- **BRVM** : http://127.0.0.1:8000/dashboards/brvm/
- **World Bank** : http://127.0.0.1:8000/dashboards/worldbank/
- **FMI** : http://127.0.0.1:8000/dashboards/imf/
- **ONU** : http://127.0.0.1:8000/dashboards/un/
- **BAD** : http://127.0.0.1:8000/dashboards/afdb/

---

## ✅ Checklist de Mise en Production

- [ ] MongoDB tourne sur port 27017
- [ ] Variables `.env` configurées
- [ ] Airflow démarré : `start_airflow_background.bat`
- [ ] DAG `master_complete_collection` activé dans l'UI
- [ ] Collecte initiale lancée : `LANCER_COLLECTE_COMPLETE.bat`
- [ ] Serveur Django tourne : `DEMARRER_SERVEUR.bat`
- [ ] Dashboards accessibles

---

## 🎓 Pour Aller Plus Loin

### Ajouter un nouvel indicateur World Bank :
Éditer `airflow/dags/master_complete_dag.py` :
```python
WORLDBANK_INDICATORS = {
    'VOTRE.INDICATEUR': 'Description',
    # ... autres
}
```

### Changer la fréquence de collecte :
```python
schedule_interval='0 3 * * 0',  # Cron expression
```

### Ajouter une notification :
```python
'email_on_failure': True,
'email': 'votre@email.com',
```

---

## 📞 Support

En cas de problème, consulter :
- `SCHEDULER_SETUP_COMPLETE.md`
- `AIRFLOW_SETUP.md`
- `PROJECT_STRUCTURE.md`

**Système opérationnel 24/7 avec Airflow** 🚀

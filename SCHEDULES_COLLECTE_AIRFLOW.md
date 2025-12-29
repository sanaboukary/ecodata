# 📅 Planning de Collecte Automatique Airflow

## Vue d'ensemble

Le système utilise **2 DAGs Airflow** pour la collecte automatique :

1. **`brvm_data_collection_hourly`** - Collecte BRVM toutes les heures
2. **`master_complete_collection`** - Collecte hebdomadaire des autres sources

---

## 📈 BRVM - Collecte Horaire (Temps Réel)

### Configuration
- **DAG**: `brvm_data_collection_hourly`
- **Fichier**: `airflow/dags/brvm_dag.py`
- **Schedule**: `0 * * * *` ⏰ **TOUTES LES HEURES (24/7)**
- **Tags**: `brvm`, `market-data`, `hourly`, `real-time`

### Données collectées
- **47 actions cotées BRVM**
- Cours, variations, volumes
- 8 pays CEDEAO (Bénin, Burkina Faso, Côte d'Ivoire, Mali, Niger, Sénégal, Togo, Guinée-Bissau)

### Pipeline ETL
```
extract_brvm → load_brvm → validate_brvm
```

### Prochaines exécutions (exemples)
```
Aujourd'hui:  01:00, 02:00, 03:00, 04:00... 23:00
Demain:       00:00, 01:00, 02:00, 03:00... 23:00
```

### Volume estimé
- **~1,000 observations/jour** (47 actions × ~20 points de données/jour)
- **~30,000 observations/mois**
- **~365,000 observations/an**

---

## 🌐 Sources Hebdomadaires - Collecte Automatique Dimanche

### Configuration
- **DAG**: `master_complete_collection`
- **Fichier**: `airflow/dags/master_complete_dag.py`
- **Schedule**: `0 3 * * 0` 📅 **Chaque Dimanche à 3h du matin**
- **Tags**: `master`, `weekly`, `auto-collection`, `worldbank-imf-un-afdb`

### Sources collectées (4 sources)

#### 1️⃣ World Bank (35 indicateurs)
**Pays**: 15 pays CEDEAO
**Indicateurs**:
- **Démographie** (3): Population, Espérance de vie, Population urbaine
- **Économie** (12): PIB, Croissance, PIB/hab, RNB, Export, Import, Inflation, Commerce, IDE, Dette
- **Éducation** (4): Scolarisation primaire/secondaire, Alphabétisation, Dépenses éducation
- **Santé** (7): Mortalité maternelle/infantile, Médecins, Dépenses santé, Eau potable, Sanitaires, Vaccins
- **Infrastructure** (5): Électricité, Internet, Routes, Téléphones mobiles, Énergie renouvelable
- **Secteur Financier** (4): Crédit privé, Dépôts, Capitalisation, Transactions

#### 2️⃣ IMF (11 indicateurs)
**Pays**: 7 pays (BEN, BFA, CIV, GHA, MLI, NER, SEN)
**Indicateurs**:
- PCPIPCH: Inflation (IPC)
- NGDP_RPCH: Croissance PIB réel
- NGDPD: PIB nominal (USD)
- NGDPDPC: PIB par habitant
- PPPPC: PIB PPA par habitant
- LUR: Taux de chômage
- GGXCNL_NGDP: Solde budgétaire
- GGXWDG_NGDP: Dette publique
- BCA_NGDPD: Balance des paiements
- TX_RPCH: Croissance exportations
- TM_RPCH: Croissance importations

#### 3️⃣ UN SDG (8 indicateurs)
**Pays**: 8 pays (BEN, BFA, CIV, GIN, MLI, NER, SEN, TGO)
**Indicateurs**:
- Pauvreté (SDG 1)
- Faim (SDG 2)
- Santé (SDG 3)
- Éducation (SDG 4)
- Égalité des sexes (SDG 5)
- Eau et assainissement (SDG 6)
- Énergie (SDG 7)
- Climat (SDG 13)

#### 4️⃣ AfDB (6 indicateurs)
**Pays**: 8 pays (BEN, BFA, CIV, GIN, MLI, NER, SEN, TGO)
**Indicateurs**:
- Note de crédit
- Dette/PIB
- Service de la dette
- Déficit budgétaire
- Réserves de change
- Durabilité de la dette

### Pipeline Parallèle
```
┌─ collect_worldbank ─┐
├─ collect_imf        ├──→ validate_all
├─ collect_un_sdg     │
└─ collect_afdb      ─┘
```

### Prochaines exécutions
```
Dimanche 24 nov 2025:  03:00
Dimanche 01 déc 2025:  03:00
Dimanche 08 déc 2025:  03:00
Dimanche 15 déc 2025:  03:00
```

### Volume estimé (hebdomadaire)
- **World Bank**: ~5,250 obs (35 indicateurs × 15 pays × 10 années)
- **IMF**: ~770 obs (11 indicateurs × 7 pays × 10 années)
- **UN SDG**: ~64 obs (8 indicateurs × 8 pays)
- **AfDB**: ~48 obs (6 indicateurs × 8 pays)
- **TOTAL/semaine**: ~6,000 observations
- **TOTAL/an**: ~312,000 observations

---

## 📊 Récapitulatif Total

| Source | Fréquence | DAG | Indicateurs | Obs/an |
|--------|-----------|-----|-------------|--------|
| **BRVM** | **Toutes les heures** | `brvm_data_collection_hourly` | 47 actions | ~365,000 |
| World Bank | Hebdomadaire (Dim 3h) | `master_complete_collection` | 35 indicateurs | ~273,000 |
| IMF | Hebdomadaire (Dim 3h) | `master_complete_collection` | 11 indicateurs | ~40,000 |
| UN SDG | Hebdomadaire (Dim 3h) | `master_complete_collection` | 8 indicateurs | ~3,300 |
| AfDB | Hebdomadaire (Dim 3h) | `master_complete_collection` | 6 indicateurs | ~2,500 |
| **TOTAL** | - | **2 DAGs** | **107 indicateurs** | **~683,800** |

---

## 🚀 Activation dans Airflow

### 1. Accéder à l'interface web
```
http://localhost:8080
Login: admin / admin
```

### 2. Activer les DAGs
Dans l'interface Airflow, localiser et **activer (toggle ON)** :
- ✅ `brvm_data_collection_hourly` (collecte horaire BRVM)
- ✅ `master_complete_collection` (collecte hebdomadaire WB/IMF/UN/AfDB)

### 3. Vérifier les prochaines exécutions
- **BRVM**: Prochaine heure pile (ex: si 14h37 → 15h00)
- **Autres sources**: Prochain dimanche à 3h du matin

---

## 🔍 Monitoring

### Logs Airflow
```bash
# Logs généraux
airflow/logs/

# Logs BRVM horaire
airflow/logs/brvm_data_collection_hourly/

# Logs collecte hebdomadaire
airflow/logs/master_complete_collection/
```

### Vérification MongoDB
```bash
# Script de vérification rapide
python etat_base_donnees.py

# Vérifier BRVM spécifiquement
python afficher_brvm_detaille.py
```

### Interface Web Airflow
- **Dashboard**: Voir les DAGs actifs et leur statut
- **Graph View**: Visualiser le pipeline ETL
- **Tree View**: Historique des exécutions
- **Logs**: Consulter les logs de chaque task

---

## ⚙️ Configuration Technique

### Retries et Timeouts

**BRVM (horaire)**:
- Retries: 3 tentatives
- Retry delay: 5 minutes
- Execution timeout: 30 minutes

**Master (hebdomadaire)**:
- Retries: 1 tentative
- Retry delay: 30 minutes
- Execution timeout: 3 heures

### Variables d'environnement
```bash
AIRFLOW_HOME=E:/DISQUE C/Desktop/Implementation plateforme/airflow
DJANGO_SETTINGS_MODULE=plateforme_centralisation.settings
MONGODB_URI=mongodb://localhost:27018
MONGODB_NAME=centralisation_db
```

---

## 🎯 Points Clés

1. **BRVM = TEMPS RÉEL** ⏰
   - Collecte **toutes les heures** (24/7)
   - Données de marché fraîches
   - ~1,000 observations/jour

2. **Autres sources = HEBDOMADAIRE** 📅
   - Collecte **dimanche matin 3h**
   - Données macro-économiques stables
   - ~6,000 observations/semaine

3. **Séparation logique**
   - 2 DAGs distincts pour flexibilité
   - BRVM indépendante (haute fréquence)
   - Autres sources regroupées (basse fréquence)

4. **Zéro intervention humaine**
   - Airflow scheduler tourne en arrière-plan
   - Collecte automatique 24/7
   - Logs et monitoring via Web UI

---

## 📞 Troubleshooting

### BRVM ne collecte pas toutes les heures
```bash
# Vérifier que le DAG est activé
1. Ouvrir http://localhost:8080
2. Chercher brvm_data_collection_hourly
3. Vérifier toggle = ON
4. Consulter les logs si erreurs
```

### Master DAG ne s'exécute pas le dimanche
```bash
# Vérifier le planning
1. Ouvrir http://localhost:8080
2. Chercher master_complete_collection
3. Vérifier "Next Run" = dimanche 03:00
4. Activer le DAG si désactivé
```

### Airflow ne répond pas
```bash
# Vérifier les processus
cat airflow_pids.txt

# Redémarrer si nécessaire
start_airflow_background.bat
```

---

**✅ Avec cette configuration, vous avez une collecte automatique complète :**
- **BRVM**: Données de marché en quasi temps-réel (chaque heure)
- **Macro-économie**: Mises à jour hebdomadaires des indicateurs structurels
- **Autonome**: Fonctionne 24/7 sans intervention
- **Scalable**: ~680,000 observations collectées par an

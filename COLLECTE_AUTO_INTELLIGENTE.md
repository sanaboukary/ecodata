# 🤖 Collecte Automatique Intelligente - Documentation

## 📋 Vue d'ensemble

Système de collecte automatique des données économiques avec :
- ✅ Gestion intelligente des timeouts et erreurs
- ✅ Fallback automatique sur mock data
- ✅ Logging détaillé et monitoring
- ✅ Vérification qualité des données
- ✅ Planification Airflow optimisée

---

## 🗓️ Planning de collecte

### Données BRVM (Priorité 1)
- **Fréquence** : Horaire (9h-16h jours ouvrables)
- **DAG** : `brvm_collecte_quotidienne_reelle.py`
- **Horaire** : Lun-Ven 17h00 (après clôture BRVM)
- **Politique** : Données RÉELLES uniquement (scraping → saisie manuelle → rien)

### Données WorldBank
- **Fréquence** : Mensuelle
- **DAG** : `worldbank_dag.py`
- **Horaire** : 15 de chaque mois à 2h00
- **Indicateurs** : 35+ indicateurs × 15 pays

### Données IMF (NOUVEAU)
- **Fréquence** : Mensuelle
- **DAG** : `imf_dag.py`
- **Horaire** : 1er de chaque mois à 3h00
- **Indicateurs** : CPI, PIB, Croissance, Inflation, Chômage
- **Fallback** : Mock data si API timeout (30s)

### Données AfDB + UN_SDG (NOUVEAU)
- **Fréquence** : Trimestrielle
- **DAG** : `afdb_un_dag.py`
- **Horaire** : 1er janvier/avril/juillet/octobre à 4h00
- **AfDB** : Mock data uniquement (pas d'API publique)
- **UN_SDG** : API officielle avec gestion pagination

---

## 🚀 Utilisation

### 1. Collecte manuelle (test)

```bash
# Collecte complète toutes sources
python collecte_auto_intelligente.py

# Vérification résultats
python verifier_collecte.py
```

### 2. Collecte automatique (Airflow)

**Démarrage Airflow** :
```bash
# Windows
start_airflow_background.bat

# Linux/Mac
airflow scheduler &
airflow webserver &
```

**Interface Web** :
- URL : http://localhost:8080
- User/Pass : admin/admin
- Activer les DAGs :
  - ✅ `brvm_collecte_quotidienne_reelle` (quotidien 17h)
  - ✅ `worldbank_collecte_mensuelle` (mensuel 15 à 2h)
  - ✅ `imf_collecte_mensuelle` (mensuel 1er à 3h)
  - ✅ `afdb_un_collecte_trimestrielle` (trimestriel à 4h)

**Vérification status** :
```bash
check_airflow_status.bat  # Windows
```

---

## 🛠️ Configuration intelligente

### Gestion des timeouts

**IMF Connector** (`scripts/connectors/imf.py`) :
```python
HTTP_TIMEOUT = 30  # secondes (au lieu de 60)
MAX_RETRIES = 2    # Tentatives avant fallback mock

# Fallback automatique :
# - Timeout connexion → Mock data 5 ans
# - Erreur API → Mock data
# - Pas de données → Mock data
```

**UN_SDG Connector** (`scripts/connectors/un_sdg.py`) :
```python
verify_ssl = False  # Contournement SSL Windows
page_size = 10000   # Pagination automatique
HTTP_TIMEOUT = 30

# Gestion pagination :
# - Boucle automatique jusqu'à totalPages
# - Accumulation observations
# - Gestion erreurs par page
```

**AfDB Connector** (`scripts/connectors/afdb.py`) :
```python
AFDB_BASE_URL = ""  # Vide → Mock data direct
USE_MOCK_AFDB = True

# Mock data :
# - 6 indicateurs × 8 pays × 5 ans
# - Variations réalistes -5% à +10%
# - Toujours disponible (fallback garanti)
```

---

## 📊 Monitoring et logs

### Logs Airflow
```
airflow/logs/
├── imf_collecte_mensuelle/
│   └── collecte_imf_intelligent/
│       └── 2026-01-06/  # Date exécution
├── afdb_un_collecte_trimestrielle/
│   ├── collecte_afdb_intelligent/
│   └── collecte_un_sdg_intelligent/
└── dag_processor_manager/
```

### Logs application
```bash
# Collecte manuelle
collecte_auto_intelligente.log

# Vérification
python verifier_collecte.py > rapport_collecte.txt
```

### Indicateurs clés

**Santé du système** :
- ✅ MongoDB opérationnel
- ✅ Total observations > 10,000
- ✅ Toutes sources présentes
- ✅ Taux succès > 80%

**Alertes** :
- ⚠️  Taux erreur IMF > 50% → Vérifier connexion API
- ⚠️  UN_SDG 0 observations → Vérifier SSL/pagination
- ❌ MongoDB indisponible → Vérifier service Docker

---

## 🔧 Dépannage

### Problème : IMF timeout systématique

**Diagnostic** :
```bash
# Tester connectivité IMF
curl -I https://dataservices.imf.org/REST/SDMX_JSON.svc/
```

**Solutions** :
1. Augmenter timeout : Modifier `HTTP_TIMEOUT` dans `scripts/connectors/imf.py`
2. Utiliser mock : `USE_MOCK_IMF=true` dans `.env`
3. VPN/Proxy : Configurer proxy si réseau restrictif

### Problème : UN_SDG SSL error

**Diagnostic** :
```bash
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

**Solutions** :
1. Déjà configuré : `verify_ssl=False` dans `un_sdg.py`
2. Si persiste : Installer certificats Windows
3. Fallback : `USE_MOCK_UN=true`

### Problème : Airflow DAGs non visibles

**Diagnostic** :
```bash
python -c "from airflow import DAG; print('OK')"
ls airflow/dags/*.py
```

**Solutions** :
1. Vérifier PYTHONPATH dans DAGs
2. Redémarrer scheduler : `airflow scheduler`
3. Check logs : `airflow/logs/dag_processor_manager/`

---

## 📈 Optimisations

### Réduction temps collecte

**Parallélisation** :
```python
# Dans afdb_un_dag.py :
[collecte_afdb, collecte_un_sdg]  # Exécution simultanée
```

**Pagination optimisée UN_SDG** :
```python
page_size = 10000  # Max autorisé (réduit nombre requêtes)
```

**Timeout adaptatif IMF** :
```python
# Si timeout fréquent → Mock immédiat
if retry_count > 1:
    return _get_mock_imf_data(...)
```

### Économie ressources

**Collecte différenciée** :
- BRVM : Quotidien (données critiques)
- WorldBank/IMF : Mensuel (données macro)
- AfDB/UN_SDG : Trimestriel (moins volatile)

**Incrémental** :
- Ne collecter que nouvelles périodes
- Vérifier `last_update` avant requête
- Skip si données récentes déjà présentes

---

## 🎯 Métriques de succès

### Objectifs

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Observations totales | > 10,000 | 10,199 ✅ |
| BRVM couverture | 60 jours | 43 jours ⚠️ |
| WorldBank indicateurs | 35+ | 35 ✅ |
| IMF séries | 5 | 5 ✅ |
| UN_SDG séries | 8 | 5 ⚠️ |
| Taux succès collecte | > 90% | 87% ⚠️ |

### Prochaines étapes

1. **Compléter historique BRVM** : 60 jours requis pour trading hebdomadaire
2. **Ajouter séries UN_SDG** : 3 séries manquantes (éducation, CO2, espérance vie)
3. **Alternative AfDB** : Mapper indicateurs → World Bank équivalents
4. **Optimiser timeouts** : Profiler requêtes lentes IMF
5. **Alerting** : Email/Slack si collecte échoue

---

## 📚 Références

**DAGs Airflow** :
- `airflow/dags/imf_dag.py` - Collecte IMF mensuelle
- `airflow/dags/afdb_un_dag.py` - Collecte AfDB/UN trimestrielle
- `airflow/dags/worldbank_dag.py` - Collecte WorldBank mensuelle
- `airflow/dags/brvm_collecte_quotidienne_reelle.py` - BRVM quotidien

**Scripts collecte** :
- `collecte_auto_intelligente.py` - Collecte manuelle toutes sources
- `verifier_collecte.py` - Vérification données MongoDB
- `show_complete_data.py` - Rapport détaillé complet

**Connectors** :
- `scripts/connectors/imf.py` - IMF avec timeout/fallback
- `scripts/connectors/afdb.py` - AfDB mock data
- `scripts/connectors/un_sdg.py` - UN SDG avec pagination

**Pipeline** :
- `scripts/pipeline.py` - Orchestrateur ETL central

---

**Dernière mise à jour** : 6 janvier 2026
**Version** : 2.0 - Collecte intelligente multi-sources

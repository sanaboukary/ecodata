# 🔄 COLLECTE AUTOMATIQUE HORAIRE BRVM

## 📋 Vue d'ensemble

Système de collecte automatique des cours BRVM **toutes les heures, tous les jours ouvrables**.

### ✅ Caractéristiques

- **Fréquence**: Toutes les heures de 9h à 16h (heures de marché)
- **Jours**: Lundi à vendredi (jours ouvrables uniquement)
- **Source**: https://www.brvm.org/fr/cours-actions/investisseurs
- **Politique**: TOLÉRANCE ZÉRO - Données réelles uniquement
- **Automatisation**: Airflow + Retry automatique (3 tentatives)

## 🚀 Démarrage Rapide

### Option 1: Collecte Immédiate

```bash
# Collecter maintenant
python collecter_brvm_horaire_auto.py

# OU via interface Windows
LANCER_COLLECTE_HORAIRE.cmd → Option 1
```

### Option 2: Activation Collecte Automatique (Recommandé)

```bash
# Démarrer Airflow
start_airflow_background.bat

# Interface web
http://localhost:8080

# Activer le DAG: brvm_collecte_horaire
```

## 📂 Fichiers du Système

| Fichier | Description |
|---------|-------------|
| `collecter_brvm_horaire_auto.py` | Script de collecte horaire |
| `airflow/dags/brvm_collecte_horaire.py` | DAG Airflow pour automatisation |
| `LANCER_COLLECTE_HORAIRE.cmd` | Interface Windows |
| `collecte_brvm_horaire.log` | Logs des collectes |

## ⚙️ Configuration Airflow

### DAG: `brvm_collecte_horaire`

```python
schedule_interval='0 9-16 * * 1-5'  # Toutes les heures 9h-16h, lun-ven
retries=3                           # 3 tentatives en cas d'échec
retry_delay=5 minutes               # Attendre 5 min entre tentatives
```

### Horaires de Collecte

| Heure | Lun | Mar | Mer | Jeu | Ven | Sam | Dim |
|-------|-----|-----|-----|-----|-----|-----|-----|
| 09:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 10:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 11:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 12:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 13:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 14:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 15:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |
| 16:00 | ✅  | ✅  | ✅  | ✅  | ✅  | ❌  | ❌  |

**Total**: 8 collectes par jour × 5 jours = **40 collectes par semaine**

## 📊 Données Collectées

### Format MongoDB

```javascript
{
  source: 'BRVM',
  dataset: 'STOCK_PRICE',
  key: 'SNTS',  // Symbole action
  ts: '2026-01-08',
  value: 25500,  // Cours de clôture en FCFA
  attrs: {
    symbole: 'SNTS',
    nom: 'Sonatel',
    cours_cloture: 25500,
    volume: 1234,
    variation: 2.3,  // En pourcentage
    data_quality: 'REAL_SCRAPER',
    source_url: 'https://www.brvm.org/fr/cours-actions/investisseurs',
    collecte_datetime: '2026-01-08T11:15:00',
    collecte_heure: '11:15:00'
  }
}
```

### Actions Collectées

- **Total**: 47 actions cotées à la BRVM
- **Mise à jour**: Chaque heure pendant les heures de marché
- **Historique**: Conservation de toutes les collectes horaires

## 🔍 Monitoring

### Logs

```bash
# Voir les logs en temps réel
tail -f collecte_brvm_horaire.log

# Logs Airflow
airflow/logs/brvm_collecte_horaire/
```

### Dashboard

```bash
# Vérifier les données collectées
http://127.0.0.1:8000/brvm/

# Airflow monitoring
http://localhost:8080
```

### Vérification Manuelle

```python
# Vérifier dernière collecte
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Dernière collecte
latest = db.curated_observations.find_one(
    {'source': 'BRVM', 'dataset': 'STOCK_PRICE'},
    sort=[('attrs.collecte_datetime', -1)]
)

if latest:
    print(f'Dernière collecte: {latest[\"attrs\"][\"collecte_datetime\"]}')
    print(f'Action: {latest[\"key\"]} = {latest[\"value\"]} FCFA')
"
```

## 🛠️ Maintenance

### Arrêter la Collecte Automatique

```bash
# Stopper Airflow
taskkill /F /IM airflow.exe

# OU
# Désactiver le DAG dans l'interface web Airflow
```

### Relancer après Erreur

```bash
# Airflow relance automatiquement (3 tentatives)
# Ou manuellement:
python collecter_brvm_horaire_auto.py
```

### Nettoyer les Logs

```bash
# Supprimer logs anciens (>30 jours)
find . -name "collecte_brvm_horaire.log.*" -mtime +30 -delete
```

## 🎯 Politique Tolérance Zéro

### Garanties

✅ **Données réelles uniquement** du site officiel BRVM
✅ **Validation** des cours (rejet si <= 0)
✅ **Traçabilité** complète (source_url, collecte_datetime)
✅ **Data quality** marquée `REAL_SCRAPER`

### Rejets Automatiques

❌ Cours à zéro
❌ Symboles invalides (< 3 caractères)
❌ Données manquantes
❌ Erreurs de parsing

## 📈 Statistiques Attendues

### Volume Quotidien

- **8 collectes/jour** × **47 actions** = **376 observations/jour**
- **Par semaine**: ~1,880 observations
- **Par mois**: ~7,520 observations

### Stockage MongoDB

- **Par observation**: ~500 bytes
- **Par jour**: ~188 KB
- **Par an**: ~68 MB

## 🚨 Alertes

### Conditions d'Alerte

1. **Échec de collecte**: 3 tentatives échouées
2. **Aucune donnée**: Site BRVM inaccessible
3. **Données incohérentes**: Validation échouée

### Actions Automatiques

- **Retry**: 3 tentatives avec délai de 5 min
- **Logging**: Erreur enregistrée dans les logs
- **Fallback**: Conserver dernières données valides

## 💡 Utilisation Avancée

### Collecte Personnalisée

```python
from collecter_brvm_horaire_auto import CollecteurBRVMHoraire

collecteur = CollecteurBRVMHoraire()

# Collecter maintenant
collecteur.collecter_maintenant()

# Vérifier si jour ouvrable
if collecteur.est_jour_ouvrable():
    print("Jour de marché")

# Vérifier heure de collecte
if collecteur.est_heure_collecte():
    print("Heure de collecte")
```

### Intégration Dashboard

Les données sont automatiquement disponibles dans:
- Dashboard BRVM: `/brvm/`
- API REST: `/api/brvm/latest/`
- Téléchargement: `/marketplace/`

---

**Statut**: ✅ Production Ready
**Version**: 1.0
**Date**: 8 janvier 2026

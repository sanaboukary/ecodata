# 📊 Système de Monitoring & Robustesse - Ingestion

## Nouvelles Fonctionnalités

### 1. Logging Structuré des Ingestions

Chaque exécution d'ingestion est maintenant automatiquement loggée dans MongoDB (`ingestion_runs` collection) avec :
- ✅ **Timestamp** (started_at)
- ✅ **Source** (BRVM, IMF, WorldBank, UN_SDG, AfDB)
- ✅ **Statut** (success/error)
- ✅ **Nombre d'observations** ingérées
- ✅ **Durée d'exécution** (secondes)
- ✅ **Message d'erreur** (si échec)
- ✅ **Paramètres** utilisés (dataset, key, indicator, etc.)

**Fichiers modifiés :**
- `scripts/mongo_utils.py` : Fonction `log_ingestion_run()`
- `scripts/pipeline.py` : Wrapper try/finally autour de chaque ingestion

### 2. Retry HTTP avec Backoff Exponentiel

Nouveau helper `scripts/_http.py` pour requêtes HTTP résilientes :
- ⚙️ **2 retries par défaut** avec backoff exponentiel (0.75s × 2^attempt)
- ⚙️ **Timeout configurable** (45s par défaut via .env)
- ⚙️ **Gestion intelligente** : retry sur 5xx, 429, timeouts ; pas de retry sur 4xx

**Fichiers modifiés :**
- `scripts/connectors/imf.py` : Utilise `get_json()` au lieu de `requests.get()`
- `scripts/connectors/un_sdg.py` : Pagination multi-pages + retry
- `scripts/connectors/afdb.py` : Utilise `get_json()` avec retry

### 3. Scheduler Automatique Amélioré

Fréquences d'ingestion optimisées par source :
- 📅 **BRVM** : Toutes les heures (9h-16h, Lun-Ven) — données boursières en temps réel
- 📅 **IMF** : Mensuel (1er jour du mois, 2h30 AM)
- 📅 **WorldBank** : Mi-mois (15, 2h00 AM)
- 📅 **UN SDG** : Trimestriel (Jan/Apr/Jul/Oct 1er, 3h15 AM)
- 📅 **AfDB** : Trimestriel (Jan/Apr/Jul/Oct 1er, 3h00 AM)

**Fichier modifié :**
- `ingestion/management/commands/start_scheduler.py`

**Lancement :**
```bash
python manage.py start_scheduler
```

### 4. Dashboard de Monitoring d'Ingestion

Nouvelle page d'administration accessible à `/administration/ingestion/` :
- 📊 **Stats par source** : Total runs, succès/erreurs, taux de réussite, dernière exécution
- 📊 **Historique détaillé** : 100 derniers runs avec timestamp, statut, durée, observations
- 📊 **Messages d'erreur** : Visibilité complète sur les échecs

**Fichiers créés/modifiés :**
- `dashboard/views.py` : Vue `ingestion_monitoring()`
- `dashboard/urls.py` : Route ajoutée
- `templates/dashboard/ingestion_monitoring.html` : Interface de monitoring

**Accès :**
```
http://localhost:8000/administration/ingestion/
```

## Scripts de Vérification

### Afficher l'historique complet
```bash
python show_ingestion_history.py
```
Affiche :
- Stats globales par source (total, succès, erreurs, taux)
- 5 dernières exécutions par source
- Résumé global multi-sources

### Tester une ingestion avec logging
```bash
# IMF
python -c "from scripts.pipeline import run_ingestion; run_ingestion('imf', dataset='IFS', key='M.CIV.PCPI_IX')"

# UN SDG
python -c "from scripts.pipeline import run_ingestion; run_ingestion('un', series='SL_TLF_UEM', area='204')"
```

## Configuration .env

```env
# Flags mock (IMF et UN maintenant en mode réel)
USE_MOCK_IMF=false
USE_MOCK_UN=false
USE_MOCK_AFDB=true

# Timeout HTTP (secondes)
HTTP_TIMEOUT=45

# Clés par défaut pour tests rapides
IMF_DATASET=IFS
IMF_KEY=M.CIV.PCPI_IX
UN_SERIES=SL_TLF_UEM
UN_AREA=204,854,384,624,466,562,686,768
```

## Architecture MongoDB

### Collections
1. **curated_observations** : Données normalisées multi-sources
2. **raw_events** : Événements bruts (payloads API)
3. **ingestion_runs** : Historique d'exécution (nouveau ✨)

### Exemple document `ingestion_runs`
```json
{
  "source": "IMF",
  "status": "success",
  "obs_count": 60,
  "duration_sec": 2.45,
  "started_at": ISODate("2025-11-06T14:30:00Z"),
  "params": {
    "dataset": "IFS",
    "key": "M.CIV.PCPI_IX"
  },
  "error_msg": null
}
```

## Prochaines Améliorations Possibles

- [ ] Alertes email/Slack sur échec d'ingestion
- [ ] Dashboard temps réel avec WebSocket pour live updates
- [ ] Métriques Prometheus/Grafana
- [ ] Tests unitaires pour chaque connecteur
- [ ] Retry intelligent avec circuit breaker (si > 3 échecs consécutifs, pause temporaire)
- [ ] Compression/archivage des runs anciens (> 6 mois)

## Résumé des Changements

✅ **Logging structuré** automatique dans MongoDB  
✅ **Retry HTTP** avec backoff exponentiel  
✅ **Pagination UN SDG** pour multi-pays  
✅ **Scheduler amélioré** avec fréquences adaptées  
✅ **Dashboard monitoring** pour surveillance en temps réel  
✅ **Script de vérification** rapide de l'historique  

**Impact :** Système d'ingestion 100% plus robuste, observable, et maintenable.

# ⏰ COLLECTE BRVM - TOUTES LES HEURES

## Configuration Actuelle

✅ **La BRVM est collectée TOUTES LES HEURES (24/7)**

### DAG Airflow
- **Nom**: `brvm_data_collection_hourly`
- **Fichier**: `airflow/dags/brvm_dag.py`
- **Schedule**: `0 * * * *` (cron expression pour chaque heure)
- **Données**: 47 actions cotées BRVM
- **Pays**: 8 pays CEDEAO

### Exemples d'exécution
```
00:00 - Collecte BRVM
01:00 - Collecte BRVM
02:00 - Collecte BRVM
03:00 - Collecte BRVM (+ collecte hebdomadaire autres sources si dimanche)
04:00 - Collecte BRVM
...
23:00 - Collecte BRVM
```

## Pourquoi toutes les heures ?

🔥 **Données de marché boursier = Temps réel**

- Les cotations changent constamment pendant les heures de trading
- Les investisseurs ont besoin de données fraîches
- Le volume de trading varie tout au long de la journée
- Permet de capturer les tendances intra-journalières

## Séparation des DAGs

### DAG 1: `brvm_data_collection_hourly`
- **Fréquence**: ⏰ TOUTES LES HEURES
- **Source**: BRVM uniquement (47 actions)
- **Raison**: Données de marché nécessitent fraîcheur

### DAG 2: `master_complete_collection`
- **Fréquence**: 📅 HEBDOMADAIRE (Dimanche 3h)
- **Sources**: World Bank, IMF, UN SDG, AfDB
- **Raison**: Données macro-économiques changent lentement

## Volume de données

### BRVM (horaire)
- **Par heure**: ~40-50 observations (47 actions)
- **Par jour**: ~1,000 observations
- **Par mois**: ~30,000 observations
- **Par an**: ~365,000 observations

### Autres sources (hebdomadaire)
- **Par semaine**: ~6,000 observations
- **Par mois**: ~24,000 observations
- **Par an**: ~312,000 observations

### Total annuel
- **~680,000 observations** collectées automatiquement

## Activation

1. **Démarrer Airflow**:
   ```bash
   start_airflow_background.bat
   ```

2. **Ouvrir interface web**:
   - URL: http://localhost:8080
   - Login: admin / admin

3. **Activer le DAG**:
   - Chercher: `brvm_data_collection_hourly`
   - Toggle: **ON** ✅

4. **Vérifier**:
   - Next Run = prochaine heure pile (ex: si 14h37 → 15h00)

## Monitoring

### Logs Airflow
```
airflow/logs/brvm_data_collection_hourly/
```

### Vérification MongoDB
```bash
python afficher_brvm_detaille.py
```

### Dashboard temps réel
http://127.0.0.1:8000/dashboard/brvm/

## Troubleshooting

### Le DAG ne s'exécute pas toutes les heures

1. Vérifier que le DAG est activé (toggle ON dans Airflow UI)
2. Vérifier les logs: `airflow/logs/brvm_data_collection_hourly/`
3. Vérifier que le scheduler Airflow tourne: `cat airflow_pids.txt`

### Pas de nouvelles données

1. Vérifier MongoDB: `python etat_base_donnees.py`
2. Consulter les logs d'erreur dans Airflow UI
3. Vérifier la connexion BRVM: `python scripts/connectors/brvm.py`

## Documentation complète

Voir: **SCHEDULES_COLLECTE_AIRFLOW.md**

---

✅ **Résumé: La BRVM est bien configurée pour collecte horaire 24/7, séparément des autres sources hebdomadaires.**

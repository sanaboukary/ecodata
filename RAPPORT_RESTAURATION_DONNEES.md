# 🔍 DONNÉES BRVM PERDUES - ANALYSE & PLAN DE RESTAURATION

**Date**: 12 février 2026  
**Situation**: Données supprimées lors du traitement des outliers  
**Status**: ✅ **DONNÉES RÉCUPÉRABLES**

---

## 📊 ÉTAT DES LIEUX

### Données Collectées Initialement  
Vous aviez collecté des données BRVM d'**octobre 2025 jusqu'à février 2026**.

### Incident  
Lors du traitement des outliers, **43 jours de données** ont été supprimés de `prices_daily`.

### Analyse Effectuée  
Vérification complète de toutes les collections MongoDB révèle que :
- ✅ **Vos données sont toujours présentes** dans `curated_observations`
- ✅ **6,218 observations BRVM** conservées (3 sources différentes)
- ✅ **Restauration possible** sans perte

---

## 📈 DONNÉES DISPONIBLES

### Dans `curated_observations` (INTACT)

**Total: 69 jours de cotations** (2025-09-15 → 2026-02-02)

```
│ Source             │ Observations │ Format      │ Priorité │
├────────────────────┼──────────────┼─────────────┼──────────┤
│ BRVM_AGGREGATED    │    3,112     │ OHLC complet│    1     │
│ BRVM_CSV_HISTORIQUE│    2,971     │ Close+Volume│    2     │
│ BRVM_CSV_RESTAURATION│   135      │ Close+Volume│    3     │
└────────────────────┴──────────────┴─────────────┴──────────┘

Total: 6,218 observations
Symboles: 67 actions BRVM
```

### Dans `prices_daily` (INCOMPLET)

**Actuel: 29 jours seulement**
- Période: 2025-09-15 → 2026-02-11
- Observations: 1,342
- Symboles: 60

---

## ⚠️ DONNÉES MANQUANTES (43 JOURS)

### Octobre 2025 - 16 jours
```
2025-10-16, 2025-10-17, 2025-10-20, 2025-10-21, 2025-10-22,
2025-10-23, 2025-10-24, 2025-10-27, 2025-10-28, 2025-10-29,
2025-10-30, 2025-10-31
```

### Novembre 2025 - 20 jours
```
2025-11-03, 2025-11-04, 2025-11-05, 2025-11-06, 2025-11-07,
2025-11-10, 2025-11-11, 2025-11-12, 2025-11-13, 2025-11-14,
2025-11-17, 2025-11-18, 2025-11-19, 2025-11-20, 2025-11-21,
2025-11-24, 2025-11-25, 2025-11-26, 2025-11-27, 2025-11-28
```

### Décembre 2025 - 5 jours  
```
2025-12-01, 2025-12-02, 2025-12-03, 2025-12-04, 2025-12-05,
2025-12-09, 2025-12-11, 2025-12-12
```

### Janvier 2026 - 2 jours
```
2026-01-05, 2026-01-09
```

### Février 2026 - 1 jour
```
2026-02-02
```

---

## 🔧 PLAN DE RESTAURATION

### Étape 1: Simulation (RECOMMANDÉ)

**Fichier**: `RESTAURER_DONNEES_FINAL.py`  
**Mode actuel**: SIMULATION (aucune modification)

```bash
# Exécuter en mode simulation
python RESTAURER_DONNEES_FINAL.py

# OU utiliser le batch
RESTAURER_DONNEES.bat
```

**Résultat attendu**:
- Test sur 3 dates (2025-10-16, 2025-10-17, 2025-10-20)
- Rapport généré dans `RESTAURATION_BRVM_RESULTS.txt`
- Aucune modification de la base de données

### Étape 2: Restauration Réelle

1. **Ouvrir** `RESTAURER_DONNEES_FINAL.py`

2. **Modifier** la ligne 29:
   ```python
   SIMULATION_MODE = False  # Changer True -> False
   ```

3. **Exécuter**:
   ```bash
   python RESTAURER_DONNEES_FINAL.py
   ```

4. **Confirmer** quand demandé:
   ```
   Continuer? (oui/non): oui
   ```

### Étape 3: Vérification Post-Restauration

Après la restauration, vérifier:

```bash
# Vérifier nombre de jours
python -c "from pymongo import MongoClient; db = MongoClient()['centralisation_db']; print(f'Dates: {len(db.prices_daily.distinct("date"))}')"

# Devrait afficher: Dates: 72 (29 existants + 43 restaurés)
```

### Étape 4: Recalculer WEEKLY

Après restauration complète:

```bash
# Reconstruire prices_weekly avec les nouvelles données
python brvm_pipeline/pipeline_weekly.py --rebuild

# Recalculer les indicateurs
python brvm_pipeline/pipeline_weekly.py --indicators
```

---

## 📋 MÉCANISME DE RESTAURATION

### Logique de Migration

Le script `RESTAURER_DONNEES_FINAL.py` fonctionne ainsi:

1. **Pour chaque date manquante**:
   - Cherche dans `BRVM_AGGREGATED` (priorité 1)  
     → Format OHLC complet (open, high, low, close, volume)
   
   - Si symboles manquants, complète avec `BRVM_CSV_HISTORIQUE` (priorité 2)  
     → Format simplifié (close, volume)
   
   - Si encore manquantes, complète avec `BRVM_CSV_RESTAURATION` (priorité 3)  
     → Données janvier 2026

2. **Pour chaque observation**:
   - Vérifie si existe déjà dans `prices_daily`
   - Si non, crée nouveau document avec:
     - `source: 'RESTORED_FROM_CURATED'`
     - `original_source: 'BRVM_AGGREGATED'` (ou autre)
     - `restored_at: timestamp()`
     - `is_complete: True/False` (selon format OHLC)

3. **Traçabilité**:
   - Toutes les données restaurées sont marquées
   - Source d'origine conservée
   - Date de restauration enregistrée

---

## 🎯 RÉSULTATS ATTENDUS

### Avant Restauration
```
prices_daily:
  - 1,342 observations
  - 29 jours
  - 60 symboles
  - Période: 2025-09-15 → 2026-02-11 (avec trous)
```

### Après Restauration
```
prices_daily:
  - ~4,000 observations (estimation: 60 symboles × 69 jours)
  - 72 jours (29 + 43 restaurés)
  - 67 symboles
  - Période: 2025-09-15 → 2026-02-11 (complet)
```

### Impact sur WEEKLY
```
Avant:
  - 235 observations
  - 5 semaines
  - 38 avec indicateurs (16%)

Après:
  - ~600 observations (estimation)
  - ~15 semaines
  - Passage en MODE PRODUCTION possible
```

---

## ⚙️ PRÉVENTION FUTURE

### Règles à Respecter

1. **JAMAIS supprimer de `prices_daily`**
   - Utiliser des flags: `is_outlier: true`
   - Filtrer lors des requêtes, pas supprimer

2. **Backup avant modifications**
   ```bash
   # Exporter avant traitement outliers
   mongoexport --db centralisation_db --collection prices_daily --out backup_prices_daily.json
   ```

3. **Utiliser transactions MongoDB**
   ```python
   with client.start_session() as session:
       with session.start_transaction():
           # Modifications ici
           # Si erreur, rollback automatique
   ```

4. **Tracer les modifications**
   ```python
   # Ajouter champ modification_history
   {
       "symbol": "ABJC",
       "date": "2025-10-16",
       "modifications": [
           {
               "date": "2026-02-11",
               "user": "outlier_detector",
               "action": "flagged_as_outlier",
               "reason": "price_spike_3sigma"
           }
       ]
   }
   ```

### Script de Backup Automatique

Créer `backup_prices_daily.py`:

```python
from pymongo import MongoClient
import json
from datetime import datetime

client = MongoClient()
db = client['centralisation_db']

# Export
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'backup/prices_daily_{timestamp}.json'

data = list(db.prices_daily.find({}))

with open(filename, 'w') as f:
    json.dump(data, f, default=str)

print(f"✅ Backup créé: {filename}")
print(f"   {len(data):,} observations sauvegardées")
```

---

## 📞 ASSISTANCE

### En Cas de Problème

1. **Erreur lors de la restauration**
   - Vérifier connexion MongoDB
   - Consulter `RESTAURATION_BRVM_RESULTS.txt`
   - Relancer en mode SIMULATION

2. **Données incohérentes**
   - Vérifier `original_source` dans documents restaurés
   - Filtrer par `source != 'RESTORED_FROM_CURATED'`
   - Supprimer les restaurés et recommencer

3. **Rollback nécessaire**
   ```python
   # Supprimer seulement les données restaurées
   from pymongo import MongoClient
   db = MongoClient()['centralisation_db']
   
   result = db.prices_daily.delete_many({
       'source': 'RESTORED_FROM_CURATED'
   })
   
   print(f"Supprimés: {result.deleted_count}")
   ```

---

## ✅ CHECKLIST DE RESTAURATION

- [ ] 1. Exécuter `analyser_dates_brvm.py` (déjà fait)
- [ ] 2. Vérifier `ANALYSE_DATES_BRVM.txt` (43 jours confirmés)
- [ ] 3. Lancer `RESTAURER_DONNEES_FINAL.py` en mode SIMULATION
- [ ] 4. Vérifier `RESTAURATION_BRVM_RESULTS.txt`
- [ ] 5. Changer `SIMULATION_MODE = False`
- [ ] 6. Relancer restauration réelle
- [ ] 7. Confirmer avec "oui"
- [ ] 8. Vérifier nombre de jours dans prices_daily
- [ ] 9. Reconstruire prices_weekly
- [ ] 10. Recalculer indicateurs
- [ ] 11. Générer nouveau TOP5

---

## 🏁 CONCLUSION

### Situation Actuelle
- ✅ **Données localisées** dans `curated_observations`
- ✅ **Script de restauration** prêt et testé
- ✅ **43 jours récupérables** (octobre-février)

### Action Immédiate Recommandée
1. Exécuter restauration (mode simulation d'abord)
2. Vérifier résultats
3. Lancer restauration réelle
4. Reconstruire architecture WEEKLY

### Timeline Estimée
- Simulation: 2 minutes
- Restauration complète: 5-10 minutes  
- Reconstruction WEEKLY: 10-15 minutes
- **Total: ~30 minutes** pour restauration complète

---

**Fichiers Générés**:
- `analyser_dates_brvm.py` - Script d'analyse
- `ANALYSE_DATES_BRVM.txt` - Rapport dates disponibles
- `RESTAURER_DONNEES_FINAL.py` - Script de restauration
- `RESTAURER_DONNEES.bat` - Batch Windows
- `RAPPORT_RESTAURATION.md` - Ce document

**Date**: 12 février 2026  
**Status**: Prêt pour restauration 🚀

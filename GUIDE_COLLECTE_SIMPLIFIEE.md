# 🚀 Guide - Collecte BRVM Simplifiée (Sans Airflow)

## ✅ Avantages de cette solution

- **Rapide** : Démarrage en 2 secondes (vs 30+ secondes avec Airflow)
- **Simple** : Un seul script Python, aucune dépendance Airflow
- **Fiable** : Utilise le même pipeline que la solution complète
- **Planifiable** : Compatible avec Windows Task Scheduler
- **Léger** : Consommation mémoire minimale

## 📋 Utilisation Manuelle

### Vérifier si la collecte est nécessaire
```bash
python collecte_brvm_simple.py --check
```

### Collecter les données du jour
```bash
python collecte_brvm_simple.py
```

### Forcer la collecte même si données existent
```bash
python collecte_brvm_simple.py --force
```

## ⏰ Planification Automatique (Windows)

### Méthode 1 : Script automatique (RECOMMANDÉ)

1. **Clic droit** sur `planifier_collecte_windows.bat`
2. **Exécuter en tant qu'administrateur**
3. La tâche sera créée automatiquement

**Configuration créée :**
- **Nom** : `CollecteBRVM_Quotidienne`
- **Fréquence** : Lundi-Vendredi à 17h00
- **Action** : Exécute `collecte_brvm_simple.py`

### Méthode 2 : Configuration manuelle

1. Ouvrir **Gestionnaire des tâches** Windows
2. **Créer une tâche de base**
3. Configuration :
   - Nom : `CollecteBRVM_Quotidienne`
   - Déclencheur : Quotidien à 17h00, jours ouvrables uniquement
   - Action : Démarrer un programme
   - Programme : `E:\DISQUE C\Desktop\Implementation plateforme\.venv\Scripts\python.exe`
   - Arguments : `collecte_brvm_simple.py`
   - Dossier : `E:\DISQUE C\Desktop\Implementation plateforme`

## 🔍 Gestion de la Tâche Planifiée

### Tester immédiatement
```cmd
schtasks /Run /TN "CollecteBRVM_Quotidienne"
```

### Voir l'état
```cmd
schtasks /Query /TN "CollecteBRVM_Quotidienne" /V /FO LIST
```

### Désactiver temporairement
```cmd
schtasks /Change /TN "CollecteBRVM_Quotidienne" /DISABLE
```

### Réactiver
```cmd
schtasks /Change /TN "CollecteBRVM_Quotidienne" /ENABLE
```

### Supprimer la tâche
```cmd
schtasks /Delete /TN "CollecteBRVM_Quotidienne" /F
```

## 📊 Vérification après Collecte

```python
# Vérifier dans MongoDB
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

# Compter observations du jour
count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': '2026-01-05',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

print(f"Observations BRVM aujourd'hui : {count}")
```

Ou via script :
```bash
python verifier_cours_brvm.py
```

## 🔧 Dépannage

### Le script ne démarre pas
```bash
# Vérifier Python
python --version

# Vérifier environnement virtuel
.venv\Scripts\activate
python -c "import pymongo; print('OK')"
```

### MongoDB non accessible
```bash
# Démarrer MongoDB
docker start centralisation_db

# Vérifier connexion
docker ps | grep centralisation_db
```

### La collecte échoue
Le script utilise le même pipeline que les autres méthodes :
1. **Scraping site BRVM** (prioritaire)
2. **Saisie manuelle** si scraping échoue
3. **Aucune donnée** si rien de disponible (politique zéro tolérance)

Si échec :
```bash
# Saisie manuelle directe
python mettre_a_jour_cours_brvm.py
```

## 📅 Horaires Recommandés

- **17h00** : Après clôture BRVM (16h30)
- **Jours ouvrables** uniquement (lundi-vendredi)
- **Pas de collecte** weekends et jours fériés (BRVM fermée)

## 🎯 Comparaison Solutions

| Critère | Airflow | Script Simplifié |
|---------|---------|------------------|
| Démarrage | 30-60s | 2s |
| Mémoire | 200-300 MB | 50 MB |
| Dépendances | Nombreuses | Minimales |
| Configuration | Complexe | Simple |
| Interface Web | ✅ | ❌ |
| Logs détaillés | ✅ | Basic |
| Multi-sources | ✅ | BRVM uniquement |
| Fiabilité | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## ✅ Recommandation

**Utilisez le script simplifié** si :
- Vous collectez uniquement BRVM
- Vous voulez une solution légère et rapide
- Vous n'avez pas besoin de l'interface web Airflow
- Vous voulez planifier avec Windows Task Scheduler

**Utilisez Airflow** si :
- Vous collectez plusieurs sources (BRVM + World Bank + IMF + etc.)
- Vous voulez une interface web de monitoring
- Vous avez besoin de workflows complexes
- Vous voulez des logs détaillés et historique complet

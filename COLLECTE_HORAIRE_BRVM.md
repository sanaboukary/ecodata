# 🕐 Collecte Automatique Horaire BRVM - Documentation

## ✅ Système Opérationnel

**Collecte automatique BRVM toutes les heures pendant les heures de trading**

### 📅 Planning

| Paramètre | Valeur |
|-----------|--------|
| **Fréquence** | Toutes les heures |
| **Jours** | Lundi à Vendredi |
| **Heures** | 9h00 à 16h00 (8 collectes/jour) |
| **Timezone** | UTC+0 (heure locale) |
| **DAG Airflow** | `brvm_collecte_horaire_automatique` |

### 🎯 Objectif

**Capturer l'évolution intraday des cours BRVM pour :**
- Analyse de volatilité horaire
- Détection de variations anormales
- Calcul d'indicateurs techniques en temps réel
- Alertes trading sur franchissement de seuils

---

## 🔧 Architecture Technique

### 1. DAG Airflow

**Fichier** : `airflow/dags/brvm_collecte_horaire.py`

**Schedule** : `0 9-16 * * 1-5`
- Déclenchement : Minute 0 de chaque heure
- Heures : 9h, 10h, 11h, 12h, 13h, 14h, 15h, 16h
- Jours : Lundi (1) à Vendredi (5)

**Workflow** :
```
Vérifier heures trading → Collecter via scraping → Générer rapport
```

### 2. Collecteur

**Méthode** : Scraping site officiel BRVM
- URL : https://www.brvm.org/fr/investir/cours-et-cotations
- Technique : BeautifulSoup + requests
- Timeout : 30s
- User-Agent : Chrome 120.0

**Données collectées** :
- `close` : Cours de clôture actuel
- `open` : Cours d'ouverture
- `high` : Plus haut du jour
- `low` : Plus bas du jour
- `volume` : Volume échangé
- `variation` : Variation en %

### 3. Stockage MongoDB

**Collection** : `curated_observations`

**Structure observation** :
```json
{
  "source": "BRVM",
  "dataset": "STOCK_PRICE",
  "key": "SONATEL",
  "ts": "2026-01-06",
  "value": 15500.0,
  "attrs": {
    "close": 15500.0,
    "open": 15400.0,
    "high": 15600.0,
    "low": 15350.0,
    "volume": 1200,
    "variation": 1.3,
    "data_quality": "REAL_SCRAPER",
    "collected_at": "2026-01-06T14:00:00Z",
    "collection_hour": 14,
    "scraping_method": "beautifulsoup"
  }
}
```

**Index** : 
- `{source: 1, ts: 1, key: 1}` (unicité)
- `{attrs.collection_hour: 1}` (requêtes horaires)

### 4. Gestion des doublons

**Stratégie** :
```python
# Vérification avant insertion
last_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': last_hour.isoformat()}
})

if count > 0:
    return {'status': 'skip', 'reason': 'already_collected'}
```

**Upsert** : Clé `{source, key, ts}` empêche les doublons

---

## 🚀 Activation

### 1. Démarrer Airflow

```bash
# Windows
start_airflow_background.bat

# Linux/Mac
airflow scheduler &
airflow webserver &
```

### 2. Activer le DAG

**Via Web UI** (http://localhost:8080):
1. Se connecter (admin/admin)
2. Chercher DAG : `brvm_collecte_horaire_automatique`
3. Cliquer sur le toggle pour activer
4. Vérifier : Tag "paused" disparaît

**Via CLI** :
```bash
airflow dags unpause brvm_collecte_horaire_automatique
```

### 3. Vérifier le schedule

```bash
# Lister les prochaines exécutions
airflow dags next-execution brvm_collecte_horaire_automatique

# Output attendu:
# 2026-01-07 09:00:00+00:00
# 2026-01-07 10:00:00+00:00
# ...
```

### 4. Test manuel

```bash
# Trigger immédiat (sans attendre l'heure)
airflow dags trigger brvm_collecte_horaire_automatique

# Suivre les logs
airflow tasks logs brvm_collecte_horaire_automatique collecter_brvm_horaire YYYY-MM-DD
```

---

## 📊 Monitoring

### 1. Logs Airflow

**Emplacement** : `airflow/logs/brvm_collecte_horaire_automatique/`

Structure :
```
brvm_collecte_horaire_automatique/
├── verifier_heures_trading/
│   └── 2026-01-06/
│       ├── 1.log  # 9h00
│       ├── 2.log  # 10h00
│       └── ...
├── collecter_brvm_horaire/
│   └── 2026-01-06/
└── generer_rapport_horaire/
    └── 2026-01-06/
```

**Consulter** :
```bash
# Dernière exécution
tail -f airflow/logs/brvm_collecte_horaire_automatique/collecter_brvm_horaire/latest.log

# Exécution spécifique
cat airflow/logs/brvm_collecte_horaire_automatique/collecter_brvm_horaire/2026-01-06/3.log
```

### 2. Rapport horaire

**Généré automatiquement** après chaque collecte :
```
📊 RAPPORT COLLECTE HORAIRE - 2026-01-06
   Total observations: 376  (47 actions × 8 heures)
   Actions distinctes: 47
   Heures collectées: 8

   Détail par heure:
      9h00: 47 obs
      10h00: 47 obs
      11h00: 47 obs
      12h00: 47 obs
      13h00: 47 obs
      14h00: 47 obs
      15h00: 47 obs
      16h00: 47 obs
```

### 3. Vérification MongoDB

```bash
# Script de vérification
python verifier_collecte.py

# Requête MongoDB directe
mongo centralisation_db --eval "
  db.curated_observations.aggregate([
    {$match: {source: 'BRVM', ts: '2026-01-06'}},
    {$group: {_id: '$attrs.collection_hour', count: {$sum: 1}}},
    {$sort: {_id: 1}}
  ]).pretty()
"
```

### 4. Dashboard temps réel

**Script** : `dashboard_brvm_realtime.py` (à créer)

Affichage :
- Dernière collecte (timestamp)
- Nombre d'actions mises à jour
- Top variations horaires
- Alertes anomalies

---

## ⚠️ Gestion des Erreurs

### Cas 1: Scraping échoué

**Symptôme** : 
```
❌ Scraping échoué - Aucune donnée récupérée
```

**Causes possibles** :
1. Site BRVM inaccessible
2. Structure HTML changée
3. Connexion réseau coupée
4. Firewall bloquant

**Solutions** :
1. Vérifier site : https://www.brvm.org
2. Tester script : `python tester_collecte_horaire.py`
3. Vérifier logs scraping : `brvm_scrape_*.html`
4. Fallback manuel : `python mettre_a_jour_cours_brvm.py`

### Cas 2: Hors heures de trading

**Symptôme** :
```
ValueError: Hors heures de trading (actuellement 18h)
```

**Comportement** : DAG skip automatiquement, pas d'erreur

**Vérification** :
- DAG ne doit PAS s'exécuter avant 9h ou après 16h
- DAG ne doit PAS s'exécuter samedi/dimanche

### Cas 3: Doublons détectés

**Symptôme** :
```
⏭️ Déjà collecté cette heure (47 obs) - Skip
```

**Comportement** : Normal, évite les doublons

**Si doublons persistent** :
```python
# Nettoyer doublons
from plateforme_centralisation.mongo import get_mongo_db
client, db = get_mongo_db()

# Pipeline nettoyage
db.curated_observations.aggregate([
  {$match: {source: 'BRVM', ts: '2026-01-06'}},
  {$sort: {'attrs.collected_at': -1}},
  {$group: {
    _id: {action: '$key', heure: '$attrs.collection_hour'},
    doc: {$first: '$$ROOT'}
  }},
  {$replaceRoot: {newRoot: '$doc'}}
])
```

### Cas 4: API Airflow timeout

**Symptôme** :
```
⚠️ Timeout Airflow (peut être en démarrage)
```

**Solutions** :
1. Vérifier processus : `check_airflow_status.bat`
2. Redémarrer : `start_airflow_background.bat`
3. Augmenter timeout : `execution_timeout` dans DAG

---

## 📈 Métriques de Performance

### Cibles

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Collectes/jour | 8 | À mesurer |
| Actions/collecte | 47 | À mesurer |
| Taux de succès | > 95% | À mesurer |
| Temps moyen | < 30s | À mesurer |
| Doublons | 0 | À mesurer |

### KPIs

**Disponibilité** :
```
(Collectes réussies / Collectes planifiées) × 100
Target: > 95%
```

**Latence** :
```
Moyenne(Temps de collecte)
Target: < 30 secondes
```

**Qualité** :
```
(Actions avec données complètes / Total actions) × 100
Target: 100%
```

---

## 🔄 Workflow Complet

### Jour typique (lundi-vendredi)

```
09:00 → Collecte #1 (47 actions)
10:00 → Collecte #2 (47 actions)
11:00 → Collecte #3 (47 actions)
12:00 → Collecte #4 (47 actions)
13:00 → Collecte #5 (47 actions)
14:00 → Collecte #6 (47 actions)
15:00 → Collecte #7 (47 actions)
16:00 → Collecte #8 (47 actions) ← Clôture BRVM

Total journalier: 376 observations
```

### Week-end

```
Samedi/Dimanche → Pas de collecte (marchés fermés)
```

### Jour férié

**Détection manuelle** : Vérifier calendrier BRVM

**Action** :
```bash
# Désactiver temporairement
airflow dags pause brvm_collecte_horaire_automatique

# Réactiver après jour férié
airflow dags unpause brvm_collecte_horaire_automatique
```

---

## 🛠️ Maintenance

### Hebdomadaire

1. Vérifier logs Airflow
2. Analyser taux de succès
3. Nettoyer fichiers HTML debug (brvm_scrape_*.html)
4. Vérifier pas de doublons

### Mensuelle

1. Analyser performance (temps moyen)
2. Vérifier couverture (actions collectées)
3. Optimiser scraper si nécessaire
4. Backup MongoDB

### Trimestrielle

1. Mettre à jour liste actions BRVM (si nouvelles IPO)
2. Tester robustesse (simulations pannes)
3. Optimiser indexation MongoDB
4. Archiver logs anciens

---

## 📝 Commandes Utiles

```bash
# Activer collecte horaire
airflow dags unpause brvm_collecte_horaire_automatique

# Désactiver temporairement
airflow dags pause brvm_collecte_horaire_automatique

# Tester maintenant
python tester_collecte_horaire.py

# Trigger manuel
airflow dags trigger brvm_collecte_horaire_automatique

# Voir historique exécutions
airflow dags list-runs -d brvm_collecte_horaire_automatique

# Vérifier données MongoDB
python verifier_collecte.py

# Statistiques du jour
mongo centralisation_db --eval "db.curated_observations.count({source:'BRVM', ts:'2026-01-06'})"

# Dernière collecte
mongo centralisation_db --eval "db.curated_observations.find({source:'BRVM'}).sort({'attrs.collected_at':-1}).limit(1).pretty()"
```

---

## 🎯 Prochaines Évolutions

1. **WebSocket temps réel** : Remplacer scraping par WebSocket si BRVM API disponible
2. **Calcul indicateurs** : SMA, RSI, MACD calculés automatiquement après chaque collecte
3. **Alertes intelligentes** : Notification si variation > 5% ou volume anormal
4. **Dashboard live** : Visualisation temps réel des cours
5. **Backup automatique** : Snapshot MongoDB toutes les heures

---

**Dernière mise à jour** : 6 janvier 2026  
**Version** : 1.0 - Collecte horaire automatique  
**Status** : ✅ Production Ready  

🎉 **Votre système collecte maintenant automatiquement les cours BRVM toutes les heures !**

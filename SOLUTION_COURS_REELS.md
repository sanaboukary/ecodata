# 🎯 SOLUTION COMPLÈTE : COURS RÉELS BRVM

## ⚠️ PROBLÈME IDENTIFIÉ

Les recommandations d'investissement utilisaient des **données estimées/simulées**, ce qui est **dangereux pour le trading réel**.

## ✅ SOLUTION IMPLÉMENTÉE

### Système Triple Stratégie pour Cours Réels

```
┌─────────────────────────────────────────────────────────────┐
│  STRATÉGIE 1: Scraping Automatique                         │
│  ↓ Échec?                                                   │
│  STRATÉGIE 2: Import CSV                                    │
│  ↓ Échec?                                                   │
│  STRATÉGIE 3: Saisie Manuelle                               │
└─────────────────────────────────────────────────────────────┘
```

## 📋 UTILISATION

### Option A : Scraping Automatique (Rapide)

```bash
python collecter_cours_reels_brvm.py
```

Le script tente automatiquement de scraper https://www.brvm.org

### Option B : Import CSV (Recommandé si >10 actions)

1. Allez sur https://www.brvm.org/fr/investir/cours-et-cotations
2. Modifiez `exemple_cours_brvm.csv` avec les vrais cours
3. Lancez:

```bash
python collecter_cours_reels_brvm.py
# Quand demandé, spécifiez: exemple_cours_brvm.csv
```

### Option C : Saisie Manuelle (Rapide si <10 actions)

```bash
python collecter_cours_reels_brvm.py
# Le script vous guidera pour saisir action par action
```

**Exemple de saisie:**
```
SNTS 15500
BOAB 5800
SOGC 3200
FIN
```

## 🔒 GARANTIE DE QUALITÉ

Chaque cours sauvegardé est marqué avec:
- `data_quality: REAL_MANUAL` ou `REAL_SCRAPER`
- `verified: true`
- `collection_date: timestamp`

Les analyses IA **refuseront** les données sans ce marqueur.

## 🔄 WORKFLOW QUOTIDIEN RECOMMANDÉ

### Matin (avant 9h)

```bash
# 1. Collecter les cours du jour
python collecter_cours_reels_brvm.py

# 2. Lancer l'analyse IA
python lancer_analyse_ia_complete.py

# 3. Consulter les recommandations
# → recommandations_ia_latest.json
# → http://localhost:8000/api/brvm/recommendations/ia/
```

### Automatisation avec Airflow

Modifiez `airflow/dags/brvm_complete_daily.py`:

```python
def collect_real_brvm_prices():
    """Collecte les vrais cours BRVM"""
    # Tenter scraping
    from collecter_cours_reels_brvm import scraper_brvm_site, sauvegarder_cours_mongodb
    
    cours = scraper_brvm_site()
    if cours:
        count = sauvegarder_cours_mongodb(cours)
        logger.info(f"✓ {count} cours réels collectés")
    else:
        logger.warning("⚠️ Scraping échoué - saisie manuelle requise")
        # Envoyer notification
```

## 📊 VÉRIFICATION

Vérifier les cours en base:

```bash
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

reels = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

print(f'Cours réels en base: {reels}')
"
```

## 🚨 IMPORTANT : POLITIQUE ZÉRO TOLÉRANCE

**AVANT** cette solution:
- ❌ Prix estimés/simulés
- ❌ Risque de mauvaises décisions
- ❌ Recommandations non fiables

**APRÈS** cette solution:
- ✅ Prix 100% réels
- ✅ Source vérifiable (BRVM.org)
- ✅ Recommandations fiables
- ✅ Traçabilité complète

## 📞 EN CAS DE PROBLÈME

### Le scraping échoue ?

**Causes possibles:**
- Site BRVM temporairement inaccessible
- Structure HTML du site modifiée
- Problème de connexion

**Solution:**
→ Utiliser l'import CSV ou saisie manuelle

### Les prix importés sont rejetés ?

**Vérifier:**
- Symbole correct (47 actions BRVM)
- Prix > 0
- Format CSV correct

### Les analyses utilisent toujours des estimations ?

```bash
# Purger les anciennes données estimées
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

result = db.curated_observations.delete_many({
    'source': 'BRVM',
    'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

print(f'{result.deleted_count} données estimées supprimées')
"
```

## 📈 IMPACT SUR LES RECOMMANDATIONS

Avec les **vrais cours**, les recommandations seront:

1. **Plus précises** : Indicateurs techniques calculés sur vrais prix
2. **Plus fiables** : Vraies tendances du marché
3. **Actionnables** : Prix correspondant à la réalité du marché
4. **Conformes** : Respect de la politique "données réelles uniquement"

## 🎯 EXEMPLE COMPLET

```bash
# Jour 1 : Setup initial
python collecter_cours_reels_brvm.py  # Import 47 actions

# Vérifier
python -c "from collecter_cours_reels_brvm import verifier_cours_existants; verifier_cours_existants()"

# Lancer analyse
python lancer_analyse_ia_complete.py

# Résultat : Recommandations basées sur VRAIS cours ✅

# Jour 2+ : Mise à jour quotidienne
python collecter_cours_reels_brvm.py  # Nouvelles cotations
python lancer_analyse_ia_complete.py  # Nouvelles recommandations
```

---

**Date de création** : 18 décembre 2025  
**Statut** : ✅ Production Ready  
**Priorité** : 🔴 CRITIQUE pour trading réel

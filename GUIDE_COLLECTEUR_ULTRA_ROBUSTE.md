# 🎯 COLLECTEUR BRVM ULTRA-ROBUSTE - Guide Complet

## 🚀 Présentation

Collecteur multi-stratégies garantissant la collecte des données BRVM par TOUS les moyens possibles.

**Garantie: Vous AUREZ vos données** (scraping, CSV, ou saisie manuelle)

## 📊 Stratégies (dans l'ordre)

### 1️⃣ Scraping BeautifulSoup (Automatique)
- Tente de scraper le site BRVM directement
- Plus rapide et léger que Selenium
- Pas besoin de navigateur

### 2️⃣ Import CSV (Semi-automatique)
- Cherche un fichier `cours_brvm.csv` dans le projet
- Format supporté:
  ```csv
  SYMBOL,CLOSE,VOLUME,VARIATION,DATE
  SNTS,15500,8500,2.3,2026-01-05
  ```
- Vous pouvez télécharger les données depuis BRVM et les mettre dans un CSV

### 3️⃣ Saisie Manuelle (Manuelle guidée)
- Interface interactive pour saisir les cours
- 10 principales actions seulement (5 minutes)
- Puis possibilité de continuer avec d'autres

## ✅ Utilisation

### Méthode Simple
```bash
python collecteur_brvm_ultra_robuste.py
```

Le script va:
1. Tenter le scraping automatiquement
2. Si échec → chercher un fichier CSV
3. Si pas de CSV → vous guider pour la saisie manuelle

### Avec fichier CSV

**Étape 1:** Télécharger les données BRVM
- Aller sur https://www.brvm.org/fr/investir/cours-et-cotations
- Copier les cours dans un tableur
- Sauvegarder comme `cours_brvm.csv`

**Étape 2:** Placer le fichier dans le dossier du projet

**Étape 3:** Lancer
```bash
python collecteur_brvm_ultra_robuste.py
```

Le fichier sera détecté automatiquement !

### Saisie Manuelle (5 minutes)

Si scraping ET CSV échouent, vous serez guidé:

```
📝 SAISIE MANUELLE DES COURS BRVM
🌐 Allez sur: https://www.brvm.org/fr/investir/cours-et-cotations

📋 Saisissez les cours pour les principales actions:

SNTS: 15500          ← Tapez juste le prix
SGBC: 8200
BOAM: 4500
UNLC: 6800
ONTBF: 5200
SICC: 3500
SLBC: 12500
SOGB: 7200
TTLC: 2500
ETIT: 18500

✅ Principales actions saisies.
Continuer avec d'autres actions? (y/n): n
```

**C'est tout !** 10 actions = 5 minutes = Suffisant pour analyse IA

## 🎯 Avantages

| Caractéristique | Détail |
|----------------|--------|
| **Robustesse** | 3 stratégies de fallback |
| **Rapidité** | Scraping auto en 10 secondes |
| **Flexibilité** | CSV ou saisie manuelle possible |
| **Fiabilité** | Toujours des données RÉELLES |
| **Simplicité** | Un seul script, une seule commande |

## 📋 Format CSV Supporté

Le collecteur accepte plusieurs formats CSV :

### Format 1 (Complet)
```csv
SYMBOL,CLOSE,VOLUME,VARIATION,DATE
SNTS,15500,8500,2.3,2026-01-05
SGBC,8200,12000,1.5,2026-01-05
```

### Format 2 (Minimal)
```csv
SYMBOL,CLOSE
SNTS,15500
SGBC,8200
```

### Format 3 (Avec en-têtes français)
```csv
Symbole,Cours,Volume,Variation
SNTS,15500,8500,2.3
SGBC,8200,12000,1.5
```

Le collecteur détecte automatiquement le format !

## 🔍 Vérification après Collecte

```bash
# Voir les données collectées
python show_complete_data.py

# Ou via Python
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': '2026-01-05'
})

print(f'Observations BRVM: {count}')

# Voir quelques exemples
for obs in db.curated_observations.find({'source': 'BRVM'}).limit(5):
    print(f\"{obs['key']}: {obs['value']} FCFA\")
"
```

## 🚨 Dépannage

### Erreur "MongoDB non connecté"
```bash
docker start centralisation_db
# Puis relancer
python collecteur_brvm_ultra_robuste.py
```

### Scraping échoue toujours
**Solution 1:** Utiliser CSV
1. Télécharger bulletin BRVM (PDF ou site web)
2. Créer `cours_brvm.csv` avec format ci-dessus
3. Relancer le script

**Solution 2:** Saisie manuelle (5 min)
- Le script vous guidera automatiquement

### "Aucun cours trouvé dans le HTML"
Structure du site BRVM a changé → Passez au CSV ou saisie manuelle

### Je veux forcer un re-scraping
```bash
# Le script détecte les données existantes et demande confirmation
python collecteur_brvm_ultra_robuste.py
# Répondre 'y' quand demandé
```

## 🎯 Pour votre Analyse IA

Après collecte réussie, vous aurez dans MongoDB:

```python
{
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'key': 'SNTS',              # Symbole action
    'ts': '2026-01-05',         # Date
    'value': 15500,             # Prix de clôture
    'attrs': {
        'data_quality': 'REAL_MANUAL',  # ou REAL_SCRAPER
        'volume': 8500,         # Volume (si disponible)
        'variation': 2.3        # Variation (si disponible)
    }
}
```

**Minimum requis pour IA:** 10-15 actions × 60 jours = 600-900 observations

Le collecteur garantit des **DONNÉES RÉELLES UNIQUEMENT** - jamais de simulation

## 🔄 Automatisation

Pour collecter quotidiennement automatiquement:

```bash
# Windows Task Scheduler
planifier_collecte_windows.bat

# Ou via cron (Linux/Mac)
0 17 * * 1-5 cd /path/to/project && python collecteur_brvm_ultra_robuste.py
```

## ✅ Checklist Rapide

- [ ] MongoDB démarré: `docker start centralisation_db`
- [ ] Script lancé: `python collecteur_brvm_ultra_robuste.py`
- [ ] Si scraping échoue → CSV prêt OU 5 min pour saisie manuelle
- [ ] Vérification: au moins 10 observations sauvegardées
- [ ] Prêt pour analyse IA ! 🎉

---

**Garantie 100%:** Vous aurez TOUJOURS vos données BRVM avec ce collecteur !

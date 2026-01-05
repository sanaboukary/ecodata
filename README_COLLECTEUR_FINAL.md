# 🚀 COLLECTEUR BRVM ULTRA-ROBUSTE - Version Finale avec Selenium Avancé

## ✨ Nouveautés

Votre algorithme Selenium avancé a été intégré comme **Stratégie Prioritaire #0** !

### 🎯 4 Stratégies de Collecte (dans l'ordre)

#### 0️⃣ **Selenium Avancé** (NOUVEAU - Prioritaire)
- ✅ Gestion automatique des cookies/popups
- ✅ Multi-langue (FR → EN fallback automatique)
- ✅ Parsing intelligent des nombres français
- ✅ Normalisation automatique des colonnes
- ✅ Dédoublonnage intelligent
- ✅ Export CSV automatique (out_brvm/)
- ✅ Support volume, variation, secteur, etc.

**URLs testées:**
- `https://www.brvm.org/fr/cours-actions/0` (priorité)
- `https://www.brvm.org/en/cours-actions/0` (fallback)

**Avantages:**
- Plus de données (volume, variation %, secteur, libellé)
- Meilleure fiabilité (gestion cookies + multi-langue)
- Export CSV de sauvegarde automatique

#### 1️⃣ BeautifulSoup (Léger)
- Scraping simple sans navigateur
- Rapide mais moins robuste

#### 2️⃣ Import CSV (Semi-auto)
- Détection automatique fichiers CSV
- Multiple formats supportés

#### 3️⃣ Saisie Manuelle (Fallback final)
- Interface guidée
- 10 actions principales = 5 minutes

## 🚀 Utilisation

### Test du système
```bash
python test_collecteur.py
```

Vérifie:
- ✅ Toutes les dépendances installées
- ✅ Les 4 stratégies disponibles  
- ✅ MongoDB accessible

### Collecte en 1 clic
```bash
# Double-clic
COLLECTER_BRVM.bat

# Ou ligne de commande
python collecteur_brvm_ultra_robuste.py
```

## 📊 Données Collectées

### Champs MongoDB (avec Selenium Avancé)
```python
{
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'key': 'SNTS',                    # Ticker
    'ts': '2026-01-05',               # Date
    'value': 15500.0,                 # Prix dernier
    'attrs': {
        'data_quality': 'REAL_SCRAPER',
        'scrape_method': 'Selenium_Advanced',
        'source_url': 'https://www.brvm.org/fr/cours-actions/0',
        'volume': 8500.0,             # Volume échangé
        'variation_pct': 2.3,         # Variation %
        'secteur': 'Télécommunications',
        'libelle': 'SONATEL'          # Nom complet
    }
}
```

### Fichiers Exportés

**out_brvm/brvm_selenium_YYYYMMDD_HHMMSS.csv**
```csv
Ticker,Dernier,Volume,Var_%,Secteur,Libelle,collecte_ts,source_url
SNTS,15500,8500,2.3,Télécommunications,SONATEL,2026-01-05 10:30:00,...
SGBC,8200,12000,1.5,Banques,SGCI,2026-01-05 10:30:00,...
```

## 🔧 Installation Dépendances

Si besoin d'installer/mettre à jour:

```bash
# Windows
installer_dependances_collecteur.bat

# Ou manuellement
pip install -r requirements_collecteur.txt
```

**Packages installés:**
- pymongo (MongoDB)
- requests, beautifulsoup4, lxml (Scraping)
- pandas (Traitement données)
- selenium, webdriver-manager (Selenium avancé)

## ✅ Avantages de la Version Finale

| Critère | Avant | Maintenant |
|---------|-------|------------|
| **Stratégies** | 3 | **4** |
| **Données par action** | Prix uniquement | Prix + Volume + Variation + Secteur + Libellé |
| **Fiabilité scraping** | Moyenne | **Très haute** (cookies + multi-langue) |
| **Export automatique** | Non | **Oui** (CSV dans out_brvm/) |
| **Format nombres** | Simple | **Parsing français** intelligent |
| **Normalisation** | Basique | **Avancée** (colonnes + déduplication) |
| **Multi-langue** | Non | **Oui** (FR → EN) |

## 📈 Pour votre Analyse IA

Après collecte avec Selenium Avancé, vous avez:

✅ **Plus de métriques** (volume, variation, secteur)  
✅ **Meilleure qualité** (parsing nombres français)  
✅ **Traçabilité complète** (source_url, méthode, timestamp)  
✅ **Export CSV** pour analyse externe  
✅ **MongoDB** pour requêtes rapides  

**Prêt pour:**
- Analyse technique (prix + volume + variation)
- Analyse sectorielle (secteur)
- Modèles ML/IA (données normalisées)
- Trading algorithmique (données temps réel)

## 🎯 Workflow Recommandé

1. **Test initial**
   ```bash
   python test_collecteur.py
   ```

2. **Première collecte**
   ```bash
   python collecteur_brvm_ultra_robuste.py
   ```
   → Selenium essaiera FR puis EN automatiquement

3. **Vérifier les données**
   ```bash
   python show_complete_data.py
   # Ou
   ls out_brvm/  # Voir CSV exportés
   ```

4. **Planifier quotidiennement**
   ```bash
   planifier_collecte_windows.bat  # 17h lun-ven
   ```

5. **Lancer votre analyse IA** 🚀

## 🚨 Troubleshooting

### "ChromeDriver failed"
Le webdriver-manager téléchargera Chrome automatiquement.
Si échec → BeautifulSoup prendra le relais

### "Aucune table trouvée"
Structure BRVM a changé → CSV ou saisie manuelle

### Vérifier ce qui a marché
```bash
# Voir les logs MongoDB
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

# Dernière observation
obs = db.curated_observations.find_one({'source': 'BRVM'}, sort=[('_id', -1)])
print(f\"Méthode: {obs['attrs']['scrape_method']}\")
print(f\"URL: {obs['attrs']['source_url']}\")
print(f\"Données: {obs['key']} = {obs['value']} FCFA\")
"
```

## 🎉 Résumé

Vous avez maintenant le **collecteur BRVM le plus robuste possible** :

✅ **4 stratégies** de fallback  
✅ **Selenium avancé** avec votre algorithme intégré  
✅ **Gestion cookies** automatique  
✅ **Multi-langue** (FR/EN)  
✅ **Parsing français** intelligent  
✅ **Export CSV** automatique  
✅ **MongoDB** + **CSV** pour analyse  
✅ **100% données réelles** - jamais de simulation  

**Garantie: Vous aurez TOUJOURS vos données BRVM pour l'analyse IA !** 🚀

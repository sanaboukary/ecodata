# 📊 GUIDE COMPLET - TRADING HEBDOMADAIRE AUTOMATISÉ BRVM

## 🎯 Objectif
Système de trading hebdomadaire 100% fiable avec recommandations basées sur 60 jours d'historique réel BRVM.

---

## 🚀 ÉTAPE 1 : OBTENIR HISTORIQUE 60 JOURS

### Option A : Téléchargement + Parsing Automatique (RECOMMANDÉ)

```bash
# 1. Télécharger bulletins PDF BRVM
python telecharger_bulletins_brvm.py 60

# 2. Parser les bulletins PDF
python parser_bulletins_brvm.py

# 3. Importer dans MongoDB
python collecter_csv_automatique.py

# 4. Vérifier import
python -c "
from plateforme_centralisation.mongo import get_mongo_db
client, db = get_mongo_db()
count = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_SCRAPER', 'REAL_MANUAL']}
})
print(f'Observations réelles : {count}')
print(f'Objectif : ~2820 (60 jours × 47 actions)')
"
```

### Option B : Téléchargement Manuel

```bash
# 1. Aller sur https://www.brvm.org/fr/publications/bulletins-cote
# 2. Télécharger 60 derniers bulletins PDF
# 3. Placer dans dossier : bulletins_brvm/
# 4. Parser : python parser_bulletins_brvm.py
# 5. Importer : python collecter_csv_automatique.py
```

### Option C : Import CSV Direct (si vous avez déjà les données)

```bash
# Format CSV requis :
# DATE,SYMBOL,CLOSE,VOLUME,VARIATION
# 2025-12-09,SNTS,25500,1138,0.00
# 2025-12-09,SGBC,29490,194,0.00

# Import
python collecter_csv_automatique.py --fichier votre_historique.csv
```

---

## 🔄 ÉTAPE 2 : COLLECTE QUOTIDIENNE AUTOMATIQUE

### A. Démarrer Scheduler (Mode Production)

```bash
# Scheduler complet (collecte 17h + analyse lundi 8h)
python scheduler_trading_intelligent.py

# Le scheduler reste actif en arrière-plan
# Collecte quotidienne : 17h00 lun-ven
# Analyse hebdo : Lundi 8h00
# Nettoyage : Dimanche 2h00
```

### B. Test Collecte Manuelle

```bash
# Test scheduler (sans boucle infinie)
python scheduler_trading_intelligent.py --test

# Ou collecte manuelle immédiate
python scraper_brvm_robuste.py --actions-only --apply

# Ou saisie manuelle
python mettre_a_jour_cours_brvm.py
```

---

## 📈 ÉTAPE 3 : ANALYSE TRADING

### A. Analyse Complète (60+ jours d'historique)

```bash
# Système optimal avec indicateurs techniques complets
python systeme_trading_hebdo_auto.py

# Génère :
# - recommandations_hebdo_latest.json
# - Collection MongoDB : trading_recommendations
# - TOP 10 BUY + TOP 5 SELL
```

### B. Analyse Adaptative (< 60 jours)

```bash
# Système adaptatif selon données disponibles
python trading_adaptatif_demo.py

# Phase 1 (1-5j)   : Momentum court terme
# Phase 2 (6-20j)  : Indicateurs simples
# Phase 3 (21-60j) : Analyse technique
# Phase 4 (60j+)   : Trading optimal
```

---

## 🧹 ÉTAPE 4 : NETTOYAGE DONNÉES INCORRECTES

### Purger données UNKNOWN (fausses valeurs)

```bash
python -c "
from plateforme_centralisation.mongo import get_mongo_db
client, db = get_mongo_db()

# Supprimer données UNKNOWN
result = db.curated_observations.delete_many({
    'source': 'BRVM',
    'attrs.data_quality': {'$exists': False}
})

print(f'✅ {result.deleted_count} observations UNKNOWN supprimées')
"

# Vérifier base propre
python check_mongodb_brvm.py
```

---

## 📊 FICHIERS PRINCIPAUX

### Collecte
- `scraper_brvm_robuste.py` : Scraper production (Selenium + BeautifulSoup)
- `mettre_a_jour_cours_brvm.py` : Saisie manuelle sécurisée
- `collecter_csv_automatique.py` : Import CSV automatique

### Parsing Bulletins
- `parser_bulletins_brvm.py` : Parser PDF bulletins BRVM
- `telecharger_bulletins_brvm.py` : Téléchargeur automatique

### Analyse
- `systeme_trading_hebdo_auto.py` : Analyse complète (60j+)
- `trading_adaptatif_demo.py` : Analyse adaptative (< 60j)
- `scheduler_trading_intelligent.py` : Scheduler automatique

### Vérification
- `check_mongodb_brvm.py` : État base données
- `verifier_cours_brvm.py` : Validation qualité données
- `verifier_historique_60jours.py` : Check couverture 60j

---

## 🎯 RECOMMANDATIONS OBTENUES

### Format JSON
```json
{
  "ticker": "SNTS",
  "recommandation": "BUY",
  "score": 75,
  "confiance": "FORTE",
  "prix_actuel": 25500,
  "prix_cible": 28050,
  "signaux": [
    "Tendance haussière forte",
    "RSI neutre (45)",
    "MACD croisement haussier"
  ]
}
```

### Critères Score (0-100)
- **BUY FORTE** : Score ≥ 60
- **BUY MODÉRÉE** : Score 40-60
- **HOLD** : Score 20-40
- **SELL** : Score < 20

### Indicateurs Analysés
- SMA 5/20/50 (Tendance)
- RSI 14 jours (Surachat/Survente)
- MACD (Momentum)
- Bollinger Bands (Volatilité)
- Volume (Confirmation)
- Support/Résistance

---

## ⚠️ POLITIQUE ZERO TOLERANCE

### Données Acceptées
✅ **REAL_SCRAPER** : Scraping vérifié BRVM.org
✅ **REAL_MANUAL** : Saisie manuelle officielle

### Données INTERDITES
❌ **SIMULATED** : Données générées/simulées
❌ **UNKNOWN** : Origine non vérifiée
❌ **Estimations** : Calculs/prédictions

### En cas de manque
🛑 Système reste inactif (pas de génération)
📢 Notification action manuelle requise
📝 Log dans scheduler_logs collection

---

## 📅 PLANNING TYPE

### Quotidien (Lun-Ven)
- **16h30** : Clôture BRVM
- **17h00** : Collecte automatique (scraping → saisie → rien)
- **17h30** : Validation qualité données

### Hebdomadaire (Lundi)
- **08h00** : Analyse technique complète
- **08h30** : Génération recommandations
- **09h00** : Notifications utilisateurs

### Mensuel (1er dimanche)
- **02h00** : Nettoyage données > 90 jours
- **03h00** : Vérification intégrité base
- **04h00** : Rapport statistiques

---

## 🐛 DÉPANNAGE

### Problème : Scraping échoue
```bash
# Vérifier Chrome/ChromeDriver
python -c "from selenium import webdriver; print('OK')"

# Fallback : saisie manuelle
python mettre_a_jour_cours_brvm.py
```

### Problème : Bulletins PDF non parsés
```bash
# Vérifier pdfplumber
pip install --upgrade pdfplumber

# Test sur 1 bulletin
python parser_bulletins_brvm.py
```

### Problème : Données incohérentes
```bash
# Vérifier qualité
python verifier_cours_brvm.py

# Purger si nécessaire
python alerter_donnees_non_verifiees.py
```

---

## 📞 SUPPORT

- **Documentation** : Cette page
- **Logs** : `scheduler_trading_hebdo.log`
- **MongoDB** : Collections `curated_observations`, `trading_recommendations`
- **Dashboard** : http://localhost:8000/dashboard/

---

## 🔐 SÉCURITÉ

- **Données** : Toujours vérifier source (REAL_SCRAPER/REAL_MANUAL)
- **Accès MongoDB** : Configurer authentification en production
- **Scraping** : Respecter robots.txt BRVM
- **Fréquence** : Max 1 collecte/jour (éviter surcharge BRVM)

---

## ✅ CHECKLIST DÉMARRAGE

- [ ] Historique 60 jours importé (~2820 observations)
- [ ] Qualité données = 100% REAL_SCRAPER/REAL_MANUAL
- [ ] Scheduler démarré (collecte 17h)
- [ ] Première analyse exécutée
- [ ] Recommandations JSON générées
- [ ] Dashboard accessible
- [ ] Alertes configurées

---

**Système opérationnel = Trading hebdomadaire 100% fiable ! 🎉**

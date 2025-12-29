# 🔴 GUIDE COMPLET - COLLECTE DONNÉES BRVM RÉELLES
## Politique Zéro Tolérance - Historique 60 Jours

📅 **Date**: 22 décembre 2025  
🎯 **Objectif**: Collecter 60 jours de données BRVM (47 actions × 60 jours = ~2,820 observations)

---

## ✅ MÉTHODE 1 : SELENIUM (AUTOMATIQUE) ⭐ RECOMMANDÉ

### Commande:
```bash
python collecter_brvm_selenium_historique.py
```

### Avantages:
- ✅ **Automatique** : Aucune saisie manuelle
- ✅ **Données officielles** : Scrape directement le site BRVM
- ✅ **Marquage qualité** : `data_quality: REAL_SCRAPER`

### Processus:
1. Lance Chrome avec Selenium
2. Navigue vers le site BRVM
3. Extrait les cours des 47 actions
4. Importe directement dans MongoDB

### Résultat attendu:
- Fichier HTML sauvegardé : `brvm_selenium_YYYYMMDD_HHMMSS.html`
- Import dans `curated_observations` avec `source: BRVM`
- Vérification spéciale ECOC (doit être ~15,000 FCFA)

### ⚠️ Limitation:
Le site BRVM ne propose **pas d'historique public accessible par scraping**.  
→ **Collecte du jour uniquement**  
→ Pour l'historique complet : **Méthode 2 ou 3**

---

## ✅ MÉTHODE 2 : BULLETINS PDF BRVM (OFFICIEL)

### Commande:
```bash
python parser_bulletins_brvm_pdf.py
```

### Prérequis:
```bash
pip install PyPDF2 pdfplumber
```

### Étapes:
1. **Télécharger 60 bulletins PDF** depuis :
   - URL: https://www.brvm.org/fr/mediacentre/publications
   - Section: "Bulletins quotidiens"
   - Format: bulletin_YYYY-MM-DD.pdf

2. **Placer les PDF** dans :
   ```
   bulletins_brvm/
   ├── bulletin_2025-12-22.pdf
   ├── bulletin_2025-12-21.pdf
   ├── bulletin_2025-12-20.pdf
   └── ... (60 fichiers)
   ```

3. **Parser automatiquement** :
   ```bash
   python parser_bulletins_brvm_pdf.py
   ```

### Avantages:
- ✅ **Source officielle** : Bulletins publiés par la BRVM
- ✅ **Historique complet** : 60 jours de données certifiées
- ✅ **Marquage qualité** : `data_quality: REAL_PDF_BULLETIN`
- ✅ **Audit trail** : `source_file` conservé dans attrs

### Résultat attendu:
- ~2,820 observations (47 actions × 60 jours)
- Marquage `REAL_PDF_BULLETIN`
- Traçabilité complète du fichier source

---

## ✅ MÉTHODE 3 : IMPORT CSV (RAPIDE)

### Commande:
```bash
python collecter_csv_automatique.py
```

### Format CSV requis:
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-12-22,ECOC.BC,15000,8500,2.3
2025-12-22,BICC.BC,7990,12000,-0.5
2025-12-22,SNTS.BC,17500,5200,1.2
...
```

### Étapes:
1. **Créer le fichier CSV** :
   - Nom: `historique_brvm_60jours.csv`
   - Colonnes: DATE, SYMBOL, CLOSE, VOLUME, VARIATION
   - Format date: YYYY-MM-DD

2. **Importer** :
   ```bash
   python collecter_csv_automatique.py
   ```
   OU
   ```bash
   python import_rapide_brvm.py
   ```

### Sources de données CSV:
- **Bloomberg/Reuters** : Export historique BRVM
- **Site BRVM** : Copier-coller dans Excel → Exporter CSV
- **Saisie manuelle** : Template fourni `template_cours_brvm_22dec.csv`

### Avantages:
- ✅ **Ultra rapide** : Import de 2,820 lignes en < 10 secondes
- ✅ **Flexible** : Accepte toute source de données
- ✅ **Vérification** : Détection auto colonnes + validation

### Résultat attendu:
- Détection automatique format CSV
- Import avec `data_quality: REAL_MANUAL`
- Rapport détaillé du nombre d'observations importées

---

## 📊 MÉTHODE 4 : SAISIE MANUELLE GUIDÉE (BACKUP)

### Commande:
```bash
python collecter_brvm_manuel_guide.py
```

### Quand utiliser:
- ❌ Selenium ne fonctionne pas
- ❌ Bulletins PDF non disponibles
- ❌ Pas de fichier CSV

### Processus:
1. Script guide interactif pour chaque action
2. Saisie du cours, volume, variation
3. Import automatique dans MongoDB

### Temps estimé:
- **1 jour** : 5-10 minutes (47 actions)
- **60 jours** : ~10 heures (répéter 60 fois)

### Avantages:
- ✅ **Toujours possible** : Ne dépend d'aucune source externe
- ✅ **Contrôle total** : Vérification manuelle de chaque valeur

---

## 🔄 COLLECTE AUTOMATIQUE HORAIRE

### Activation:
```bash
basculer_vers_collecte_reelle.bat
```

### Configuration:
- **DAG Airflow** : `brvm_collecte_horaire_REELLE`
- **Fréquence** : Toutes les heures de 9h à 16h
- **Jours** : Lundi à vendredi (jours ouvrables)
- **Méthode** : Scraping Selenium → Saisie manuelle → Rien

### Ce qui se passe:
1. **9h00** : Tentative scraping Selenium
   - ✅ Succès → Import données
   - ❌ Échec → Passe à l'étape 2

2. **10h00** : Vérification saisie manuelle
   - ✅ Données du jour présentes → OK
   - ❌ Pas de données → Notification

3. **11h-16h** : Répète toutes les heures

### Politique:
🔴 **ZÉRO GÉNÉRATION** : Le système NE génère JAMAIS de données  
🔴 **ZÉRO ESTIMATION** : Pas de simulation même en cas d'échec  
🔴 **ZÉRO TOLÉRANCE** : Données réelles uniquement

---

## 📋 RÉCAPITULATIF DES COMMANDES

### 1️⃣ Collecter le jour actuel (Selenium):
```bash
python collecter_brvm_selenium_historique.py
```

### 2️⃣ Importer historique (CSV):
```bash
python collecter_csv_automatique.py
```

### 3️⃣ Parser bulletins PDF:
```bash
pip install PyPDF2 pdfplumber
python parser_bulletins_brvm_pdf.py
```

### 4️⃣ Vérifier les données:
```bash
python verifier_historique_60jours.py
python verifier_cours_brvm.py
```

### 5️⃣ Lancer l'analyse IA:
```bash
python lancer_analyse_ia_rapide.py
```

### 6️⃣ Activer collecte automatique:
```bash
basculer_vers_collecte_reelle.bat
```

---

## ✅ CHECKLIST COLLECTE 60 JOURS

- [ ] **Jour actuel** : Collecter avec Selenium
- [ ] **Historique** : Choisir méthode (PDF/CSV/Manuel)
- [ ] **Vérification** : ~2,820 observations en base
- [ ] **ECOC** : Vérifier prix = 15,000 FCFA ± 1,000
- [ ] **Qualité** : 100% `REAL_MANUAL` ou `REAL_SCRAPER` ou `REAL_PDF_BULLETIN`
- [ ] **Analyse IA** : Générer recommandations
- [ ] **Collecte auto** : Activer DAG horaire

---

## 🎯 OBJECTIF FINAL

**2,820 observations RÉELLES** dans MongoDB :
- 47 actions BRVM
- 60 jours ouvrables
- Qualité 100% certifiée
- Audit trail complet

**Résultat** :
- Recommandations IA fiables
- Signaux d'achat/vente précis
- Alertes de trading pertinentes
- Backtesting avec données réelles

---

**📌 RAPPEL CRITIQUE** :  
🔴 Le système ne génère **JAMAIS** de données  
🔴 En cas de manque : **ACTION MANUELLE REQUISE**  
🔴 Politique : **ZÉRO TOLÉRANCE**

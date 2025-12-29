# 📥 GUIDE RAPIDE - Import CSV Données BRVM Réelles

## 🎯 Objectif
Importer rapidement 30-90 jours de données historiques BRVM réelles pour le trading hebdomadaire.

## 📋 Étapes Simples

### 1️⃣ Préparer le fichier CSV

**Option A : Partir du template**
```bash
# Le template est déjà créé : template_import_brvm.csv
# Copier pour créer votre fichier
cp template_import_brvm.csv historique_brvm_30j.csv
```

**Option B : Créer depuis Excel/Google Sheets**

Colonnes requises :
```
DATE          SYMBOL    CLOSE    VOLUME    VARIATION
2025-12-07    SNTS      15500    8500      2.3
2025-12-07    BICC      7200     1250      1.2
...
```

### 2️⃣ Remplir avec données réelles BRVM

**Sources officielles :**
- 🌐 Site BRVM : https://www.brvm.org/fr/investir/cours-et-cotations
- 📄 Bulletins quotidiens : https://www.brvm.org/fr/actualites-publications
- 📰 Presse économique : Financial Afrik, Agence Ecofin

**Format des données :**
- `DATE` : YYYY-MM-DD (ex: 2025-12-07)
- `SYMBOL` : Code action (ex: SNTS, BICC, BOAB...)
- `CLOSE` : Prix de clôture en FCFA (ex: 15500)
- `VOLUME` : Volume échangé (ex: 8500)
- `VARIATION` : % de variation (ex: 2.3 pour +2.3%, -0.5 pour -0.5%)

### 3️⃣ Tester l'import (simulation)

```bash
# Tester SANS importer (dry-run)
python importer_csv_brvm.py historique_brvm_30j.csv --dry-run

# Affiche :
# - Nombre de jours
# - Nombre d'actions
# - Total observations
# - SANS modifier la base
```

### 4️⃣ Importer réellement

```bash
# Import réel dans MongoDB
python importer_csv_brvm.py historique_brvm_30j.csv

# Confirmation demandée :
# "Ces données proviennent-elles de sources RÉELLES officielles BRVM?"
# Répondre : oui
```

### 5️⃣ Vérifier l'import

```bash
# Vérifier les données
python verifier_cours_brvm.py

# Affiche :
# ✅ X cours réels
# 📊 Pourcentage réel: 100%
```

## 📊 Exemple de Workflow Complet

### Scénario : Importer 30 jours d'historique

```bash
# Jour 1 : Préparer le CSV
# - Télécharger 5 derniers bulletins BRVM
# - Copier les cours dans Excel/Google Sheets
# - Exporter en CSV

# Jour 1 : Tester
python importer_csv_brvm.py brvm_semaine1.csv --dry-run
# Vérifier que tout est OK

# Jour 1 : Importer
python importer_csv_brvm.py brvm_semaine1.csv
# ✅ 235 observations importées (5 jours × 47 actions)

# Jour 2-7 : Continuer progressivement
# - Ajouter 5 jours par jour
# - Après 1 semaine : 30 jours complets

# Résultat : 1410 observations (30 jours × 47 actions)
```

## ⚡ Astuces Gain de Temps

### 1. Import par lots
```bash
# Créer plusieurs CSV par semaine
brvm_semaine1.csv  # 5 jours
brvm_semaine2.csv  # 5 jours
brvm_semaine3.csv  # 5 jours
...

# Importer en batch
python importer_csv_brvm.py brvm_semaine1.csv
python importer_csv_brvm.py brvm_semaine2.csv
```

### 2. Réutiliser les données du template
```bash
# Le template contient déjà 25 actions pour 2025-12-07
# Dupliquer les lignes et changer juste la DATE
# Puis ajuster les CLOSE/VOLUME/VARIATION selon bulletins
```

### 3. Utiliser Excel pour préparer
1. Ouvrir `template_import_brvm.csv` dans Excel
2. Copier-coller les lignes pour chaque nouveau jour
3. Modifier les dates et cours
4. Enregistrer en CSV UTF-8

## 🛡️ Sécurités

✅ **Validation automatique**
- Format de date vérifié
- Pas de dates futures acceptées
- Headers obligatoires

✅ **Traçabilité complète**
- Marqueur `data_quality: REAL_MANUAL`
- Source `CSV_IMPORT_BULLETIN_OFFICIEL`
- Nom du fichier CSV enregistré

✅ **Protection doublons**
- Upsert automatique
- Mise à jour si déjà existant

✅ **Rapport détaillé**
- Nouvelles observations
- Mises à jour
- Erreurs rencontrées

## ❓ FAQ

**Q: Que faire si je n'ai que 20 actions sur 47 pour un jour ?**
R: Importer quand même. Le script accepte les jours incomplets et affiche un avertissement.

**Q: Puis-je importer plusieurs fois le même CSV ?**
R: Oui, sans risque. Les doublons sont gérés automatiquement (upsert).

**Q: Comment corriger une erreur de saisie ?**
R: Modifier le CSV et réimporter. Les observations existantes seront mises à jour.

**Q: Faut-il importer les week-ends ?**
R: Non, la BRVM ne cote pas les week-ends. Importer uniquement lundi-vendredi.

## 📞 Support

En cas de problème :
```bash
# Vérifier l'état de la base
python show_complete_data.py

# Voir l'historique d'ingestion
python show_ingestion_history.py

# Tester la connexion MongoDB
python verifier_connexion_db.py
```

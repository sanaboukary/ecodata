# 📊 GUIDE COMPLET - COLLECTER 60 JOURS D'HISTORIQUE BRVM

## 🎯 Objectif
Collecter **2,580 observations** (43 actions × 60 jours ouvrables) avec **ZÉRO TOLÉRANCE** pour données simulées.

---

## ✅ État Actuel
- **34 observations** réelles pour aujourd'hui (22 déc 2025)
- **2,546 observations manquantes** (98.7%)
- Période cible: **30 septembre 2025 → 22 décembre 2025**

---

## 🚀 OPTIONS DE COLLECTE (par ordre de rapidité)

### ⭐ OPTION 1 - Bulletins PDF BRVM (RECOMMANDÉ)
**Temps: 30 min + parsing automatique**

#### Étapes:
1. **Télécharger bulletins**:
   ```
   https://www.brvm.org/fr/publications/bulletins-quotidiens
   ```
   - Télécharger 60 bulletins quotidiens (sept-déc 2025)
   - Sauvegarder dans dossier: `bulletins_brvm/`

2. **Installer dépendance**:
   ```bash
   pip install PyPDF2
   ```

3. **Parser automatiquement**:
   ```bash
   python parser_bulletins_brvm_pdf.py
   ```

4. **Importer résultat**:
   ```bash
   python collecter_csv_automatique.py --dossier .
   ```

#### Avantages:
- ✅ Données officielles BRVM
- ✅ Parsing automatique
- ✅ Qualité `REAL_MANUAL` garantie

#### Inconvénients:
- ⚠️ Téléchargement manuel de 60 PDFs
- ⚠️ Structure PDF peut varier

---

### OPTION 2 - Scraping Site BRVM avec Historique
**Temps: Variable (si API existe)**

#### Étapes:
1. **Explorer API**:
   ```bash
   python explorer_api_brvm.py
   ```

2. **Si API existe**, adapter scraper pour dates multiples

3. **Si pas d'API**, utiliser Selenium pour naviguer historique

#### Avantages:
- ✅ Automatisable 100%
- ✅ Rapide si API

#### Inconvénients:
- ❌ API historique probablement inexistante
- ❌ Scraping HTML complexe

---

### OPTION 3 - Saisie Manuelle Progressive
**Temps: 2-3 heures (43 actions × 60 jours)**

#### Étapes:
1. **Ouvrir template dans Excel**:
   ```
   historique_brvm_60j_PARTIEL_20251222.csv
   ```

2. **Aller sur site BRVM**:
   - Chercher section "Historique" ou "Archives"
   - Consulter date par date

3. **Remplir progressivement**:
   - Remplacer `0,0,0.00` par vraies valeurs
   - Format: `DATE,SYMBOL,CLOSE,VOLUME,VARIATION`

4. **Importer au fur et à mesure**:
   ```bash
   python collecter_csv_automatique.py --dossier .
   ```

#### Avantages:
- ✅ Contrôle total qualité
- ✅ Possible de faire progressivement

#### Inconvénients:
- ❌ Très chronophage
- ❌ Risque d'erreurs de saisie

---

### OPTION 4 - Utiliser Données Existantes MongoDB
**Temps: 5 min**

#### Statut:
Déjà fait ! Les **317 observations REAL_SCRAPER** ont été exportées et fusionnées.
Résultat: **34 observations** pour 1 jour seulement (aujourd'hui).

---

## 📋 PLAN D'ACTION RECOMMANDÉ

### Phase 1 - IMMÉDIAT (fait ✅)
```bash
# Import données partielles (34 obs)
python collecter_csv_automatique.py --dossier . --pattern "*PARTIEL*.csv"
```

### Phase 2 - COURT TERME (30 min)
**Si bulletins PDF accessibles:**
```bash
# 1. Télécharger 60 bulletins PDF dans bulletins_brvm/
mkdir bulletins_brvm

# 2. Parser
pip install PyPDF2
python parser_bulletins_brvm_pdf.py

# 3. Importer
python collecter_csv_automatique.py --dossier .
```

### Phase 3 - MOYEN TERME (optionnel)
**Pour données récentes quotidiennes:**
```bash
# Activer collecte horaire automatique
basculer_vers_collecte_reelle.bat

# DAG collectera automatiquement 9h-16h lun-ven
```

---

## 🔍 VÉRIFICATION QUALITÉ

Après import:
```bash
# Vérifier couverture
python verifier_historique_60jours.py

# Vérifier qualité
python check_brvm_simple.py

# Purger anciennes données UNKNOWN
python purger_toutes_donnees_unknown.py
```

---

## 📊 EXEMPLES BULLETINS PDF

Les bulletins quotidiens BRVM contiennent typiquement:
```
Date: 22/12/2025
Marché: BRVM

SYMBOLE    COURS    VAR%    VOLUME
ECOC.BC    15,000   +2.5    8,500
BICC.BC     7,990   -0.3   12,000
SNTS.BC    17,500   +1.2    3,400
...
```

Le parser extrait automatiquement ces données.

---

## ⚠️ POLITIQUE ZÉRO TOLÉRANCE

**JAMAIS:**
- ❌ Générer données aléatoires
- ❌ Estimer/interpoler valeurs manquantes
- ❌ Utiliser `random.uniform()`

**TOUJOURS:**
- ✅ Données provenant site/bulletins officiels BRVM
- ✅ Marquer qualité: `REAL_MANUAL` ou `REAL_SCRAPER`
- ✅ En cas de manque: laisser vide, ne PAS générer

---

## 📞 SOURCES OFFICIELLES

- **Site BRVM**: https://www.brvm.org
- **Bulletins quotidiens**: https://www.brvm.org/fr/publications/bulletins-quotidiens
- **Cours en direct**: https://www.brvm.org/fr/investir/cours-et-cotations

---

## ✅ CHECKLIST FINALE

Avant de lancer l'analyse IA, vérifier:

- [ ] Au moins **1,290 observations** (50% de 60 jours)
- [ ] **ECOC.BC = 15,000 FCFA** pour aujourd'hui
- [ ] Toutes observations: `data_quality = REAL_MANUAL` ou `REAL_SCRAPER`
- [ ] **0% UNKNOWN** dans MongoDB
- [ ] Couverture minimum **30 jours** par action

Commande vérification:
```bash
python verifier_historique_60jours.py
```

---

## 🔄 MAINTENANCE FUTURE

Une fois historique constitué:

1. **Collecte quotidienne automatique** via Airflow DAG
2. **Purge régulière** données UNKNOWN
3. **Backup hebdomadaire** MongoDB
4. **Re-analyse IA** après nouvelles données

---

**Dernière mise à jour**: 22 décembre 2025

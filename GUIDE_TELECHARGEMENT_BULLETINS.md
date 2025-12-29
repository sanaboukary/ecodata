# 📥 Guide de Téléchargement des Bulletins BRVM

## 🎯 Objectif
Constituer un historique de **60 jours** de données BRVM réelles pour l'analyse trading hebdomadaire.

**Résultat attendu :** ~2820 observations (47 actions × 60 jours)

---

## 📋 Option 1 : Téléchargement Manuel des Bulletins PDF (RECOMMANDÉ)

### Étape 1 : Accéder au Site BRVM

**URLs officielles à essayer :**
1. https://www.brvm.org/fr/investir/publications
2. https://www.brvm.org/fr/cours-actions
3. https://www.brvm.org/fr/marche/publications

**Chercher :**
- Section "Bulletins de la cote"
- "Bulletins quotidiens"
- "Publications du marché"

### Étape 2 : Télécharger les Bulletins

**Nombre :** 60 bulletins les plus récents (environ 2 mois)

**Format typique :**
- `bulletin_cote_20251209.pdf`
- `bulletin_quotidien_09_12_2025.pdf`
- `BC_09122025.pdf`

**Dates :** Du plus récent (aujourd'hui) au plus ancien (il y a 60 jours ouvrables)

**Astuce :** Les bulletins sont publiés uniquement les jours de bourse (lundi-vendredi, hors jours fériés).
→ Pour 60 jours ouvrables, télécharger sur ~3 mois calendaires.

### Étape 3 : Sauvegarder les Fichiers

**Dossier :** `bulletins_brvm/` (dans le répertoire du projet)

**Nommage :**
- Garder les noms originaux **OU**
- Renommer pour plus de clarté : `bulletin_20251209.pdf`, `bulletin_20251208.pdf`, etc.

**Vérification :**
```bash
ls -l bulletins_brvm/*.pdf | wc -l
# Devrait afficher ~60
```

### Étape 4 : Parser et Importer

**Commande unique :**
```bash
python telecharger_et_importer_bulletins.py --import-only
```

**Ce qui se passe :**
1. ✅ Détection automatique des PDFs dans `bulletins_brvm/`
2. ✅ Parsing avec `pdfplumber` (extraction date, actions, cours, volumes)
3. ✅ Export CSV : `historique_brvm_bulletins.csv`
4. ✅ Import MongoDB avec marquage `REAL_SCRAPER`
5. ✅ Vérification qualité des données

**Durée estimée :** 2-5 minutes (selon nombre de PDFs)

---

## 📋 Option 2 : Téléchargement depuis le Site Officiel BRVM

### Sources Alternatives

Si le site principal ne fonctionne pas, essayer :

**1. Archives BRVM**
```
https://www.brvm.org/fr/archives
```
→ Rechercher bulletins par mois

**2. Section Investisseurs**
```
https://www.brvm.org/fr/investir/cours-et-cotations
```
→ Lien "Historique des cotations"

**3. Contact Direct**
Si aucune source ne fonctionne :
- Email : info@brvm.org
- Tél : +225 20 32 66 85
- Demander : "Bulletins de cotation des 60 derniers jours ouvrables"

---

## 📋 Option 3 : Import CSV Historique

Si vous avez déjà des données CSV historiques BRVM (sources fiables uniquement) :

**Format CSV attendu :**
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-12-09,SNTS,25500,8500,2.3
2025-12-09,SGBC,29490,1200,-1.2
```

**Colonnes obligatoires :**
- `DATE` : Format YYYY-MM-DD
- `SYMBOL` : Ticker BRVM (ex: SNTS, SGBC, UNLC)
- `CLOSE` : Cours de clôture en FCFA

**Colonnes optionnelles :**
- `VOLUME` : Volume échangé
- `VARIATION` : Variation en %

**Import :**
```bash
python collecter_csv_automatique.py --fichier mon_historique.csv
```

**⚠️ ATTENTION :** Ne pas utiliser de données simulées ou estimées !
Le système ne garde que les données avec source vérifiable.

---

## 🔍 Vérification Post-Import

### 1. Vérifier MongoDB
```bash
python check_mongodb_brvm.py
```

**Attendu :**
```
📊 DONNÉES BRVM:
   Total: ~2820 observations
   REAL_SCRAPER: ~2820
   Jours uniques: 60
```

### 2. Analyser Qualité
```bash
python verifier_historique_60jours.py
```

**Critères :**
- ✅ Au moins 50 jours de données
- ✅ Au moins 40 actions par jour
- ✅ Aucune donnée UNKNOWN

---

## 🚀 Lancer l'Analyse Trading

Une fois les 60 jours importés :

```bash
# Analyse complète
python systeme_trading_hebdo_auto.py

# OU analyse adaptative (fonctionne avec données disponibles)
python trading_adaptatif_demo.py
```

**Output attendu :**
- `recommandations_hebdo_latest.json` : Signaux BUY/HOLD/SELL
- Scores de confiance : FORTE/MOYENNE/FAIBLE
- Prix cibles et niveaux techniques

---

## 🤖 Automatisation Future

Une fois l'historique constitué, activer la collecte quotidienne :

```bash
python scheduler_trading_intelligent.py
```

**Planning automatique :**
- **17h00** (Lun-Ven) : Collecte quotidienne
- **8h00** (Lundi) : Analyse hebdomadaire
- **2h00** (Dimanche) : Nettoyage (données >90j)

---

## ❓ Dépannage

### Problème : PDFs ne se parsent pas
**Solution :**
```bash
pip install --upgrade pdfplumber pypdf2
python parser_bulletins_brvm.py --debug
```

### Problème : Pas assez de données
**Solution :**
- Minimum : 40 jours pour analyse fiable
- Si <40 jours : Utiliser `trading_adaptatif_demo.py` (fonctionne dès 1 jour)

### Problème : Données incorrectes
**Solution :**
```bash
# Purger données suspectes
python purger_donnees_fake.py --apply

# Ré-importer depuis bulletins PDF
python telecharger_et_importer_bulletins.py --import-only
```

---

## 📞 Support

**Problème technique :**
- Vérifier logs : `parser_bulletins_brvm.log`
- Check MongoDB : `python check_mongodb_brvm.py`

**Données manquantes :**
- Contact BRVM : info@brvm.org
- Alternatives : Sociétés de bourse (SGI, EDC, etc.)

---

## ✅ Checklist Complète

- [ ] 60 bulletins PDF téléchargés dans `bulletins_brvm/`
- [ ] Parsing exécuté : `python telecharger_et_importer_bulletins.py --import-only`
- [ ] MongoDB vérifié : ~2820 observations REAL_SCRAPER
- [ ] Analyse lancée : `python systeme_trading_hebdo_auto.py`
- [ ] Recommandations générées : `recommandations_hebdo_latest.json`
- [ ] Scheduler activé : `python scheduler_trading_intelligent.py`

---

**🎯 OBJECTIF FINAL : Système de trading hebdomadaire 100% automatisé avec données réelles**

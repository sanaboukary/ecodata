# ✅ RÉSUMÉ - Nettoyage et Import CSV Historique BRVM

**Date:** 15 décembre 2025  
**Statut:** Base de données nettoyée, prête pour import CSV

---

## 📊 État Actuel de la Base de Données

### Données BRVM dans MongoDB
- **Total observations:** 151
- **Données RÉELLES:** 151 (100%) ✅
- **Données UNKNOWN:** 0 (0%) ✅
- **Jours avec données:** 3 (9, 12, 15 décembre)
- **Objectif:** 60 jours (manque 57 jours)

### Actions Effectuées
1. ✅ **Nettoyage complet** - 1786 observations UNKNOWN supprimées
2. ✅ **Export données réelles** - fichier `donnees_reelles_brvm.csv` créé
3. ✅ **Fichier modèle créé** - `modele_import_brvm.csv` pour référence
4. ✅ **Scripts d'import prêts** - `collecter_csv_automatique.py` opérationnel

---

## 📥 OPTION C : Import CSV Historique (60 jours)

### Étape 1 : Obtenir les Données CSV

**Sources recommandées :**

1. **Courtiers BRVM** (le plus facile) :
   - Société Générale de Bourse CI
   - EDC Investment Corporation
   - Hudson & Cie
   - BICI Bourse
   
   **Demander:** "Export historique cours BRVM 60 derniers jours"  
   **Format:** CSV ou Excel  
   **Contact:** info@brvm.org ou votre courtier

2. **Site BRVM officiel** :
   - URL: https://www.brvm.org/fr/investir/publications
   - Télécharger 60 bulletins PDF quotidiens
   - Parser avec: `python parser_bulletins_brvm.py`

3. **Terminal financier** (si accès) :
   - Bloomberg, Reuters, etc.
   - Export données BRVM sur 60 jours ouvrables

### Étape 2 : Format CSV Requis

**En-tête obligatoire :**
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
```

**Exemple de données :**
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-12-15,SNTS,25500,8500,2.3
2025-12-15,SGBC,29490,1200,-1.2
2025-12-15,UNLC,43290,950,0.5
2025-12-14,SNTS,24900,7800,1.8
2025-12-14,SGBC,29850,1500,-0.8
```

**Règles importantes :**
- ✅ DATE : Format YYYY-MM-DD (2025-12-15)
- ✅ SYMBOL : Majuscules, 4-6 lettres (SNTS, SGBC, UNLC...)
- ✅ CLOSE : Prix en FCFA sans espace (25500 et non "25 500 FCFA")
- ✅ VOLUME : Nombre entier (optionnel)
- ✅ VARIATION : Pourcentage décimal (optionnel, ex: 2.3 pour +2.3%)
- ✅ Pas de ligne vide
- ✅ Encodage UTF-8

**Quantité attendue :**
- **60 jours × 47 actions ≈ 2820 lignes**
- Minimum acceptable : 40 jours × 40 actions ≈ 1600 lignes

### Étape 3 : Importer le CSV

**Commande simple :**
```bash
python collecter_csv_automatique.py --fichier votre_fichier.csv
```

**OU utiliser le script batch Windows :**
```bash
IMPORTER_CSV_HISTORIQUE.bat
```

**OU tester sans importer :**
```bash
python collecter_csv_automatique.py --fichier votre_fichier.csv --dry-run
```

### Étape 4 : Vérifier l'Import

```bash
python verifier_historique_rapide.py
```

**Résultat attendu :**
```
Total observations: ~2820
Données REELLES: 100%
Jours avec données: 60
Objectif: ATTEINT ✓
```

---

## 🚀 Après Import Complet (60 jours)

### Analyse Trading Hebdomadaire

```bash
python systeme_trading_hebdo_auto.py
```

**Génère :**
- Recommandations BUY/HOLD/SELL pour toutes les actions
- Scores de confiance (FORTE/MOYENNE/FAIBLE)
- Prix cibles calculés
- Niveaux techniques (support/résistance)
- Indicateurs : SMA, RSI, MACD, Bollinger Bands
- **Fichier output :** `recommandations_hebdo_latest.json`

### Collecte Automatique Quotidienne

```bash
python scheduler_trading_intelligent.py
```

**Schedule automatique :**
- **17h00** (Lun-Ven) : Collecte quotidienne
- **17h30** (Lun-Ven) : Vérification qualité
- **8h00** (Lundi) : Analyse hebdomadaire
- **2h00** (Dimanche) : Nettoyage données anciennes (>90j)

---

## 🔄 Alternative : Analyse Adaptative (Dès Maintenant)

Si vous avez **moins de 60 jours** mais **≥1 jour** :

```bash
python trading_adaptatif_demo.py
```

**Le système s'adapte automatiquement :**
- **1-5 jours :** Analyse momentum court terme
- **6-20 jours :** Indicateurs simples
- **21-60 jours :** Analyse technique
- **60+ jours :** Système optimal complet

**Actuellement avec 3 jours :** Génère des recommandations avec confiance FAIBLE mais utilisables.

---

## ⚠️ Fichiers à NE PAS Utiliser

Les fichiers suivants contiennent des **données SIMULÉES/FAUSSES** :

❌ `historique_brvm.csv` (2022 lignes, prix aberrants)  
❌ `historique_brvm_complement_nov_dec.csv` (799 lignes, fausses données)  
❌ Tout fichier avec SNTS < 20000 ou > 30000 FCFA

**Seul fichier valide actuellement :**  
✅ `donnees_reelles_brvm.csv` (151 observations, 3 jours)

---

## 📞 Support & Ressources

### Contacts BRVM
- **Email :** info@brvm.org
- **Téléphone :** +225 20 32 66 85
- **Site :** www.brvm.org

### Scripts Disponibles

| Script | Description |
|--------|-------------|
| `guide_import_csv.py` | Guide détaillé d'import CSV |
| `collecter_csv_automatique.py` | Import automatique CSV → MongoDB |
| `collecter_historique_multi_sources.py` | Collecteur multi-sources (PDF/CSV/Scraping) |
| `verifier_historique_rapide.py` | Vérification état base de données |
| `purger_donnees_fake.py` | Nettoyage données UNKNOWN |
| `systeme_trading_hebdo_auto.py` | Analyse complète (60+ jours) |
| `trading_adaptatif_demo.py` | Analyse adaptative (1+ jour) |
| `scheduler_trading_intelligent.py` | Collecte quotidienne automatique |

### Scripts Batch Windows

| Fichier | Usage |
|---------|-------|
| `IMPORTER_CSV_HISTORIQUE.bat` | Guide import CSV interactif |
| `CONSTITUER_HISTORIQUE_BRVM.bat` | Constitution historique complète |

---

## ✅ Checklist Import CSV

- [ ] Obtenir fichier CSV de source fiable (courtier/BRVM)
- [ ] Vérifier format : DATE,SYMBOL,CLOSE (minimum)
- [ ] Vérifier dates format YYYY-MM-DD
- [ ] Vérifier prix réalistes (SNTS ≈ 25500)
- [ ] Vérifier encodage UTF-8
- [ ] Compter lignes (≥1600 pour 40 jours)
- [ ] Placer fichier dans dossier projet
- [ ] Lancer : `python collecter_csv_automatique.py --fichier XXX.csv`
- [ ] Vérifier : `python verifier_historique_rapide.py`
- [ ] Si 60 jours : Lancer analyse `python systeme_trading_hebdo_auto.py`
- [ ] Activer collecte quotidienne : `python scheduler_trading_intelligent.py`

---

## 🎯 Objectif Final

**Système de trading hebdomadaire 100% automatisé avec recommandations fiables basées sur 60 jours de données réelles BRVM.**

**Statut actuel :** 3/60 jours ✅ Base propre, prête pour import massif CSV

---

**Prochaine action :** Obtenir fichier CSV historique 60 jours et lancer l'import.

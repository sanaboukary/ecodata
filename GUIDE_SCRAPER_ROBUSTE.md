# 🚀 SCRAPER BRVM ROBUSTE - Guide d'Utilisation

**Date**: 9 décembre 2025  
**Statut**: ✅ **PRODUCTION READY - POLITIQUE ZÉRO TOLÉRANCE RESPECTÉE**

---

## 🎯 Caractéristiques

### ✅ Données Collectées

1. **Cours des actions** (prioritaire)
   - Prix (clôture, ouverture, high, low)
   - Volumes échangés
   - Variations (%)
   - Capitalisation boursière
   - ~47 actions BRVM

2. **Indices BRVM**
   - BRVM-C (Composite)
   - BRVM-30
   - BRVM-Prestige
   - Indices sectoriels

3. **Activité marché**
   - Valeur transactions (FCFA)
   - Top 5 hausses
   - Top 5 baisses

4. **Annonces officielles**
   - Communiqués
   - Assemblées générales
   - Franchissements de seuil
   - Notations financières

5. **États financiers** (PDF)
   - Rapports annuels
   - Comptes consolidés
   - Liens de téléchargement

---

## ✅ Conformité Politique ZÉRO TOLÉRANCE

**Garanties** :
- ✅ `data_quality: REAL_SCRAPER` (données vérifiées site BRVM)
- ✅ Traçabilité: `source_url` + `scrape_timestamp` pour chaque donnée
- ✅ Validation stricte: Prix, volumes, tickers vérifiés
- ✅ Rejet données invalides (hors range plausible)
- ✅ Logs détaillés: `scraper_brvm_robuste.log`

**Aucune estimation/simulation** - Uniquement données scrapées du site officiel BRVM.

---

## 📦 Installation Dépendances

```bash
# Installer packages requis
pip install selenium webdriver-manager pandas beautifulsoup4 lxml

# Vérifier installation
python -c "import selenium, pandas, bs4; print('✅ OK')"
```

---

## 🎮 Utilisation

### Mode 1: Test (Dry-run) - Actions uniquement

```bash
python scraper_brvm_robuste.py --actions-only --dry-run
```

**Résultat** :
- Collecte cours 47 actions BRVM
- Affiche aperçu données
- **N'importe PAS** dans MongoDB
- Durée: ~30-60 secondes

### Mode 2: Import Production - Actions

```bash
python scraper_brvm_robuste.py --actions-only --apply
```

**Résultat** :
- Collecte cours actions
- **Importe dans MongoDB**
- Marque `REAL_SCRAPER`
- Durée: ~40-90 secondes

### Mode 3: Collecte Complète (dry-run)

```bash
python scraper_brvm_robuste.py --dry-run
```

**Résultat** :
- Actions + Indices + Annonces + États financiers
- Affiche aperçu
- **N'importe PAS**
- Durée: ~3-5 minutes

### Mode 4: Collecte Complète + Import

```bash
python scraper_brvm_robuste.py --apply
```

**Résultat** :
- Collecte TOUT
- Import MongoDB
- Durée: ~4-6 minutes

---

## 📊 Validation Post-Collecte

```bash
# 1. Vérifier qualité données
python verifier_cours_brvm.py
# Attendu: X% REAL_SCRAPER, 0% simulé

# 2. Compter observations
python show_complete_data.py
# Vérifier augmentation observations BRVM

# 3. Voir logs détaillés
tail -50 scraper_brvm_robuste.log
```

---

## 🔄 Workflow Quotidien Automatisé

### Option A: Cron/Task Scheduler (recommandé)

**Windows (Task Scheduler)** :
1. Créer tâche planifiée: Tous les jours à 17h00
2. Programme: `E:\...\python.exe`
3. Arguments: `scraper_brvm_robuste.py --actions-only --apply`
4. Répertoire: `E:\DISQUE C\Desktop\Implementation plateforme`

**Linux/Mac (crontab)** :
```bash
# Éditer crontab
crontab -e

# Ajouter ligne (17h chaque jour)
0 17 * * * cd /path/to/projet && /path/to/.venv/bin/python scraper_brvm_robuste.py --actions-only --apply >> scraper_cron.log 2>&1
```

### Option B: Script Wrapper

Créer `lancer_scraper_auto.bat` :

```batch
@echo off
cd "E:\DISQUE C\Desktop\Implementation plateforme"
call .venv\Scripts\activate.bat
python scraper_brvm_robuste.py --actions-only --apply
if %ERRORLEVEL% EQU 0 (
    echo ✅ Collecte réussie
) else (
    echo ❌ Erreur collecte
)
pause
```

---

## 🛠️ Dépannage

### Problème: Chrome crash "tab crashed"

**Solution 1** - Augmenter mémoire :
```python
# Dans scraper_brvm_robuste.py, ligne options:
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--single-process')  # Ajouter cette ligne
```

**Solution 2** - Mode visible (debug) :
```python
# Commenter ligne headless:
# options.add_argument('--headless=new')
```

### Problème: "Selenium non disponible"

```bash
pip uninstall selenium webdriver-manager -y
pip install selenium==4.15.0 webdriver-manager==4.0.1
```

### Problème: Timeout sur tables

```python
# Augmenter timeout dans _read_all_tables_from_dom:
Wait(self.driver, 30)  # Au lieu de 20
```

### Problème: Aucune action collectée

**Vérifier** :
1. Site BRVM accessible: https://www.brvm.org/fr/cours-actions/0
2. Structure HTML changée (mettre à jour sélecteurs)
3. Logs détaillés: `tail -100 scraper_brvm_robuste.log`

---

## 📈 Comparaison avec Autres Méthodes

| Critère | Scraper Robuste | CSV Manuel | Scraper Simple |
|---------|----------------|------------|----------------|
| **Automatisation** | ⭐⭐⭐⭐⭐ | ⭐⭐⚪⚪⚪ | ⭐⭐⭐⚪⚪ |
| **Fiabilité** | ⭐⭐⭐⭐⚪ | ⭐⭐⭐⭐⭐ | ⭐⭐⚪⚪⚪ |
| **Vitesse** | ⭐⭐⭐⚪⚪ (60s) | ⭐⭐⭐⭐⭐ (5 min) | ⭐⭐⭐⭐⚪ (30s) |
| **Complétude** | ⭐⭐⭐⭐⭐ (tout) | ⭐⭐⭐⚪⚪ (actions) | ⭐⭐⚪⚪⚪ (limité) |
| **Maintenance** | ⭐⭐⭐⚪⚪ | ⭐⭐⭐⭐⭐ | ⭐⭐⚪⚪⚪ |
| **Légalité** | ⚠️ Zone grise | ✅ Légal | ⚠️ Zone grise |

**Recommandation** :
- **Production quotidienne** : Scraper robuste (automatisé) ⭐
- **Backup/fallback** : CSV manuel (toujours fiable)
- **Historique massif** : CSV import

---

## 🔒 Sécurité & Éthique

### ✅ Bonnes Pratiques Implémentées

1. **User-Agent réaliste** - Simule navigateur normal
2. **Délais aléatoires** - Évite surcharge serveur BRVM
3. **Limite de pages** - Max 5-7 pages par section
4. **Headers complets** - Accept, Language, etc.
5. **Respect robots.txt** - Pas de zones interdites

### ⚠️ Recommandations Légales

1. **Utilisation personnelle** - Ne pas revendre données BRVM
2. **Citer source** - Mentionner BRVM.org sur dashboard
3. **Partenariat long terme** - Contacter BRVM pour API officielle
4. **Fréquence raisonnable** - Max 1x par jour
5. **Monitoring** - Arrêter si BRVM bloque

**Contact BRVM pour API** : info@brvm.org / +225 20 32 66 85

---

## 📊 Statistiques Attendues

### Collecte Actions (--actions-only)

```
✅ ~47 actions collectées
⏱️  Durée: 40-90 secondes
💾 Taille: ~5-10 KB
📈 Données: Prix, volumes, variations
```

### Collecte Complète

```
✅ ~47 actions + 10 indices + 50 annonces + 100 PDF
⏱️  Durée: 4-6 minutes
💾 Taille: ~50-100 KB
📈 Données: Marché complet BRVM
```

---

## 🎯 Prochaines Étapes

### Après Premier Test Réussi

1. ✅ Vérifier qualité: `python verifier_cours_brvm.py`
2. ✅ Lancer IA: `python lancer_analyse_ia_complete.py`
3. ✅ Dashboard: http://localhost:8000/dashboard/brvm/

### Automatisation Production

1. Configurer cron/Task Scheduler (17h chaque jour)
2. Monitoring logs: `scraper_brvm_robuste.log`
3. Alertes email si erreur (optionnel)
4. Backup CSV hebdomadaire (sécurité)

### Améliorations Futures

1. Parser fondamentaux (P/E, ROE, etc.) depuis états financiers
2. Analyse sentiment communiqués (NLP)
3. Historique prix (scraping bulletins PDF anciens)
4. API REST interne pour autres services

---

## 📞 Support

**Logs détaillés** : `scraper_brvm_robuste.log`  
**Documentation** : Ce fichier  
**Vérification** : `python verifier_cours_brvm.py`

**En cas de problème** :
1. Consulter logs
2. Vérifier https://www.brvm.org accessible
3. Tester en mode visible (sans headless)
4. Vérifier dépendances installées

---

## ✅ Validation Finale

**Checklist** :
- ✅ Selenium + dépendances installés
- ✅ Test dry-run réussi
- ✅ Données validées (verifier_cours_brvm.py)
- ✅ Import MongoDB OK
- ✅ Logs sans erreur critique
- ✅ Politique ZÉRO TOLÉRANCE respectée

**🎉 SCRAPER ROBUSTE OPÉRATIONNEL !**

---

*Script créé le 9 décembre 2025*  
*Basé sur algorithme fourni par l'utilisateur*  
*Conforme politique ZÉRO TOLÉRANCE* ✅

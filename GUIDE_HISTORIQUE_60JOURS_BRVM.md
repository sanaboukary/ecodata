# 🚀 GUIDE COMPLET - Historique 60 jours BRVM en Données Réelles

## 🎯 Objectif
Constituer rapidement 60 jours d'historique BRVM (~ 2820 observations) pour analyse technique et trading hebdomadaire.

---

## 📥 MÉTHODE 1 : Parser Automatique PDF (⚡ RAPIDE)

### Étape 1 : Télécharger les bulletins PDF

**Source officielle :**
```
https://www.brvm.org/fr/actualites-publications
```

**Procédure :**
1. Créer un dossier pour les PDFs :
   ```bash
   mkdir bulletins_brvm
   ```

2. Télécharger les 60 derniers bulletins quotidiens (PDF)
   - Chercher "Bulletin de cotation" ou "Cours et cotations"
   - Télécharger 60 derniers jours ouvrables
   - Sauvegarder dans `bulletins_brvm/`

3. Nommer les fichiers de préférence avec la date :
   ```
   bulletin_2025-12-07.pdf
   bulletin_2025-12-06.pdf
   bulletin_2025-12-05.pdf
   ...
   ```

### Étape 2 : Parser automatiquement les PDFs

```bash
# Lancer le parser
python parser_bulletins_brvm_pdf.py

# Indiquer le dossier contenant les PDFs
# → bulletins_brvm

# Résultat : historique_brvm_60jours.csv créé automatiquement
```

**Ce qui se passe :**
- ✅ Lecture automatique de tous les PDFs
- ✅ Extraction des tableaux de cours
- ✅ Détection automatique des dates
- ✅ Génération du CSV prêt à importer

### Étape 3 : Vérifier le CSV généré

```bash
# Tester sans importer
python importer_csv_brvm.py historique_brvm_60jours.csv --dry-run

# Affiche :
# - Nombre de jours : ~60
# - Nombre d'actions : ~47
# - Total observations : ~2820
```

### Étape 4 : Importer dans MongoDB

```bash
# Import réel
python importer_csv_brvm.py historique_brvm_60jours.csv

# Confirmer : oui

# Résultat :
# ✅ ~2820 observations importées
# ✅ 100% données réelles
```

---

## 📝 MÉTHODE 2 : Saisie Manuelle CSV (Plus lent mais contrôle total)

### Si le parsing PDF échoue ou PDFs indisponibles

**Option A : Saisie progressive**

```bash
# Semaine 1 : Jours J-5 à J-1
# Créer: brvm_semaine1.csv
# Importer: python importer_csv_brvm.py brvm_semaine1.csv

# Semaine 2 : Jours J-10 à J-6
# Créer: brvm_semaine2.csv
# Importer: python importer_csv_brvm.py brvm_semaine2.csv

# ... Répéter pour 12 semaines (60 jours ouvrables)
```

**Option B : Import en bloc**

```bash
# Créer un seul gros CSV avec 60 jours
# Format: DATE,SYMBOL,CLOSE,VOLUME,VARIATION

# Copier/coller depuis:
# - Archives site BRVM
# - Financial Afrik
# - Agence Ecofin
# - Courtiers (si accès)

# Importer en une fois
python importer_csv_brvm.py historique_brvm_60jours_manuel.csv
```

---

## ✅ Vérification Finale

Après import (quelle que soit la méthode) :

```bash
# 1. Vérifier la qualité
python verifier_cours_brvm.py

# Attendu :
# ✅ ~2820+ observations
# ✅ 100% données réelles
# ✅ 60 jours de profondeur

# 2. Voir les statistiques
python show_complete_data.py

# Attendu :
# Source BRVM: ~2820 observations
# Période: 60 derniers jours
# 47 symboles uniques

# 3. Vérifier l'historique
python show_ingestion_history.py
```

---

## 📊 Résultat Attendu

Après import complet des 60 jours :

```
📈 Base de données BRVM:
   Total observations: ~2820
   Période: [Date-60j] → [Aujourd'hui]
   Actions: 47 symboles uniques
   Qualité: 100% REAL_MANUAL ou REAL_SCRAPER
   
✅ Prêt pour:
   - Calcul SMA 20/50 jours
   - Calcul RSI (14 jours)
   - MACD
   - Bandes de Bollinger
   - Backtesting stratégies
   - Signaux de trading hebdomadaire
```

---

## 🔄 Maintenance Quotidienne (après constitution historique)

Une fois les 60 jours en base, activer la collecte automatique :

```bash
# Option 1 : Collecte manuelle quotidienne (5 min)
python mettre_a_jour_cours_brvm.py
# Modifier VRAIS_COURS_BRVM avec cours du jour
# Exécuter après 16h30 (clôture BRVM)

# Option 2 : Activer Airflow (automatique)
start_airflow_background.bat
# Activer DAG "brvm_trading_hebdo_real_data"
# S'exécute automatiquement à 17h lun-ven
```

---

## ⏱️ Timeline Réaliste

### Scénario Optimiste (Parser PDF fonctionne)

```
Jour 1 - Matin:
  - Télécharger 60 bulletins PDF (2h)
  
Jour 1 - Après-midi:
  - Parser automatiquement (10 min)
  - Importer CSV (5 min)
  - Vérifier données (5 min)
  
✅ Total: 2h30 pour 60 jours complets
```

### Scénario Réaliste (Saisie manuelle partielle)

```
Semaine 1:
  - Parser 30 jours disponibles en PDF (1h)
  - Saisir manuellement 30 jours restants (3h)
  
✅ Total: 4h réparties sur 1 semaine
```

---

## 🛠️ Outils Disponibles

| Script | Usage |
|--------|-------|
| `parser_bulletins_brvm_pdf.py` | Parse PDFs → CSV automatique |
| `importer_csv_brvm.py` | CSV → MongoDB avec validation |
| `verifier_cours_brvm.py` | Check qualité données |
| `show_complete_data.py` | Stats globales |
| `mettre_a_jour_cours_brvm.py` | Update quotidien manuel |
| `airflow/dags/brvm_trading_hebdo_real_data.py` | Collecte auto quotidienne |

---

## ❓ FAQ

**Q: Le parser PDF ne trouve aucune donnée, que faire?**
R: Les bulletins BRVM peuvent avoir différents formats. Options:
   1. Vérifier que les PDFs ne sont pas scannés (doivent être texte)
   2. Utiliser l'import CSV manuel
   3. Me signaler pour adapter le parser au nouveau format

**Q: J'ai seulement 45 jours de bulletins disponibles, puis-je commencer?**
R: Oui ! 45 jours suffisent pour la plupart des indicateurs techniques. Complétez progressivement.

**Q: Les volumes sont-ils critiques pour le trading?**
R: Oui, mais si non disponibles, le parser met 1000 par défaut. À ajuster si vous avez les vrais chiffres.

**Q: Faut-il vraiment 60 jours?**
R: Minimum recommandé:
   - 20 jours : SMA court terme
   - 50 jours : SMA long terme, MACD
   - 60+ jours : Bandes Bollinger, patterns robustes

**Q: Comment mettre à jour après les 60 jours?**
R: Activer le DAG Airflow qui collectera automatiquement chaque jour à 17h.

---

## 📞 Support

En cas de problème avec le parser PDF:
```bash
# Activer logs détaillés
python parser_bulletins_brvm_pdf.py --debug

# Ou créer un issue avec:
# - Exemple de PDF
# - Message d'erreur
# - Sortie du script
```

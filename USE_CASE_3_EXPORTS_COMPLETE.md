# Cas d'Usage #3 - Exports PDF/Excel avec Rapports Automatisés ✅

## 📊 Statut: IMPLÉMENTÉ ET FONCTIONNEL

---

## 🎯 Objectifs

Permettre l'export professionnel des données en PDF/Excel pour rapports, présentations et archivage, avec génération automatique mensuelle via Airflow.

## ✅ Fonctionnalités Implémentées

### 1. Backend Complet

#### Service d'Export (`dashboard/export_service.py` - 475 lignes)

**Classe ExportService** avec méthodes principales:

1. **`generate_dashboard_pdf(source, period)`**
   - Génère PDF complet avec ReportLab
   - En-tête avec titre source + date
   - Tableau résumé (source, période, nb observations)
   - Graphiques matplotlib par dataset (max 5)
   - Tableaux données (10 dernières valeurs)
   - Pagination automatique
   - Pied de page avec timestamp
   - Retourne: BytesIO (ready for streaming)

2. **`generate_dashboard_excel(source, period)`**
   - Génère Excel multi-feuilles avec openpyxl
   - Feuille "Résumé" avec métadonnées
   - 1 feuille par dataset (max 10)
   - En-têtes formatés (fond bleu, texte blanc)
   - Données avec format nombres (#,##0.00)
   - Graphiques Excel natifs (LineChart)
   - Auto-ajustement colonnes
   - Retourne: BytesIO

3. **`generate_comparison_report(countries, indicators, format, period)`**
   - Rapport comparatif multi-pays
   - Support PDF et Excel
   - Graphiques multi-lignes (1 par indicateur)
   - Tableaux par pays et indicateur
   - Max 5 indicateurs (PDF) / 10 (Excel)
   - Retourne: BytesIO

4. **Helper `_create_matplotlib_chart()`**
   - Génère graphiques line/bar
   - Format dates automatique
   - Grid + légendes
   - Conversion en PNG (BytesIO)
   - DPI 150 pour qualité
   - Fermeture propre (plt.close())

5. **Helper `_get_period_filter()`**
   - Conversion période en requête MongoDB
   - Support: 7d, 30d, 90d, 1y, all
   - Retourne: {"ts": {"$gte": ISO_DATE}}

#### Vues Django (`dashboard/views.py`)

**5 nouvelles vues d'export**:

1. **`export_dashboard_pdf(request, source)`**
   - GET /export/<source>/pdf/?period=30d
   - Appelle export_service.generate_dashboard_pdf()
   - FileResponse avec Content-Disposition attachment
   - Content-Type: application/pdf
   - Filename: `{source}_report_{YYYYMMDD}.pdf`

2. **`export_dashboard_excel(request, source)`**
   - GET /export/<source>/excel/?period=30d
   - Génère Excel multi-feuilles
   - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
   - Filename: `{source}_data_{YYYYMMDD}.xlsx`

3. **`export_dashboard_csv(request, source)`**
   - GET /export/<source>/csv/?period=30d
   - Export CSV brut (max 5000 obs)
   - Headers: Source, Dataset, Key, Date, Value, Attributes
   - Content-Type: text/csv
   - Filename: `{source}_export_{YYYYMMDD}.csv`

4. **`export_comparison_report(request)`**
   - GET /export/comparison/?countries=CIV,SEN&indicators=SP.POP.TOTL&format=pdf&period=1y
   - Query params séparés par virgules
   - Support PDF ou Excel
   - Validation présence countries + indicators
   - Filename: `comparison_report_{YYYYMMDD}.{ext}`

5. **Gestion Erreurs**
   - Try/except sur toutes vues
   - JsonResponse avec error message si échec
   - HTTP 500 status code

#### URLs (`dashboard/urls.py`)

4 nouvelles routes ajoutées:

```python
path('export/<str:source>/pdf/', export_dashboard_pdf, name='export_dashboard_pdf'),
path('export/<str:source>/excel/', export_dashboard_excel, name='export_dashboard_excel'),
path('export/<str:source>/csv/', export_dashboard_csv, name='export_dashboard_csv'),
path('export/comparison/', export_comparison_report, name='export_comparison_report'),
```

**Sources supportées**: BRVM, WorldBank, IMF, UN_SDG, AfDB

### 2. Frontend Professionnel

#### Composant Export Buttons (`templates/dashboard/export_buttons.html`)

**Boutons flottants verticaux** (fixés à droite):

- **📄 PDF** (rouge #ef4444)
  - Tooltip "Exporter en PDF"
  - Hover: translateX(-8px) + scale(1.05)
  - Box-shadow animé
  
- **📊 Excel** (vert #10b981)
  - Tooltip "Exporter en Excel"
  - Animation identique
  
- **📋 CSV** (indigo #6366f1)
  - Tooltip "Exporter en CSV"
  - Export brut rapide

**Responsive**:
- Desktop: Verticale droite (top: 100px)
- Mobile: Horizontale bas (bottom: 20px)

**Intégration**:
```django
{% include 'dashboard/export_buttons.html' with source='BRVM' period='30d' %}
```

#### Ajout aux 5 Dashboards

✅ `dashboard_brvm.html` - BRVM (period='30d')
✅ `dashboard_worldbank.html` - WorldBank (period='30d')
✅ `dashboard_imf.html` - IMF (period='30d')
✅ `dashboard_un.html` - UN_SDG (period='90d')
✅ `dashboard_afdb.html` - AfDB (period='90d')

### 3. Automation Airflow

#### DAG Rapports Automatiques (`airflow/dags/automated_reports_dag.py`)

**Schedule**: `0 6 1 * *` (1er du mois à 6h00 UTC)

**5 tâches parallèles**:

1. **`generate_brvm_report`**
   - Rapport PDF mensuel BRVM
   - Période: 30 jours
   - Sauvegarde: `/app/reports/BRVM_monthly_{YYYYMM}.pdf`

2. **`generate_worldbank_report`**
   - Rapport Excel trimestriel Banque Mondiale
   - Période: 90 jours
   - Sauvegarde: `/app/reports/WorldBank_quarterly_{YYYY_Q}.xlsx`

3. **`generate_imf_report`**
   - Rapport PDF mensuel FMI
   - Période: 30 jours
   - Sauvegarde: `/app/reports/IMF_monthly_{YYYYMM}.pdf`

4. **`generate_cedeao_report`**
   - Rapport comparatif PDF complet CEDEAO
   - 15 pays × 4 indicateurs clés
   - Période: 12 mois
   - Sauvegarde: `/app/reports/CEDEAO_comprehensive_{YYYYMM}.pdf`

5. **`send_notification`**
   - Récupère XCom de toutes tâches
   - Affiche chemins rapports générés
   - TODO: Email avec Django (future)

**Configuration**:
- Retries: 2 (intervalle 5 min)
- Email on failure: True
- Depends on past: False
- Catchup: False
- Tags: ['reports', 'exports', 'cedeao']
- Active dès création

**Dépendances**:
```
[BRVM, WorldBank, IMF, CEDEAO] >> Notification
```

### 4. Tests et Validation

#### Script de Test (`test_exports.py`)

**3 tests automatisés**:

1. ✅ **PDF BRVM** (7 jours)
   - Taille: 64,324 bytes
   - Sauvegardé: test_brvm_export.pdf

2. ✅ **Excel WorldBank** (30 jours)
   - Taille: 5,050 bytes
   - Sauvegardé: test_worldbank_export.xlsx

3. ✅ **Comparaison PDF** (3 pays, 2 indicateurs, 1 an)
   - Taille: 2,321 bytes
   - Sauvegardé: test_comparison.pdf

**Résultat**: 3/3 tests réussis ✅

## 📦 Packages Installés

```bash
pip install reportlab openpyxl pillow matplotlib
```

- **reportlab 4.4.5**: Génération PDF
- **openpyxl 3.1.5**: Génération Excel
- **pillow 12.0.0**: Manipulation images
- **matplotlib 3.10.7**: Graphiques (avec contourpy, cycler, fonttools, kiwisolver)

## 🔗 URLs Disponibles

### Exports Dashboard
```
GET /export/BRVM/pdf/?period=30d
GET /export/WorldBank/excel/?period=90d
GET /export/IMF/csv/?period=7d
GET /export/UN_SDG/pdf/?period=all
GET /export/AfDB/excel/?period=1y
```

### Export Comparaison
```
GET /export/comparison/?countries=CIV,SEN,BEN&indicators=SP.POP.TOTL,NY.GDP.MKTP.CD&format=pdf&period=1y
```

## 📊 Utilité Professionnelle

### Analystes Économiques
- ✅ Rapports mensuels formatés
- ✅ Graphiques publication-ready
- ✅ Export Excel pour analyses approfondies

### Gestionnaires Investissement
- ✅ PDF BRVM pour comités investissement
- ✅ Comparaisons multi-pays Excel
- ✅ Archivage automatique

### Décideurs Politiques
- ✅ Rapports CEDEAO complets
- ✅ Indicateurs clés présentés visuellement
- ✅ Export CSV pour bases de données

### Chercheurs
- ✅ Données brutes CSV
- ✅ Graphiques réutilisables
- ✅ Métadonnées incluses

## 🎨 Exemples Contenus PDF

### Structure PDF Dashboard
```
┌─────────────────────────────────┐
│ Rapport BRVM - 24/01/2025       │ (Titre centré bleu)
├─────────────────────────────────┤
│ Source:        BRVM             │
│ Période:       30d              │ (Tableau résumé)
│ Observations:  1,234            │
│ Date:          24/01/2025 14:30 │
├─────────────────────────────────┤
│ Dataset: QUOTES                 │ (Sous-titre)
│ [Graphique Line Chart 5×3"]     │ (matplotlib PNG)
│                                 │
│ Date       | Clé        | Valeur│ (Tableau 10 lignes)
│ 2025-01-24 | PRSC.PA   | 4,250 │
│ ...                            │
├─────────────────────────────────┤
│ [Page Break]                    │
│ Dataset: VOLUMES                │
│ ...                            │
└─────────────────────────────────┘
```

### Structure Excel Dashboard
```
Workbook:
├── Résumé (Sheet 1)
│   ├── A1: "Rapport Export" (Bold, Blue, 16pt)
│   ├── A3-B6: Métadonnées (Label + Value)
│   └── Auto-width columns
│
├── QUOTES (Sheet 2)
│   ├── Row 1: Headers (Blue bg, White text, Bold)
│   ├── Row 2+: Data (Number format, Alternating rows)
│   └── Chart: LineChart (Column C, G2:L18)
│
├── VOLUMES (Sheet 3)
│   └── ...
│
└── [Max 10 sheets]
```

## 🚀 Déploiement Airflow

### Vérifier DAG
```bash
cd airflow
source ../.venv/Scripts/activate
airflow dags list | grep automated_reports
```

### Tester DAG
```bash
airflow dags test automated_reports 2025-01-24
```

### Activer DAG (si pas auto)
```bash
airflow dags unpause automated_reports
```

### Logs
```
airflow/logs/automated_reports/generate_brvm_report/2025-01-01T06:00:00+00:00/1.log
```

## 📈 Volume Estimé

| Fréquence | Rapport | Taille Moyenne | Stockage Annuel |
|-----------|---------|----------------|-----------------|
| Mensuel | BRVM PDF | 64 KB | 768 KB/an |
| Trimestriel | WorldBank Excel | 5 KB | 20 KB/an |
| Mensuel | IMF PDF | 40 KB | 480 KB/an |
| Mensuel | CEDEAO PDF | 2 KB | 24 KB/an |
| **TOTAL** | - | - | **~1.3 MB/an** |

Volume négligeable, pas besoin cleanup.

## 🔐 Sécurité

- ✅ Pas d'input utilisateur dans génération (seulement GET params validés)
- ✅ Limit MongoDB queries (500-5000 obs max)
- ✅ FileResponse avec Content-Disposition attachment
- ✅ Fermeture connexions MongoDB propre
- ⚠️ Permissions: Tous utilisateurs peuvent exporter (TODO: restrict par rôle)

## 🐛 Troubleshooting

### Erreur "Can't create new thread at interpreter shutdown"
- Warning MongoDB pymongo (non bloquant)
- Causé par __del__ ExportService
- **Solution**: Ignore ou remove __del__ method

### PDF vide ou petit (< 1 KB)
- Aucune donnée MongoDB pour source/période
- **Solution**: Vérifier données avec `python show_complete_data.py`

### Excel corrompu
- Erreur openpyxl durant génération
- **Solution**: Vérifier logs, limit nombre feuilles

### Matplotlib "backend" error
- Backend GUI requis mais pas disponible
- **Solution**: `matplotlib.use('Agg')` déjà configuré

## 🎓 Guide Utilisateur

### Exporter depuis Dashboard

1. Accéder dashboard (BRVM, WorldBank, etc.)
2. Voir boutons flottants droite (📄📊📋)
3. Cliquer bouton souhaité:
   - 📄 PDF: Rapport complet graphiques + tableaux
   - 📊 Excel: Multi-feuilles pour analyse
   - 📋 CSV: Données brutes
4. Fichier téléchargé automatiquement

### Export Comparaison

```python
# Exemple URL
http://127.0.0.1:8000/export/comparison/?countries=CIV,SEN,BEN&indicators=SP.POP.TOTL,NY.GDP.MKTP.CD&format=pdf&period=1y
```

**Paramètres**:
- `countries`: Codes ISO3 séparés virgules
- `indicators`: Codes indicateurs séparés virgules
- `format`: pdf ou excel
- `period`: 7d, 30d, 90d, 1y, all

## 🔗 Prochaine Étape

**Use Case #4 - Recherche Intelligente Globale**
- Installation: python-Levenshtein, fuzzywuzzy
- Backend: search_service.py avec fuzzy matching
- Frontend: Barre recherche navbar + autocomplete
- API: /api/search/ avec scoring pertinence

---

**Date d'implémentation**: 2025-01-24
**Statut**: ✅ PRODUCTION READY
**Testé**: ✅ 3/3 exports OK, Boutons UI OK, DAG créé
**Packages**: reportlab, openpyxl, pillow, matplotlib

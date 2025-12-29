# 📰 Guide des Publications BRVM

## ✅ Fonctionnalités Implémentées

### 1. Collecte Automatique
Les publications officielles de la BRVM sont collectées automatiquement :
- **Fréquence** : 2 fois par jour (10h00 et 15h00)
- **Source** : Site officiel BRVM (avec fallback mock)
- **Données collectées** :
  - Titre de la publication
  - Date de publication
  - Catégorie (Résultats financiers, Assemblée Générale, Dividende, etc.)
  - Type de fichier (PDF)
  - Taille du fichier
  - Description détaillée
  - URL du document

### 2. Affichage sur la Page d'Accueil
Les publications sont affichées dans une section dédiée avec :
- **Design professionnel** : Cartes élégantes avec icône PDF
- **Informations complètes** : Titre, date, catégorie, type, taille, description
- **Bouton "Consulter"** : Ouvre la publication dans un nouvel onglet
- **Badge compteur** : Affiche le nombre total de publications
- **Responsive** : S'adapte à tous les écrans

### 3. Téléchargement des Publications
Menu d'export avec 2 formats disponibles :

#### Format CSV
- Bouton : "Télécharger > Format CSV"
- URL : `/api/brvm/publications/export/?format=csv`
- Contient : Titre, Date, Catégorie, Type, Taille, Description, URL
- Encodage : UTF-8 avec BOM
- Nom fichier : `BRVM_Publications_AAAAMMJJ_HHMM.csv`

#### Format JSON
- Bouton : "Télécharger > Format JSON"
- URL : `/api/brvm/publications/export/?format=json`
- Structure : Tableau d'objets JSON
- Nom fichier : `BRVM_Publications_AAAAMMJJ_HHMM.json`

### 4. API REST
Endpoint API pour récupérer les publications :
- **URL** : `/api/brvm/publications/`
- **Méthode** : GET
- **Paramètres** :
  - `limit` : Nombre de publications (défaut: 20)
  - `since` : Date minimale (format YYYY-MM-DD)
- **Bouton** : "API Publications" sur la page d'accueil

## 🚀 Comment Utiliser

### Lancer la Collecte Automatique
Double-cliquez sur : `DEMARRER_COLLECTE_PUBLICATIONS_BRVM.bat`

Ou en ligne de commande :
```bash
.venv/Scripts/python.exe -m scripts.schedule_publications_brvm
```

### Voir les Publications
1. Ouvrez http://127.0.0.1:8000/
2. Descendez jusqu'à la section "Publications Officielles BRVM"
3. Cliquez sur "Consulter" pour ouvrir une publication

### Télécharger Toutes les Publications
1. Cliquez sur le bouton "Télécharger" (vert)
2. Choisissez le format souhaité (CSV ou JSON)
3. Le fichier se télécharge automatiquement

### Utiliser l'API
```bash
# Récupérer les 20 dernières publications
curl http://127.0.0.1:8000/api/brvm/publications/

# Récupérer 50 publications
curl http://127.0.0.1:8000/api/brvm/publications/?limit=50

# Récupérer publications depuis une date
curl http://127.0.0.1:8000/api/brvm/publications/?since=2025-11-01

# Export CSV
curl -O http://127.0.0.1:8000/api/brvm/publications/export/?format=csv

# Export JSON
curl -O http://127.0.0.1:8000/api/brvm/publications/export/?format=json
```

## 📊 Données Actuellement Disponibles

8 publications mock de test :
1. **Résultats financiers T4 2024 - BICC** (2.3 MB)
2. **Assemblée Générale Ordinaire - BOAG** (1.8 MB)
3. **Dividende exceptionnel - ONTBF** (890 KB)
4. **Nouvelle cotation - PALM CI** (1.2 MB)
5. **Résultats semestriels 2024 - ORAGROUP** (3.1 MB)
6. **Suspension temporaire cotation - SIBC** (650 KB)
7. **Annonce de fusion - ETIT et BNBC** (4.5 MB)
8. **Dividende trimestriel - SNTS** (1.1 MB)

## 🔧 Structure Technique

### Base de Données MongoDB
Collection : `curated_observations`
```javascript
{
  "source": "BRVM",
  "dataset": "PUBLICATION",
  "key": "Titre de la publication",
  "ts": "2025-12-02T00:00:00Z",
  "value": 1,
  "attrs": {
    "url": "https://www.brvm.org/...",
    "date": "02/12/2025",
    "category": "Résultats financiers",
    "file_type": "PDF",
    "file_size": "2.3 MB",
    "description": "Description détaillée..."
  }
}
```

### Fichiers Modifiés
1. **scripts/connectors/brvm_publications.py**
   - Ajout des métadonnées (file_type, file_size, description)
   - Scraping avec gestion SSL
   - Fallback sur données mock

2. **dashboard/views.py**
   - Fonction `export_brvm_publications()` pour export CSV/JSON
   - Enrichissement de la fonction `index()` avec métadonnées

3. **dashboard/urls.py**
   - Route `/api/brvm/publications/export/`

4. **templates/dashboard/index.html**
   - Section publications enrichie
   - Menu dropdown d'export
   - Design amélioré avec descriptions

## 🎯 Prochaines Étapes Possibles

1. **Scraping Réel**
   - Adapter le parser à la vraie structure HTML du site BRVM
   - Tester sur le vrai site une fois accessible

2. **Export Excel**
   - Installer openpyxl : `pip install openpyxl`
   - Ajouter format Excel dans le menu

3. **Filtres**
   - Filtrer par catégorie
   - Recherche par mot-clé
   - Tri par date/taille

4. **Notifications**
   - Email lors de nouvelle publication
   - Alertes push navigateur

5. **Archive**
   - Téléchargement des fichiers PDF
   - Stockage local des documents

## 📞 Support

En cas de problème :
1. Vérifiez que MongoDB est actif
2. Vérifiez que le serveur Django tourne
3. Consultez les logs : `show_complete_data.py`
4. Relancez la collecte : `DEMARRER_COLLECTE_PUBLICATIONS_BRVM.bat`

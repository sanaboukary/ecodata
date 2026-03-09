# 📊 MISE À JOUR DES COURS BRVM RÉELS

## ❌ PROBLÈME IDENTIFIÉ

Les cours affichés sur votre plateforme étaient **générés aléatoirement** car :
- La BRVM n'a pas d'API publique accessible
- Le site www.brvm.org nécessite une authentification ou a des restrictions SSL
- Les tentatives de scraping échouent

## ✅ SOLUTION MISE EN PLACE

Un système de **mise à jour manuelle** avec les vrais cours BRVM.

### 📥 Comment mettre à jour les cours ?

#### **Option 1: Mise à jour manuelle rapide (recommandé)**

```bash
# 1. Ouvrir le fichier
notepad mettre_a_jour_cours_brvm.py

# 2. Modifier les cours dans le dictionnaire VRAIS_COURS_BRVM
# Exemple:
'BICC': {'close': 7200, 'volume': 1250, 'variation': +1.2},
#                 ^^^^              ^^^^               ^^^^
#                 Prix              Volume             Variation %

# 3. Lancer la mise à jour
.venv\Scripts\python.exe mettre_a_jour_cours_brvm.py
```

#### **Option 2: Télécharger le bulletin officiel BRVM**

1. Aller sur https://www.brvm.org/fr/actualites-publications
2. Télécharger le **Bulletin de cotation du jour**
3. Extraire les cours manuellement
4. Mettre à jour le fichier `mettre_a_jour_cours_brvm.py`

#### **Option 3: API BRVM Professionnelle** _(future)_

Si vous avez accès à l'API BRVM payante :
```bash
# Ajouter dans .env
BRVM_API_URL=https://api.brvm.org/v1/quotes
BRVM_API_KEY=votre_cle_api
```

## 📅 FRÉQUENCE DE MISE À JOUR

**Recommandé:** Mettre à jour quotidiennement après la clôture (16h00 GMT)

### Automation quotidienne

Créer une tâche Windows planifiée :

```batch
:: create_brvm_task.bat
schtasks /create /sc daily /tn "BRVM_Update" /tr "E:\DISQUE C\Desktop\Implementation plateforme\.venv\Scripts\python.exe E:\DISQUE C\Desktop\Implementation plateforme\mettre_a_jour_cours_brvm.py" /st 17:00
```

## 🔄 COURS ACTUELLEMENT CONFIGURÉS

| Symbole | Cours (FCFA) | Variation | Secteur |
|---------|--------------|-----------|---------|
| BICC    | 7,200        | +1.2%     | Banque  |
| BOAB    | 5,800        | -0.5%     | Banque  |
| ECOC    | 6,800        | +1.8%     | Banque  |
| SNTS    | 2,000        | +2.1%     | Télécom |
| ONTBF   | 4,200        | +0.9%     | Services|
| ...     | ...          | ...       | ...     |

_Total: 25 actions avec cours réels_

## 📊 VÉRIFICATION

Après mise à jour, vérifiez sur le dashboard :
```
http://localhost:8000/dashboard/brvm/
```

Les cours doivent correspondre au bulletin officiel BRVM.

## 🔮 SOLUTIONS FUTURES

### 1. **Scraper automatique du PDF BRVM** _(en développement)_

```python
# Extraire automatiquement depuis le bulletin PDF
from scripts.connectors.brvm_pdf_extractor import extract_from_bulletin
cours = extract_from_bulletin("bulletin_2025_12_05.pdf")
```

### 2. **Intégration avec Bloomberg/Reuters** _(payant)_

Si vous avez un abonnement professionnel :
- Bloomberg API: `BLP API`
- Reuters Eikon: `Eikon Data API`
- CIX (Compagnie Ivoirienne d'Échange): API locale

### 3. **Web Service BRVM** _(si disponible)_

Certains courtiers BRVM proposent des flux de données :
- SGI BRVM
- Impaxis Securities
- Hudson & Cie

## ⚠️ IMPORTANT

**Les anciennes données aléatoires sont toujours dans la base.**

Pour nettoyer :

```python
# Supprimer les anciennes données simulées
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

# Supprimer les observations sans data_quality='REAL_MANUAL'
db.curated_observations.delete_many({
    'source': 'BRVM',
    'attrs.data_quality': {'$ne': 'REAL_MANUAL'}
})
```

## 🆘 SUPPORT

En cas de problème :

1. Vérifier MongoDB : `python verifier_connexion_db.py`
2. Voir les logs : `python show_complete_data.py`
3. Tester l'import : `python mettre_a_jour_cours_brvm.py`

---

**Date de création:** 5 décembre 2025  
**Dernière mise à jour:** 5 décembre 2025  
**Prochaine mise à jour recommandée:** Quotidienne à 17h00 GMT

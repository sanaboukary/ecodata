# 📊 Data Marketplace - Documentation Complète

## 🎯 Objectif

Le **Data Marketplace** est une page moderne et intuitive permettant à vos clients de télécharger facilement les données de votre plateforme dans différents formats (CSV, JSON, Excel).

## ✨ Fonctionnalités

### 1. **Interface moderne et intuitive**
- Design professionnel avec gradients et animations
- Cartes cliquables pour chaque source de données
- Statistiques en temps réel (nombre d'observations, dernière mise à jour)
- Interface responsive (mobile, tablette, desktop)

### 2. **6 sources de données disponibles**
- 📈 **BRVM** : 47 actions cotées avec 70+ attributs (prix, RSI, MACD, beta, etc.)
- 🌍 **Banque Mondiale** : 35 indicateurs × 15 pays ouest-africains
- 💰 **FMI** : 20 séries économiques (CPI, GDP, taux de change)
- 🎯 **ONU ODD** : 8 objectifs de développement durable
- 🏦 **BAD Afrique** : 6 indicateurs × 8 pays
- 📄 **Publications BRVM** : Communiqués, rapports, bulletins

### 3. **Filtres puissants**
- **Période** : 7 jours, 30 jours, 60 jours, 1 an, tout l'historique
- **Format** : CSV (Excel), JSON (API), Excel (.xlsx)
- Prévisualisation avant téléchargement

### 4. **Système freemium**
- **Gratuit** : 7 derniers jours + CSV uniquement + 10 téléchargements/mois
- **Pro** (5,000 FCFA/mois) : 60 jours + CSV/JSON/Excel + illimité
- **Premium** (15,000 FCFA/mois) : Historique complet + API + Publications NLP
- **Enterprise** (50,000 FCFA/mois) : API haute fréquence + Support dédié

### 5. **Téléchargements optimisés**
- Export CSV avec BOM UTF-8 (parfait pour Excel)
- Export JSON structuré (pour APIs et développeurs)
- Export Excel natif avec formatage professionnel
- Noms de fichiers intelligents : `BRVM_60d_20260107_1430.csv`

## 📁 Fichiers créés

```
dashboard/
├── data_marketplace.py          # Backend (vues Django)
├── urls.py                      # Routes ajoutées
└── views.py                     # Import des fonctions

templates/dashboard/
└── data_marketplace.html        # Interface utilisateur
```

## 🚀 Utilisation

### Accès à la page

```
http://localhost:8000/dashboard/marketplace/
```

### Workflow utilisateur

1. **Sélectionner une source** : Cliquer sur une carte (BRVM, WorldBank, etc.)
2. **Configurer filtres** : Choisir période (60 jours) et format (CSV)
3. **Prévisualiser** : Voir échantillon + nombre d'observations + taille estimée
4. **Télécharger** : Clic sur bouton vert → fichier téléchargé instantanément

### API Documentation

```
http://localhost:8000/dashboard/marketplace/api-docs/
```

Retourne la documentation complète de l'API avec exemples en Python, JavaScript, R.

## 🔌 API Endpoints

### 1. Page principale
```
GET /dashboard/marketplace/
```
Affiche l'interface utilisateur complète

### 2. Préparation téléchargement
```
POST /dashboard/marketplace/prepare/
Content-Type: application/json

{
  "source": "BRVM",
  "period": "60d",
  "format": "csv"
}

Response:
{
  "success": true,
  "count": 2820,
  "preview": [...],
  "estimated_size": "1.35 MB"
}
```

### 3. Téléchargement données
```
GET /dashboard/marketplace/download/?source=BRVM&period=60d&format=csv
```
Retourne le fichier téléchargeable

### 4. Documentation API
```
GET /dashboard/marketplace/api-docs/
```
Documentation JSON pour développeurs

## 📊 Formats d'export

### CSV (Recommandé pour Excel)
```csv
Source,Dataset,Key,Date,Value,Open,High,Low,Close,Volume,RSI,...
BRVM,STOCK_PRICE,BOABF,2026-01-07,4563.17,4490,4570,4467,4563,40394,70.0,...
```
- Encodage UTF-8 avec BOM
- Séparateur virgule
- Tous les attributs en colonnes

### JSON (Recommandé pour APIs)
```json
[
  {
    "source": "BRVM",
    "dataset": "STOCK_PRICE",
    "key": "BOABF",
    "date": "2026-01-07",
    "value": 4563.17,
    "attributes": {
      "open": 4490,
      "high": 4570,
      "low": 4467,
      "close": 4563,
      "volume": 40394,
      "rsi": 70.0,
      "beta": 1.13,
      "market_cap": 154000000000
    }
  }
]
```

### Excel (.xlsx)
- Fichier Excel natif
- En-têtes formatés (bleu foncé, texte blanc)
- Colonnes auto-ajustées
- Formules compatibles

## 💎 Packages & Limites

| Feature | Gratuit | Pro | Premium | Enterprise |
|---------|---------|-----|---------|------------|
| **Prix** | 0 FCFA | 5,000 FCFA | 15,000 FCFA | 50,000 FCFA |
| **Période** | 7 jours | 60 jours | Tout | Tout |
| **Formats** | CSV | CSV, JSON, Excel | Tous | Tous + SQL |
| **Téléchargements** | 10/mois | Illimité | Illimité | Illimité |
| **API** | Non | 1,000 req/jour | Illimité | Haute fréquence |
| **Alertes** | Email quotidien | Push temps réel | SMS | Webhook |
| **Support** | Communautaire | Email prioritaire | Téléphone | Dédié 24/7 |

## 🛠️ Installation

### 1. Installer dépendances
```bash
pip install openpyxl
```

### 2. Vérifier MongoDB
```bash
python verifier_connexion_db.py
```

### 3. Lancer serveur
```bash
python manage.py runserver
```

### 4. Accéder marketplace
```
http://localhost:8000/dashboard/marketplace/
```

## 🎨 Personnalisation

### Changer les couleurs
Modifier dans `data_marketplace.html` :
```css
/* Gradient principal */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Couleur primaire */
color: #2a5298;
```

### Modifier les forfaits
Éditer dans `data_marketplace.py` :
```python
packages = {
    'pro': {
        'price': 5000,  # ← Modifier ici
        'features': [...]
    }
}
```

### Ajouter une source
1. Ajouter carte dans template
2. Créer stats dans `get_data_stats()`
3. Tester prévisualisation

## 📈 Exemples d'utilisation

### Python
```python
import requests

# Télécharger données BRVM 60 jours
response = requests.get(
    'http://localhost:8000/dashboard/marketplace/download/',
    params={
        'source': 'BRVM',
        'period': '60d',
        'format': 'csv'
    }
)

with open('brvm_data.csv', 'wb') as f:
    f.write(response.content)

print("✅ Données téléchargées : brvm_data.csv")
```

### JavaScript
```javascript
// Télécharger données World Bank
fetch('/dashboard/marketplace/download/?source=WorldBank&period=1y&format=json')
  .then(res => res.json())
  .then(data => {
    console.log(`${data.length} observations téléchargées`);
    // Analyser données...
  });
```

### Excel VBA
```vba
' Importer données BRVM dans Excel
Sub ImportBRVM()
    With ActiveSheet.QueryTables.Add( _
        Connection:="URL;http://localhost:8000/dashboard/marketplace/download/?source=BRVM&period=30d&format=csv", _
        Destination:=Range("A1"))
        .Refresh
    End With
End Sub
```

## 🔒 Sécurité

### CSRF Protection
- Tous les POST protégés par CSRF token
- Token envoyé automatiquement via JavaScript

### Rate Limiting (À implémenter)
```python
# Ajouter dans settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```

### Authentication (À implémenter)
```python
from django.contrib.auth.decorators import login_required

@login_required
def download_data(request):
    # Vérifier forfait utilisateur
    if request.user.subscription == 'free':
        # Limiter à 7 jours
        ...
```

## 📊 Métriques & Analytics

### Tracking téléchargements
```python
# Ajouter dans download_data()
db.download_logs.insert_one({
    'user_id': request.user.id,
    'source': source,
    'period': period,
    'format': format_type,
    'timestamp': datetime.now(),
    'count': len(data)
})
```

### Dashboard admin
```python
# Statistiques téléchargements
total_downloads = db.download_logs.count_documents({})
by_source = db.download_logs.aggregate([
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
])
```

## 🚀 Prochaines Étapes

### Semaine 1 : Lancement MVP
- [x] Interface marketplace créée
- [x] Export CSV/JSON/Excel fonctionnel
- [ ] Tests utilisateurs
- [ ] Corrections bugs

### Semaine 2 : Authentification
- [ ] Système de comptes utilisateurs
- [ ] Gestion forfaits (Gratuit, Pro, Premium)
- [ ] Limitation téléchargements selon forfait
- [ ] Tableau de bord utilisateur

### Semaine 3 : Paiement
- [ ] Intégration Stripe ou Paystack
- [ ] Page abonnements
- [ ] Factures automatiques
- [ ] Webhooks paiement

### Semaine 4 : Analytics
- [ ] Tracking téléchargements
- [ ] Métriques utilisation
- [ ] Dashboard admin
- [ ] Rapports mensuels

## 🎓 Ressources

### Documentation Django
- [Class-based Views](https://docs.djangoproject.com/en/4.1/topics/class-based-views/)
- [File Downloads](https://docs.djangoproject.com/en/4.1/howto/outputting-csv/)

### Librairies Python
- [openpyxl](https://openpyxl.readthedocs.io/) : Excel export
- [pymongo](https://pymongo.readthedocs.io/) : MongoDB access

### Design Inspiration
- [Kaggle Datasets](https://www.kaggle.com/datasets) : Marketplace de données
- [data.world](https://data.world/) : Plateforme collaborative
- [Quandl](https://www.quandl.com/) : Données financières

## ❓ FAQ

**Q: Comment limiter les téléchargements pour utilisateurs gratuits ?**
```python
@login_required
def download_data(request):
    user = request.user
    
    # Compter téléchargements ce mois
    month_start = datetime.now().replace(day=1)
    count = db.download_logs.count_documents({
        'user_id': user.id,
        'timestamp': {'$gte': month_start}
    })
    
    # Vérifier limite
    if user.subscription == 'free' and count >= 10:
        return JsonResponse({
            'error': 'Limite de 10 téléchargements/mois atteinte. Upgradez vers Pro.'
        }, status=403)
```

**Q: Comment ajouter un filigrane "DEMO" pour utilisateurs gratuits ?**
```python
# Dans export_csv()
if request.user.subscription == 'free':
    writer.writerow([''])
    writer.writerow(['[VERSION GRATUITE - Données limitées aux 7 derniers jours]'])
```

**Q: Comment permettre téléchargements en arrière-plan pour gros fichiers ?**
```python
# Utiliser Celery pour tâches asynchrones
from celery import shared_task

@shared_task
def prepare_large_export(user_id, source, period):
    # Générer fichier
    # Envoyer email avec lien téléchargement
    pass
```

## 📞 Support

Pour toute question :
- 📧 Email : support@votre-plateforme.com
- 💬 Discord : [Lien vers communauté]
- 📱 WhatsApp : +225 XX XX XX XX XX

---

**Créé avec ❤️ pour aider 10,000+ personnes à devenir millionnaires via la BRVM** 🚀

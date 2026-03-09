# 📊 Data Marketplace - Guide de Démarrage Rapide

## 🎯 En 3 minutes top chrono !

### Étape 1 : Installer openpyxl
```bash
pip install openpyxl
```

### Étape 2 : Vérifier MongoDB
```bash
python verifier_connexion_db.py
```
✅ Si connecté → Passer à l'étape 3  
❌ Si erreur → Lancer `python demarrer_mongodb.py`

### Étape 3 : Démarrer le marketplace
```bash
python demarrer_marketplace.py
```
Choisir **Option 1** → Le serveur démarre

### Étape 4 : Ouvrir dans le navigateur
```
http://localhost:8000/dashboard/marketplace/
```

## 🎨 Ce que vous allez voir

### Page d'accueil moderne
- **Header bleu** avec gradient professionnel
- **6 cartes sources** cliquables (BRVM, WorldBank, IMF, ONU, BAD, Publications)
- **Stats en temps réel** : Nombre d'observations, dernière mise à jour
- **Packages tarifaires** : Gratuit, Pro (5K), Premium (15K), Enterprise (50K)

### Workflow en 4 étapes
1. **Sélectionner source** : Cliquer sur carte BRVM (ou autre)
2. **Configurer filtres** : Choisir période (7j/30j/60j/1an/tout) + format (CSV/JSON/Excel)
3. **Prévisualiser** : Voir échantillon + nombre d'observations + taille fichier
4. **Télécharger** : Bouton vert → Fichier téléchargé instantanément

## 📥 Exemples de téléchargement

### BRVM 60 jours (CSV)
```
Source,Dataset,Key,Date,Value,Open,High,Low,Close,Volume,RSI,Beta,...
BRVM,STOCK_PRICE,BOABF,2026-01-07,4563.17,4490,4570,4467,4563,40394,70.0,1.13,...
BRVM,STOCK_PRICE,BOAC,2026-01-07,6850.00,6800,6900,6750,6850,12500,55.2,0.98,...
...
```

### World Bank (JSON)
```json
[
  {
    "source": "WorldBank",
    "dataset": "INDICATOR",
    "key": "SP.POP.TOTL",
    "date": "2025-12-01",
    "value": 26378275,
    "attributes": {
      "country": "CIV",
      "indicator_name": "Population, total"
    }
  }
]
```

## 🚀 Fonctionnalités avancées

### API Documentation
```
http://localhost:8000/dashboard/marketplace/api-docs/
```
Exemples de code : Python, JavaScript, R

### Tester avec Python
```python
import requests

# Télécharger BRVM 30 jours
response = requests.get(
    'http://localhost:8000/dashboard/marketplace/download/',
    params={
        'source': 'BRVM',
        'period': '30d',
        'format': 'csv'
    }
)

with open('brvm_data.csv', 'wb') as f:
    f.write(response.content)

print("✅ Données téléchargées!")
```

## 💎 Packages & Prix

| Package | Prix | Période | Formats | Téléchargements |
|---------|------|---------|---------|-----------------|
| **Gratuit** | 0 FCFA | 7 jours | CSV | 10/mois |
| **Pro** | 5,000/mois | 60 jours | CSV, JSON, Excel | Illimité |
| **Premium** | 15,000/mois | Tout | Tous | Illimité + API |
| **Enterprise** | 50,000/mois | Tout | Tous + SQL | API haute fréquence |

## 🧪 Tests automatiques

```bash
python test_marketplace.py
```

Tests exécutés :
- ✅ Page marketplace chargée
- ✅ Statistiques affichées
- ✅ Préparation téléchargement
- ✅ Export CSV/JSON/Excel
- ✅ Documentation API
- ✅ Toutes les sources (6/6)
- ✅ Toutes les périodes (5/5)

## 📱 Responsive Design

Le marketplace s'adapte automatiquement :
- 💻 **Desktop** : Grille 3 colonnes
- 📱 **Tablette** : Grille 2 colonnes
- 📱 **Mobile** : Grille 1 colonne

## 🎓 Ressources

### Documentation complète
```
MARKETPLACE_DOCUMENTATION.md
```
40+ pages avec exemples, FAQ, architecture

### Scripts utiles
- `demarrer_marketplace.py` : Menu interactif
- `test_marketplace.py` : Tests automatiques
- `collecter_quotidien_intelligent.py` : Collecte BRVM

## ❓ Problèmes courants

### Erreur "Module openpyxl not found"
```bash
pip install openpyxl
```

### Erreur "MongoDB connection failed"
```bash
python demarrer_mongodb.py
```

### Aucune donnée BRVM
```bash
python collecter_quotidien_intelligent.py
```

### Port 8000 déjà utilisé
```bash
python manage.py runserver 8001
# Puis ouvrir: http://localhost:8001/dashboard/marketplace/
```

## 🎯 Prochaines étapes

### Semaine 1 : Authentification
- [ ] Système de comptes utilisateurs
- [ ] Login/Logout
- [ ] Profils utilisateurs

### Semaine 2 : Paiement
- [ ] Intégration Stripe/Paystack
- [ ] Abonnements mensuels
- [ ] Factures automatiques

### Semaine 3 : Analytics
- [ ] Tracking téléchargements
- [ ] Dashboard utilisateur
- [ ] Métriques d'utilisation

## 💡 Conseils

1. **Commencez simple** : Package Gratuit → Testez → Upgradez
2. **Utilisez l'API** : Plus flexible que téléchargements manuels
3. **Automatisez** : Scripts Python pour téléchargements quotidiens
4. **Partagez** : Invitez vos collègues à tester

## 📞 Support

- 📧 **Email** : support@votre-plateforme.com
- 💬 **Discord** : [Communauté]
- 📱 **WhatsApp** : +225 XX XX XX XX XX

---

**Créé avec ❤️ pour aider 10,000+ investisseurs BRVM** 🚀

**Objectif** : Battre Sika Finance (15K clients) et RichBourse (8K clients) avec la meilleure plateforme de données d'Afrique de l'Ouest !

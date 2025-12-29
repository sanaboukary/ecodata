# 🎯 Dashboard BRVM - Système de Filtrage par Action

## ✨ Nouvelles Fonctionnalités

### 🔍 Analyse d'Action Individuelle

Le dashboard BRVM dispose maintenant d'un système complet de filtrage et d'analyse par action permettant d'examiner en détail n'importe quelle action cotée à la BRVM.

---

## 🚀 Utilisation

### 1️⃣ Accéder au Dashboard BRVM

```
http://localhost:8000/dashboards/brvm/
```

### 2️⃣ Sélectionner une Action

En haut du dashboard, utilisez le **sélecteur d'action** :

```
🔍 Analyser une Action Spécifique
[-- Sélectionner une action --] ↻ Réinitialiser
```

Le sélecteur affiche **toutes les actions** disponibles avec :
- **Symbole** (ex: BOAC, SGBC, TTLS...)
- **Nom complet** (ex: BOA CI, Société Générale...)
- **Secteur** (Banque, Télécommunications, Assurance...)

### 3️⃣ Observer les Détails

Une fois l'action sélectionnée, un **panneau détaillé** s'affiche avec :

#### 📊 En-tête de l'Action
- Nom complet de l'entreprise
- Symbole boursier
- Secteur d'activité
- Pays
- **Prix actuel** en gros caractères
- **Variation du jour** (en vert si positif, rouge si négatif)

#### 💼 Indicateurs Financiers (Grille 4x3)
1. **Capitalisation** - Capitalisation boursière totale
2. **P/E Ratio** - Price/Earnings (valorisation)
3. **P/B Ratio** - Price/Book (actif net)
4. **Dividende** - Rendement du dividende (%)
5. **ROE** - Return on Equity (rentabilité)
6. **Beta** - Volatilité par rapport au marché
7. **Dette/Capitaux** - Levier financier
8. **Volume** - Volume de transactions du jour
9. **Volume Moy.** - Volume moyen sur 90 jours
10. **Max 90j** - Prix maximum sur 90 jours
11. **Min 90j** - Prix minimum sur 90 jours
12. **Prix Moyen** - Prix moyen sur 90 jours
13. **Variation 90j** - Performance sur 90 jours (mise en évidence)

#### 📈 Graphiques Interactifs

**Graphique 1: Évolution du Cours (90 derniers jours)**
- Ligne principale : Prix de clôture (or)
- Ligne pointillée verte : Plus hauts
- Ligne pointillée rouge : Plus bas
- Tooltips interactifs au survol
- Remplissage dégradé sous la courbe

**Graphique 2: Volume de Transactions**
- Barres colorées par direction (vert = hausse, rouge = baisse)
- Affichage du volume quotidien
- Permet d'identifier les journées à forte activité

### 4️⃣ Réinitialiser

Cliquez sur **↻ Réinitialiser** pour :
- Fermer le panneau de détails
- Réinitialiser le sélecteur
- Détruire les graphiques Chart.js (libération mémoire)

---

## 🔧 Architecture Technique

### Backend (Django)

#### Nouvelle API REST: `brvm_stock_detail_api`

**Endpoint:**
```
GET /api/brvm/stock/<symbol>/
```

**Exemple:**
```bash
curl http://localhost:8000/api/brvm/stock/BOAC/
```

**Réponse JSON:**
```json
{
  "stock_info": {
    "symbol": "BOAC",
    "name": "BOA CI",
    "sector": "Banque",
    "country": "CI",
    "current_price": 4539.87,
    "last_update": "2025-11-17"
  },
  "financial_metrics": {
    "day_change_pct": 1.54,
    "market_cap": 22773649512.42,
    "pe_ratio": 15.51,
    "pb_ratio": 1.95,
    "dividend_yield": 5.29,
    "roe": 9.84,
    "debt_to_equity": 0.34,
    "beta": 0.83,
    "volume": 45701,
    "avg_volume": 30865
  },
  "statistics": {
    "max_90d": 7922.98,
    "min_90d": 3991.07,
    "avg_price": 5804.60,
    "avg_volume": 30865.47,
    "total_observations": 38,
    "period_change_pct": -6.95
  },
  "chart_data": {
    "dates": ["2025-10-13", "2025-10-14", ...],
    "prices": [4879.06, 5755.94, ...],
    "volumes": [25000, 32000, ...],
    "highs": [4950.00, 5800.00, ...],
    "lows": [4800.00, 5700.00, ...]
  }
}
```

#### Modifications dans `dashboard/views.py`

```python
@require_http_methods(["GET"])
def brvm_stock_detail_api(request, symbol):
    """API JSON pour les détails et historique d'une action BRVM"""
    _, db = get_mongo_db()
    
    # Récupération de 90 jours d'historique
    historical_data = list(db.curated_observations.find(
        {'source': 'BRVM', 'key': symbol},
        sort=[('ts', -1)]
    ).limit(90))
    
    # ... Traitement et calculs ...
    
    return JsonResponse({...})
```

#### Modifications dans `dashboard/urls.py`

```python
from .views import brvm_stock_detail_api

urlpatterns = [
    # ...
    path('api/brvm/stock/<str:symbol>/', brvm_stock_detail_api, name='brvm_stock_detail_api'),
]
```

#### Modifications dans `dashboard_brvm` (vue)

Ajout de `all_stocks` au contexte :

```python
# Liste complète des actions pour le sélecteur
all_stocks_list = []
for stock in sorted(latest_stocks, key=lambda x: x.get('key', '')):
    attrs = stock.get('attrs', {})
    all_stocks_list.append({
        'symbol': stock.get('key'),
        'name': attrs.get('name', stock.get('key')),
        'sector': attrs.get('sector', 'N/A'),
        'country': attrs.get('country', 'N/A')
    })

return render(request, "dashboard/dashboard_brvm.html", {
    # ...
    "all_stocks": all_stocks_list,
})
```

### Frontend (HTML/JavaScript)

#### Structure HTML

```html
<!-- Filtre par action -->
<div class="action-filter-container">
  <div class="filter-header">
    <div class="filter-title">🔍 Analyser une Action Spécifique</div>
    <div class="stock-selector">
      <select id="stockSelector">
        <option value="">-- Sélectionner une action --</option>
        {% for stock in all_stocks %}
        <option value="{{ stock.symbol }}" 
                data-name="{{ stock.name }}"
                data-sector="{{ stock.sector }}"
                data-country="{{ stock.country }}">
          {{ stock.symbol }} - {{ stock.name }} ({{ stock.sector }})
        </option>
        {% endfor %}
      </select>
    </div>
    <button class="reset-filter-btn" onclick="resetFilter()">↻ Réinitialiser</button>
  </div>
  
  <!-- Panneau de détails -->
  <div id="stockDetailsPanel" class="stock-details-panel">
    <div class="loading-spinner" id="loadingIndicator">Chargement...</div>
    
    <div id="stockContent" style="display: none;">
      <!-- En-tête avec prix -->
      <div class="stock-header">...</div>
      
      <!-- Grille d'indicateurs -->
      <div class="indicators-grid" id="indicatorsGrid"></div>
      
      <!-- Graphiques -->
      <canvas id="stockHistoricalChart"></canvas>
      <canvas id="stockVolumeChart"></canvas>
    </div>
  </div>
</div>
```

#### JavaScript Principal

```javascript
// Variables globales pour les graphiques
let stockChart = null;
let volumeChart = null;

// Event listener sur le sélecteur
document.getElementById('stockSelector')?.addEventListener('change', function() {
  const symbol = this.value;
  if (symbol) {
    loadStockDetails(symbol);
  } else {
    resetFilter();
  }
});

// Chargement AJAX des détails
async function loadStockDetails(symbol) {
  const panel = document.getElementById('stockDetailsPanel');
  const loading = document.getElementById('loadingIndicator');
  const content = document.getElementById('stockContent');
  
  panel.classList.add('active');
  loading.style.display = 'block';
  content.style.display = 'none';
  
  try {
    const response = await fetch(`/api/brvm/stock/${symbol}/`);
    const data = await response.json();
    
    displayStockDetails(data);
    
    loading.style.display = 'none';
    content.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
  } catch (error) {
    console.error('Erreur:', error);
    loading.innerHTML = '❌ Erreur de chargement';
  }
}

// Affichage des données
function displayStockDetails(data) {
  // Mise à jour de l'en-tête
  document.getElementById('stockName').textContent = data.stock_info.name;
  // ... autres éléments ...
  
  // Création des graphiques Chart.js
  createStockChart(data.chart_data);
  createVolumeChart(data.chart_data);
}

// Réinitialisation
function resetFilter() {
  document.getElementById('stockSelector').value = '';
  document.getElementById('stockDetailsPanel').classList.remove('active');
  
  if (stockChart) stockChart.destroy();
  if (volumeChart) volumeChart.destroy();
}
```

---

## 📊 Données Disponibles

### Actions BRVM (50 actions)

Le système gère **47 vraies actions BRVM** réparties sur **8 pays** :

- **Bénin (BEN)**: BOA BEN, ONTBF...
- **Burkina Faso (BF)**: BOABF, CBIBF...
- **Côte d'Ivoire (CI)**: BOAC, SGBC, BIDC...
- **Guinée-Bissau (GW)**: BOAGW...
- **Mali (ML)**: BOAM, CBNK...
- **Niger (NE)**: BOAN, BSIC...
- **Sénégal (SN)**: SGBS, CBAO, SONATEL...
- **Togo (TG)**: BOATG, ETIT...

### Secteurs

- Banque (principal)
- Assurance
- Télécommunications
- Industrie
- Distribution
- Agro-alimentaire
- Immobilier
- Services financiers

---

## 🎨 Design & UX

### Thème Visuel
- **Couleur principale**: Or (#C9A961, #FFD700)
- **Arrière-plan**: Dégradé bleu foncé (#1a1a2e → #16213e)
- **Cartes**: Verre dépoli (backdrop-filter: blur)
- **Effets**: Transitions fluides, ombres portées au survol

### Responsive
- **Desktop**: Grille 4 colonnes d'indicateurs
- **Tablet**: Grille 2 colonnes
- **Mobile**: Grille 1 colonne (empilée)

### Performance
- **Lazy loading**: Les graphiques ne sont créés qu'à la sélection
- **Destruction propre**: Les instances Chart.js sont détruites lors du changement
- **Cache**: Les données restent en mémoire pendant la session
- **Smooth scroll**: Animation douce vers le panneau de détails

---

## 🧪 Tests

### Script de Test Automatique

Fichier: `test_brvm_filter.py`

```bash
python test_brvm_filter.py
```

**Tests effectués:**
1. ✓ Liste des actions disponibles (API `/api/brvm/stocks/`)
2. ✓ Détails d'une action spécifique (API `/api/brvm/stock/BOAC/`)
3. ✓ Présence des composants HTML dans le dashboard

### Tests Manuels

1. **Navigation**
   - Ouvrir `http://localhost:8000/dashboards/brvm/`
   - Vérifier l'affichage du sélecteur en haut

2. **Sélection d'action**
   - Sélectionner "BOAC - BOA CI (Banque)"
   - Vérifier l'apparition du panneau
   - Vérifier l'affichage du spinner de chargement

3. **Affichage des données**
   - Vérifier le prix actuel et la variation
   - Vérifier les 13 indicateurs financiers
   - Vérifier le graphique d'évolution (3 courbes)
   - Vérifier le graphique de volume (barres colorées)

4. **Interactivité**
   - Survoler les graphiques → Tooltips
   - Cliquer "Réinitialiser" → Fermeture du panneau
   - Changer d'action → Mise à jour instantanée

5. **Responsive**
   - Tester sur mobile (DevTools)
   - Vérifier la grille d'indicateurs (1 colonne)
   - Vérifier les graphiques (hauteur adaptée)

---

## 🐛 Debugging

### Erreur 404 sur l'API

```bash
# Vérifier que l'URL est correcte
curl http://localhost:8000/api/brvm/stock/BOAC/

# Vérifier les URLs Django
python manage.py show_urls | grep brvm
```

### Action non trouvée

```bash
# Lister les actions disponibles
curl http://localhost:8000/api/brvm/stocks/ | jq '.items[].symbol'
```

### Graphiques ne s'affichent pas

```javascript
// Ouvrir la console du navigateur (F12)
// Vérifier les erreurs Chart.js

// Vérifier que Chart.js est chargé
console.log(Chart.version); // Devrait afficher "3.9.1"

// Vérifier que les canvas existent
console.log(document.getElementById('stockHistoricalChart'));
console.log(document.getElementById('stockVolumeChart'));
```

### Données manquantes

```python
# Dans Django shell
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

# Vérifier une action spécifique
count = db.curated_observations.count_documents({'source': 'BRVM', 'key': 'BOAC'})
print(f"Observations pour BOAC: {count}")

# Voir un exemple
sample = db.curated_observations.find_one({'source': 'BRVM', 'key': 'BOAC'})
print(sample)
```

---

## 📈 Améliorations Futures

### Court Terme
- [ ] Comparaison de 2 actions côte à côte
- [ ] Export des données en CSV/Excel
- [ ] Signets/Favoris pour actions suivies
- [ ] Alertes de prix (email/notifications)

### Moyen Terme
- [ ] Analyse technique (RSI, MACD, Bollinger)
- [ ] Backtesting de stratégies
- [ ] Screener multi-critères avancé
- [ ] Actualités BRVM par action (scraping)

### Long Terme
- [ ] Machine Learning - Prédiction de prix
- [ ] Sentiment analysis (Twitter, news)
- [ ] Portfolio virtuel avec suivi P&L
- [ ] API WebSocket pour temps réel

---

## 🔗 Ressources

### Documentation
- [Chart.js 3.x](https://www.chartjs.org/docs/latest/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [MongoDB Aggregation](https://www.mongodb.com/docs/manual/aggregation/)

### Fichiers Modifiés
- `dashboard/views.py` - Nouvelle API `brvm_stock_detail_api`
- `dashboard/urls.py` - Route `/api/brvm/stock/<symbol>/`
- `templates/dashboard/dashboard_brvm.html` - Sélecteur + Panneau + Graphiques
- `test_brvm_filter.py` - Script de test automatique

### Support
- Issues GitHub: [Créer une issue](#)
- Documentation projet: `PROJECT_STRUCTURE.md`
- Changelog: `CHANGELOG.md`

---

**Créé le**: 17 novembre 2025  
**Version**: 1.0  
**Auteur**: GitHub Copilot  
**Licence**: MIT

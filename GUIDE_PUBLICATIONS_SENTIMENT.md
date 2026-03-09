"""
📰🔬 GUIDE COMPLET - SYSTÈME DE PUBLICATIONS & SENTIMENT BRVM
===============================================================

## 🎯 OBJECTIF
Collecter et analyser toutes les publications officielles BRVM pour :
- Anticiper mouvements de marché
- Générer signaux trading intelligents
- Analyse de sentiment en temps réel

## 📂 CATÉGORIES COLLECTÉES

### 1️⃣ BULLETIN_OFFICIEL (Quotidien)
- Bulletins de la cote BRVM
- Résumés des séances de trading
- URL : https://www.brvm.org/fr/bulletins-officiels-de-la-cote

### 2️⃣ COMMUNIQUE_RESULTATS (Haute priorité)
- Résultats trimestriels/annuels
- Chiffres d'affaires
- Impact : FORT sur cours
- Sentiment : Positif/Négatif selon performance

### 3️⃣ COMMUNIQUE_DIVIDENDE (Haute priorité)
- Annonces de dividendes
- Dates de détachement
- Montants distribués
- Impact : FORT (hausse attendue)

### 4️⃣ COMMUNIQUE_AG (Priorité moyenne)
- Convocations Assemblées Générales
- Ordres du jour
- Impact : MOYEN

### 5️⃣ RAPPORT_SOCIETE (Annuel)
- Rapports financiers complets
- États financiers audités
- Impact : FORT (analyse fondamentale)

### 6️⃣ ACTUALITE
- News BRVM générales
- Événements de marché
- Impact : VARIABLE

### 7️⃣ COMMUNIQUE_SUSPENSION
- Suspensions de cotation
- Reprises de cotation
- Impact : TRÈS FORT (alerte rouge)

## 🚀 UTILISATION

### Collecte Manuelle
```cmd
# Collecte COMPLÈTE (toutes catégories)
COLLECTER_PUBLICATIONS_BRVM.cmd → Option 1

# Collecte TEST (30 par catégorie)
COLLECTER_PUBLICATIONS_BRVM.cmd → Option 2

# Une catégorie spécifique
COLLECTER_PUBLICATIONS_BRVM.cmd → Option 3
→ Entrer : BULLETIN_OFFICIEL
```

### Collecte Automatique Airflow
```bash
# Activer DAG dans Airflow Web UI
http://localhost:8080/
→ DAG : brvm_publications_quotidien
→ Schedule : 18h00 tous les jours

# Lancer manuellement
airflow dags trigger brvm_publications_quotidien
```

### Analyse de Sentiment
```cmd
# Analyser 30 derniers jours
ANALYSER_SENTIMENT.cmd → Option 1

# Analyser 7 derniers jours
ANALYSER_SENTIMENT.cmd → Option 2

# Score par émetteur
ANALYSER_SENTIMENT.cmd → Option 3
→ Entrer : SNTS
```

### Intégration Python
```python
from analyser_sentiment_publications import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Analyser toutes publications
analyzer.analyze_all_publications(days_back=30)

# Score par émetteur
result = analyzer.get_sentiment_by_emetteur('SNTS')
print(f"Signal : {result['signal']}")  # BUY/HOLD/SELL
print(f"Score  : {result['avg_score']}")
```

## 📊 SCHÉMA MONGODB

```javascript
{
  source: 'BRVM_PUBLICATION',
  dataset: 'COMMUNIQUE_RESULTATS',  // Catégorie
  key: 'SNTS - Résultats T4 2025',   // Titre
  ts: '2025-12-15',                  // Date publication
  value: 1,                          // Compteur
  attrs: {
    // 📄 Métadonnées publication
    url: 'https://www.brvm.org/...',
    emetteur: 'SNTS',
    category: 'COMMUNIQUE_RESULTATS',
    file_type: 'PDF',
    hash: 'a1b2c3d4e5f6',
    description: 'Sonatel publie ses résultats...',
    scraped_at: '2025-12-15T18:30:00',
    
    // 💡 Analyse de sentiment (ajouté par analyser_sentiment_publications.py)
    sentiment: 'positive',           // positive/negative/neutral
    sentiment_score: 0.75,           // -1.0 à +1.0
    sentiment_confidence: 0.85,      // 0.0 à 1.0
    financial_events: [              // Événements détectés
      'RESULTATS',
      'DIVIDENDE'
    ],
    impact_level: 'HIGH',            // HIGH/MEDIUM/LOW
    keywords: [                      // Mots-clés pertinents
      'hausse',
      'croissance',
      'bénéfice',
      'dividende'
    ],
    analyzed_at: '2025-12-15T19:00:00',
    
    // ✅ Qualité
    data_quality: 'REAL_SCRAPER'
  }
}
```

## 🎯 SIGNAUX TRADING GÉNÉRÉS

### Score de Sentiment → Signal
```
Score >  0.5  → BUY  (sentiment très positif)
Score > -0.5  → HOLD (sentiment neutre)
Score < -0.5  → SELL (sentiment négatif)
```

### Impact → Urgence
```
HIGH   → Réaction immédiate (résultats, dividendes, suspension)
MEDIUM → Surveillance (AG, nominations)
LOW    → Information générale
```

### Exemples Concrets
```
📈 BUY Signal :
   Émetteur : SNTS
   Publication : "Sonatel : Résultats annuels en hausse de 15%"
   Sentiment : positive (score: 0.85)
   Événements : RESULTATS, DIVIDENDE
   Impact : HIGH
   → Signal : BUY
   
📉 SELL Signal :
   Émetteur : BICC
   Publication : "BICICI : Perte nette de 2 milliards"
   Sentiment : negative (score: -0.75)
   Événements : RESULTATS
   Impact : HIGH
   → Signal : SELL
   
⏸️ HOLD Signal :
   Émetteur : BOABF
   Publication : "BOA : Convocation AG ordinaire"
   Sentiment : neutral (score: 0.1)
   Événements : AG
   Impact : MEDIUM
   → Signal : HOLD
```

## 📱 DASHBOARD WEB

### Page Publications
```
http://127.0.0.1:8000/brvm/publications/

Filtres :
- Catégorie (Bulletins, Communiqués, Rapports)
- Date (du/au)
- Émetteur

Affichage :
- Liste publications avec sentiment 😊😐😞
- Graphique publications/mois
- Export CSV/JSON
```

### API REST
```bash
# Liste publications
curl http://127.0.0.1:8000/api/brvm/publications/

# Export CSV
curl http://127.0.0.1:8000/api/brvm/publications/export/?format=csv

# Export JSON
curl http://127.0.0.1:8000/api/brvm/publications/export/?format=json
```

## 🔄 WORKFLOW COMPLET

### 1. Collecte Quotidienne (Automatique)
```
18h00 : DAG Airflow démarre
18h05 : Scraping toutes catégories (50 par catégorie)
18h15 : Insertion MongoDB
18h20 : Vérification (alerte si 0 publications)
```

### 2. Analyse Sentiment (Manuelle ou Auto)
```
Option A (Manuelle) :
   ANALYSER_SENTIMENT.cmd → Option 1

Option B (Automatique - à configurer) :
   Ajouter task dans DAG Airflow après collecte
```

### 3. Génération Signaux Trading
```python
# Dans votre stratégie de trading
from analyser_sentiment_publications import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Top 10 actions BRVM
tickers = ['SNTS', 'BOABF', 'BICC', 'ECOC', 'SGBC', 
           'NSBC', 'TTLC', 'SIBC', 'PALC', 'SLBC']

signals = {}
for ticker in tickers:
    result = analyzer.get_sentiment_by_emetteur(ticker)
    signals[ticker] = result['signal']

print(signals)
# {'SNTS': 'BUY', 'BOABF': 'HOLD', 'BICC': 'SELL', ...}
```

### 4. Intégration Stratégie Trading
```python
# dashboard/correlation_engine.py (à modifier)

def get_enhanced_recommendations(ticker):
    """Recommandations enrichies avec sentiment"""
    
    # 1. Analyse technique (existant)
    technical_score = calculate_technical_score(ticker)
    
    # 2. Analyse fondamentale (existant)
    fundamental_score = calculate_fundamental_score(ticker)
    
    # 3. Analyse sentiment (NOUVEAU)
    from analyser_sentiment_publications import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    sentiment_result = analyzer.get_sentiment_by_emetteur(ticker)
    sentiment_score = sentiment_result['avg_score']
    
    # 4. Score final pondéré
    final_score = (
        0.4 * technical_score +
        0.4 * fundamental_score +
        0.2 * sentiment_score  # 20% sentiment
    )
    
    # 5. Recommandation
    if final_score > 0.6:
        return 'BUY'
    elif final_score < -0.6:
        return 'SELL'
    else:
        return 'HOLD'
```

## ⚙️ CONFIGURATION

### Fréquence Collecte
```python
# airflow/dags/brvm_publications_quotidien.py
schedule_interval='0 18 * * *'  # 18h00 quotidien

# Modifier à :
schedule_interval='0 */6 * * *'  # Toutes les 6h
schedule_interval='0 9,18 * * *' # 9h et 18h
```

### Limite Publications
```python
# collecter_publications_brvm_intelligent.py
collector.collect_all(limit_per_category=50)  # 50 par défaut

# Modifier à :
collector.collect_all(limit_per_category=100)  # Plus de publications
collector.collect_all(limit_per_category=None) # TOUTES (lent)
```

### Dictionnaire Sentiment
```python
# analyser_sentiment_publications.py
SENTIMENT_WORDS = {
    'positive': [
        # Ajouter vos mots
        'expansion', 'innovation', 'partenariat'
    ],
    'negative': [
        # Ajouter vos mots
        'contentieux', 'amende', 'sanction'
    ]
}
```

## 🐛 DÉPANNAGE

### Aucune publication collectée
```bash
# Vérifier connectivité BRVM.org
curl -I https://www.brvm.org/

# Tester scraper directement
python collecter_publications_brvm_intelligent.py --category BULLETIN_OFFICIEL

# Vérifier MongoDB
python verifier_connexion_db.py
```

### Sentiment toujours neutre
```bash
# Vérifier publications ont du texte
python -c "
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()
pub = db.curated_observations.find_one({'source': 'BRVM_PUBLICATION'})
print(pub.get('key'))
print(pub.get('attrs', {}).get('description'))
"

# Enrichir avec descriptions si vides
```

### Airflow DAG n'apparaît pas
```bash
# Vérifier DAG dans dossier
ls airflow/dags/brvm_publications_quotidien.py

# Tester syntaxe
python airflow/dags/brvm_publications_quotidien.py

# Redémarrer Airflow
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *airflow*"
start_airflow_background.bat
```

## 📈 MÉTRIQUES DE SUCCÈS

### KPIs Collecte
- Publications/jour : > 20
- Catégories actives : 5-7 (sur 7)
- Taux de duplication : < 20%

### KPIs Sentiment
- Publications analysées : 100%
- Confiance moyenne : > 0.6
- Impact HIGH : 10-20% des publications

### KPIs Trading
- Signaux générés : 1-3/jour
- Précision signaux : > 60% (à backtester)
- Corrélation sentiment/cours : > 0.4

## 🔗 RESSOURCES

### Scripts
- `collecter_publications_brvm_intelligent.py` : Scraper multi-catégories
- `analyser_sentiment_publications.py` : Analyseur de sentiment
- `COLLECTER_PUBLICATIONS_BRVM.cmd` : Interface collecte
- `ANALYSER_SENTIMENT.cmd` : Interface analyse

### DAGs Airflow
- `airflow/dags/brvm_publications_quotidien.py` : Collecte automatique

### Dashboard
- http://127.0.0.1:8000/brvm/publications/
- http://127.0.0.1:8000/api/brvm/publications/

### Documentation
- Ce fichier : `GUIDE_PUBLICATIONS_SENTIMENT.md`

---

✅ **Système opérationnel !**
🚀 Lancez : `COLLECTER_PUBLICATIONS_BRVM.cmd`
📊 Puis : `ANALYSER_SENTIMENT.cmd`
🔍 Vérifiez : http://127.0.0.1:8000/brvm/publications/

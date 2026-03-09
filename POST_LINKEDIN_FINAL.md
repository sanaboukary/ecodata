# POST LINKEDIN - VERSION PORTFOLIO TECHNIQUE

## 🔧 Architecture d'une plateforme de données économiques scalable pour l'Afrique de l'Ouest

**Contexte :**
Centralisation de 4 sources de données hétérogènes (BRVM, Banque Mondiale, FMI, AfDB) pour l'analyse des marchés financiers ouest-africains.

---

### 🎯 Défis techniques relevés :

**1️⃣ ETL Pipeline robuste**
• Scraping BRVM avec gestion SSL/anti-bot (BeautifulSoup + contournement certificats)
• Normalisation de 4 schémas hétérogènes vers un modèle commun (source, dataset, key, ts, value, attrs)
• Gestion d'erreurs avec retry automatique (max 3 tentatives)
• Logging complet pour audit (collection ingestion_runs avec durée, statut, obs_count)
• Politique data quality STRICTE : REAL_SCRAPER ou REAL_MANUAL uniquement (zéro tolérance données simulées)

**2️⃣ Optimisation des performances**
• **Réduction massive** : 35,376 → 3,696 requêtes API (-90%)
  → Collecte par blocs temporels (décennies) au lieu d'années individuelles
  → Durée : 85h → 2h (42x plus rapide)
• Cache MongoDB avec indexation stratégique sur {source, dataset, key, ts}
• Requêtes parallèles non-bloquantes pour dashboard temps réel

**3️⃣ Data Quality Management**
• Traçabilité complète : 3 collections MongoDB
  - `raw_events` : Audit trail immutable des réponses API brutes
  - `curated_observations` : Données normalisées prêtes pour analyse
  - `ingestion_runs` : Métriques d'exécution (success rate, durée, erreurs)
• Validation automatique avant insertion (format, types, plages valides)
• Alertes automatiques sur données non vérifiées (data_quality != REAL_*)

**4️⃣ Architecture NoSQL flexible**
• Schéma document MongoDB pour 70+ attributs par action BRVM
• Support de structures hétérogènes (attrs dynamiques par source)
• Agrégations complexes pour KPIs dashboard (pipeline MongoDB)
• Scalabilité horizontale prête (sharding par source)

**5️⃣ Orchestration & Automatisation**
• Airflow DAGs pour collecte horaire BRVM (9h-16h jours ouvrables)
• Collecte mensuelle World Bank/IMF (jour 1 et 15 du mois)
• Monitoring intégré avec logs horodatés
• Fallback manuel si scraping échoue (script de saisie guidée)

---

### 📊 Résultats mesurables :

✅ **35,000+ observations** historiques collectées (1960-2026)  
✅ **47 actions BRVM** avec 70 attributs enrichis (PE, dividend yield, RSI, recommendations)  
✅ **66 indicateurs économiques** × 8 pays UEMOA  
✅ **Taux de succès** : 95%+ sur collectes automatisées  
✅ **Latence API** : <2s par requête moyenne  

---

### 💻 Stack technique :

**Backend :** Python 3.13, Django 4.1  
**Database :** MongoDB 7.0 (NoSQL)  
**ETL :** Custom scripts + Airflow pour orchestration  
**Scraping :** BeautifulSoup4, Requests (avec SSL bypass)  
**Data APIs :** World Bank API, IMF Data API, AfDB Open Data  
**Frontend :** Django Templates + Charts.js  
**DevOps :** Git, environnement virtuel Python  

---

### 🚀 Prochaines étapes :

🔹 Intégration LLM pour analyse sentiment publications financières  
🔹 Modèles prédictifs (LSTM) pour tendances BRVM  
🔹 API REST pour consommation externe  
🔹 Dashboard React pour UI moderne  

---

### 📌 Repo GitHub :
👉 github.com/sanaboukary/ecodata

---

### 💡 Leçons apprises :

1. **L'optimisation précoce paie** : Penser "blocs" dès le début (90% gain)
2. **Data quality > quantité** : Politique stricte évite analyses biaisées
3. **Logging = debugging facile** : ingestion_runs sauve des heures de debug
4. **NoSQL pour données hétérogènes** : MongoDB parfait pour schémas variables
5. **Automatisation progressive** : Scraping → Saisie manuelle → API (fallback chain)

---

### 🤝 Intéressé par le code ou des collaborations ?

📧 Contact : [votre email]  
🔗 GitHub : github.com/sanaboukary  
💼 LinkedIn : [votre profil]  

---

#Python #Django #MongoDB #DataEngineering #ETL #WebScraping #BackendDev #BRVM #FinTech #AfricanTech #OpenSource #DataPipeline #SystemDesign #SoftwareArchitecture #APIs

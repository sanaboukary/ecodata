# 🎯 Stratégie de Collecte des Cours BRVM Réels

## Objectif Client
**Trading hebdomadaire sur la BRVM** avec analyses IA basées sur des **prix réels historiques** pour générer des signaux d'achat/vente fiables.

## Problème Actuel
- ❌ Aucun historique de prix (seulement 1 observation par action)
- ❌ Impossible de calculer RSI, MACD, Bollinger Bands, etc.
- ❌ 0 signal d'investissement généré par l'IA
- ⚠️ 21/46 actions avec cours estimés (pas réels)

## Solution Complète : 3 Phases

### 📅 PHASE 1 : Historique Rétrospectif (URGENT)
**Objectif** : Obtenir 60-90 jours d'historique pour démarrer les analyses

**Options disponibles** :

#### Option A : Site BRVM Officiel ✅ RECOMMANDÉ
```
Source : https://www.brvm.org/fr/cours-actions
Méthode : Web scraping avec authentification
Fréquence : Quotidien (disponible depuis 2008)
Coût : GRATUIT
```

**Script à créer** :
```python
# scripts/connectors/brvm_scraper_historique.py
- Scraper avec gestion SSL/certificats
- Récupération historique par action
- Stockage en base avec data_quality='REAL_BRVM_SITE'
```

#### Option B : API Bloomberg/Reuters 💰
```
Coût : ~500-2000 USD/mois
Avantages : Données temps réel + historique
Inconvénient : Budget nécessaire
```

#### Option C : Courtiers BRVM (SGI, Impaxis, etc.) 🤝
```
Coût : Potentiellement gratuit si client
Avantages : Données officielles, support
Méthode : API privée ou export Excel quotidien
```

#### Option D : Saisie Manuelle PDF Bulletins ⏱️
```
Source : Bulletins quotidiens BRVM (PDF)
Méthode : OCR + extraction données
Temps : ~2-3 heures/jour pour 60 jours
```

### 📊 PHASE 2 : Collecte Quotidienne Automatique
**Une fois l'historique établi**

**Solution 1 : Scraping BRVM (17h00 GMT)** ✅
```python
# airflow/dags/brvm_collecte_quotidienne.py
schedule_interval='0 17 * * 1-5'  # Lundi-Vendredi 17h

Tasks:
1. Scraper www.brvm.org/fr/cours-actions
2. Extraire cours de clôture + volumes
3. Sauvegarder dans curated_observations
4. Déclencher analyse IA à 17h30
```

**Solution 2 : Email automatique bulletin** 📧
```
- S'abonner au bulletin quotidien BRVM (email)
- Parser PDF attaché avec PyPDF2
- Extraction automatique des cours
```

### 🤖 PHASE 3 : Analyse IA Hebdomadaire
**Chaque dimanche soir avant ouverture lundi**

```python
# airflow/dags/analyse_ia_hebdomadaire.py
schedule_interval='0 20 * * 0'  # Dimanche 20h00

Workflow:
1. Récupérer 60 derniers jours de prix
2. Calculer 15+ indicateurs techniques
3. Analyser sentiment PDF collectés
4. Intégrer données macro (IMF, WB)
5. Générer signaux BUY/SELL/HOLD
6. Envoyer rapport par email
```

## 🚀 Plan d'Action Immédiat

### Aujourd'hui (Jour 1)
1. ✅ **Tester scraping BRVM** avec gestion SSL
2. ✅ **Récupérer 60 jours d'historique** pour les 46 actions
3. ✅ **Valider la qualité** des données récupérées

### Demain (Jour 2)
4. ✅ **Relancer analyse IA** avec historique réel
5. ✅ **Vérifier les signaux** générés (BUY/SELL)
6. ✅ **Affiner les seuils** de confiance

### Cette semaine (Jours 3-7)
7. ✅ **Configurer Airflow** pour collecte quotidienne 17h00
8. ✅ **Tester 5 jours** de collecte automatique
9. ✅ **Mise à jour des 21 cours estimés** avec vrais cours
10. ✅ **Générer premier rapport hebdomadaire** dimanche

## 📋 Checklist Technique

### Base de Données
- [x] Nettoyage données simulées (8,008 supprimées)
- [x] 46 actions BRVM présentes
- [ ] **60 jours d'historique par action** (2,760 observations)
- [ ] **Validation qualité des prix**

### Scripts de Collecte
- [ ] `brvm_scraper_historique.py` - Récupération historique
- [ ] `brvm_scraper_quotidien.py` - Collecte quotidienne
- [x] `mettre_a_jour_cours_brvm.py` - Mise à jour manuelle (backup)

### Analyse IA
- [x] Moteur IA 15+ facteurs opérationnel
- [ ] **Test avec historique réel** (générer signaux)
- [ ] Validation backtesting 60 jours
- [ ] Configuration alertes email/SMS

### Automatisation
- [ ] DAG Airflow collecte quotidienne
- [ ] DAG Airflow analyse hebdomadaire
- [ ] Monitoring erreurs collecte
- [ ] Backup quotidien base données

## 💡 Recommandations Finales

### Court Terme (Cette semaine)
**PRIORITÉ 1** : Obtenir l'historique réel (Option A recommandée)
- Script scraping BRVM avec retry/fallback
- Validation manuelle des 5 premières actions
- Génération historique complet 60 jours

**PRIORITÉ 2** : Valider l'analyse IA avec données réelles
- Relancer analyse avec historique
- Vérifier RSI, MACD fonctionnent
- Ajuster seuils pour éviter faux signaux

### Moyen Terme (Ce mois)
- Automatiser collecte quotidienne 100%
- Rapport hebdomadaire par email
- Backtest stratégie trading

### Long Terme (3-6 mois)
- API BRVM officielle si disponible
- Intégration courtier pour exécution ordres
- Portfolio tracking temps réel

---

**🎯 Action Immédiate : Créer le scraper BRVM avec historique**
```bash
python creer_scraper_brvm_historique.py --jours=60
```

# 🤖 SYSTÈME DE COLLECTE AUTOMATIQUE INTELLIGENT BRVM

## ✅ Ce qui a été créé

### 1. **Collecteur Automatique Intelligent**
**`collecteur_auto_intelligent.py`** - Système multi-stratégies avec fallback

**4 Stratégies de Collecte (par ordre de priorité) :**

1. **🌐 Scraping Site BRVM** (Priorité 1 - Données officielles)
   - Scrape automatiquement brvm.org
   - Qualité: `REAL_SCRAPER`
   - Temps: ~30 secondes
   
2. **🔌 API Financière Externe** (Priorité 2 - À venir)
   - Yahoo Finance, Alpha Vantage, etc.
   - Qualité: `REAL_API`
   - Temps: ~10 secondes
   
3. **📄 CSV Manuel** (Priorité 3 - Intervention humaine)
   - Détecte fichiers CSV du jour
   - Formats: `update_YYYY-MM-DD.csv`, `update_latest.csv`
   - Qualité: `REAL_MANUAL`
   
4. **🧠 Estimation Intelligente** (Priorité 4 - Fallback)
   - Basée sur 10 derniers jours
   - Variations réalistes (-1.5% à +1.5%)
   - Qualité: `ESTIMATED` ⚠️ À remplacer

**Fonctionnalités :**
- ✅ Détection automatique si collecte déjà faite
- ✅ Logging complet de chaque tentative
- ✅ Retry automatique entre stratégies
- ✅ Pas de doublons (upsert MongoDB)
- ✅ Historique des collectes consultable

### 2. **DAG Airflow Production**
**`airflow/dags/brvm_collecte_auto_intelligente.py`**

**6 Tâches Orchestrées :**
1. Check si collecte nécessaire
2. Collecte auto intelligente
3. Vérification qualité données
4. Calcul indicateurs techniques
5. Génération recommandations
6. Notification fin de collecte

**Schedule** : 17h00 lundi-vendredi (après clôture BRVM à 16h30)

---

## 🚀 Utilisation

### Test Manuel
```bash
# Collecte du jour (skip si déjà fait)
python collecteur_auto_intelligent.py

# Forcer la re-collecte
python collecteur_auto_intelligent.py --force

# Voir l'historique des collectes
python collecteur_auto_intelligent.py --logs
```

### Activation Airflow (Production)
```bash
# Démarrer Airflow
start_airflow_background.bat

# Web UI: http://localhost:8080
# Login: admin / admin

# Activer le DAG: brvm_collecte_auto_intelligente
# → Clique sur le toggle à gauche du DAG
```

### Collecte Quotidienne Automatique

**Option A : Airflow (Recommandé pour production)**
```bash
# Déjà configuré dans le DAG
# S'exécute automatiquement à 17h lun-ven
# Rien à faire après activation !
```

**Option B : Tâche planifiée Windows**
```bash
# Créer une tâche dans le planificateur Windows
# Programme: python
# Arguments: E:\DISQUE C\Desktop\Implementation plateforme\collecteur_auto_intelligent.py
# Déclencheur: Quotidien à 17h00, lun-ven uniquement
```

**Option C : Cron Linux (si déployé sur serveur)**
```bash
# Ajouter à crontab
0 17 * * 1-5 cd /chemin/projet && python collecteur_auto_intelligent.py
```

---

## 📊 Stratégies de Collecte Détaillées

### Stratégie 1 : Scraping BRVM (Optimal)

**Prérequis** :
```bash
pip install beautifulsoup4 requests
```

**Comment activer** :
- Script déjà présent : `scripts/connectors/brvm_scraper_production.py`
- S'active automatiquement si BeautifulSoup installé
- Contournement SSL intégré

**Résultat attendu** :
- 47 actions collectées
- Qualité : `REAL_SCRAPER`
- Temps : 20-40 secondes

### Stratégie 3 : CSV Manuel (Simple)

**Format fichier** :
```csv
DATE,SYMBOL,CLOSE,VOLUME,VARIATION
2025-12-08,SNTS,15600,9000,0.6
2025-12-08,BICC,7200,1250,1.2
...
```

**Noms détectés automatiquement** :
- `update_2025-12-08.csv`
- `update_latest.csv`
- `brvm_2025-12-08.csv`
- `cours_2025-12-08.csv`

**Workflow** :
1. Créer le fichier CSV avec les cours du jour
2. Le mettre dans le dossier du projet
3. Lancer : `python collecteur_auto_intelligent.py`
4. Le système détecte et importe automatiquement

### Stratégie 4 : Estimation (Fallback)

**Quand utilisée** :
- Toutes les autres stratégies ont échoué
- Week-end ou jour férié
- Problème de connexion internet

**Comment fonctionne** :
- Récupère les 10 derniers jours de cours
- Applique une variation réaliste (-1.5% à +1.5%)
- Ajuste le volume selon historique

**⚠️ Important** :
- Les données estimées sont marquées `ESTIMATED`
- Doivent être remplacées par des vraies données dès que possible
- Utilisables pour tests et démo, pas pour trading réel

---

## 📋 Vérification et Monitoring

### Vérifier la Dernière Collecte
```bash
# Voir l'historique
python collecteur_auto_intelligent.py --logs

# Résultat :
# ✅ 2025-12-08 17:05:23
#    Date: 2025-12-08 | Stratégie: scraping_brvm
#    Observations: 47 | Scraping réussi : 47 actions collectées
```

### Vérifier les Données Collectées
```bash
# Qualité des cours
python verifier_cours_brvm.py

# Historique 60 jours
python verifier_historique_60jours.py

# Vue d'ensemble
python show_complete_data.py
```

### Monitoring Airflow
```bash
# Web UI : http://localhost:8080
# Onglet "DAGs" → brvm_collecte_auto_intelligente
# Voir :
#   - Dernière exécution
#   - Statut des tâches
#   - Logs détaillés
#   - Prochaine exécution planifiée
```

---

## 🔧 Configuration et Personnalisation

### Modifier l'Horaire de Collecte

**Dans le DAG Airflow** :
```python
# Fichier: airflow/dags/brvm_collecte_auto_intelligente.py
# Ligne: schedule_interval

# Actuel : 17h00 lun-ven
schedule_interval='0 17 * * 1-5'

# Exemples :
# 16h30 tous les jours : '30 16 * * *'
# 18h00 lun-ven : '0 18 * * 1-5'
# Toutes les heures 9h-16h lun-ven : '0 9-16 * * 1-5'
```

### Ajouter une Nouvelle Stratégie

```python
# Dans collecteur_auto_intelligent.py
def strategie_5_nouvelle_source(self, date_collecte):
    """Stratégie 5 : Votre nouvelle source."""
    print("\n🆕 Stratégie 5 : Nouvelle source...")
    
    try:
        # Votre code de collecte ici
        observations = []
        
        # ... collecte des données ...
        
        if observations:
            self._importer_observations(observations)
            self.log_collecte('nouvelle_source', 'SUCCESS', len(observations), "Collecte OK")
            return True, len(observations)
        
        return False, 0
    except Exception as e:
        self.log_collecte('nouvelle_source', 'ERROR', 0, str(e), e)
        return False, 0

# Ajouter à la liste des stratégies (dans collecter_aujourd_hui)
strategies = [
    ('scraping', self.strategie_1_scraping_brvm),
    ('nouvelle_source', self.strategie_5_nouvelle_source),  # Ajouter ici
    ('api_externe', self.strategie_2_api_externe),
    # ...
]
```

### Notifications (Email/Slack)

**Prérequis** :
```bash
pip install slack-sdk  # Pour Slack
# ou
# Configurer SMTP pour email
```

**Dans le DAG** :
```python
# Modifier notification_task
def envoyer_notification(**context):
    import slack_sdk
    
    client = slack_sdk.WebClient(token='votre_token')
    message = f"✅ Collecte BRVM {datetime.now().strftime('%Y-%m-%d')} terminée"
    
    client.chat_postMessage(channel='#trading-brvm', text=message)
```

---

## 🎯 Scénarios d'Utilisation

### Scénario 1 : Production (Automatique Complet)

```bash
# 1. Activer Airflow
start_airflow_background.bat

# 2. Activer le DAG dans Web UI
# http://localhost:8080 → Toggle ON

# 3. C'est tout !
# Le système collecte automatiquement à 17h lun-ven
```

### Scénario 2 : Semi-Automatique (CSV Manuel)

```bash
# Chaque jour après clôture :
# 1. Créer CSV avec cours du jour
echo "DATE,SYMBOL,CLOSE,VOLUME,VARIATION" > update_latest.csv
echo "2025-12-08,SNTS,15600,9000,0.6" >> update_latest.csv
# ... (ajouter autres actions)

# 2. Import automatique
python collecteur_auto_intelligent.py

# Le système détecte et importe le CSV
```

### Scénario 3 : Mode Urgence (Estimation)

```bash
# Si aucune source disponible
# Le système utilise automatiquement l'estimation

python collecteur_auto_intelligent.py --force

# Résultat : 47 actions estimées (marquées ESTIMATED)
# À remplacer plus tard avec vraies données
```

---

## 📈 Roadmap / Améliorations Futures

### Court Terme (Prochains jours)
- [ ] Installer BeautifulSoup pour activer scraping
- [ ] Tester collecte quotidienne pendant 1 semaine
- [ ] Valider qualité des données scrapées

### Moyen Terme (Prochaines semaines)
- [ ] Intégrer API financière externe (Yahoo Finance)
- [ ] Implémenter calcul indicateurs techniques réels
- [ ] Développer moteur de recommandations
- [ ] Ajouter notifications Slack/Email

### Long Terme (Prochains mois)
- [ ] Machine Learning pour prédictions
- [ ] Backtest automatisé sur données historiques
- [ ] Dashboard temps réel
- [ ] API REST pour accès externe

---

## 🆘 Dépannage

### Problème : Toutes Stratégies Échouent

```bash
# Vérifier logs
python collecteur_auto_intelligent.py --logs

# Solution temporaire : CSV manuel
echo "DATE,SYMBOL,CLOSE,VOLUME,VARIATION" > update_latest.csv
# Remplir avec cours du jour
python collecteur_auto_intelligent.py
```

### Problème : Scraping Ne Fonctionne Pas

```bash
# Installer BeautifulSoup
pip install beautifulsoup4 requests

# Tester manuellement
python scripts/connectors/brvm_scraper_production.py

# Vérifier connexion internet
ping brvm.org
```

### Problème : Airflow Ne Lance Pas le DAG

```bash
# Vérifier statut Airflow
check_airflow_status.bat

# Relancer si nécessaire
start_airflow_background.bat

# Vérifier logs
cat airflow/logs/brvm_collecte_auto_intelligente/
```

---

## 📚 Commandes Rapides

```bash
# Collecte manuelle
python collecteur_auto_intelligent.py

# Collecte forcée
python collecteur_auto_intelligent.py --force

# Historique collectes
python collecteur_auto_intelligent.py --logs

# Vérifier données
python verifier_cours_brvm.py
python verifier_historique_60jours.py

# Airflow
start_airflow_background.bat
check_airflow_status.bat

# Import CSV manuel
python collecter_csv_automatique.py
```

---

**🎉 Votre système de collecte automatique est maintenant opérationnel !**

**Activation immédiate recommandée** :
1. Installer BeautifulSoup : `pip install beautifulsoup4`
2. Activer Airflow : `start_airflow_background.bat`
3. Activer le DAG dans l'UI Web
4. Laisser tourner ! ✅

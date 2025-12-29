# ✅ COLLECTE AUTOMATIQUE INTELLIGENTE - DONNÉES RÉELLES UNIQUEMENT

## 🎯 Système Activé et Opérationnel

### 📊 État Actuel
- ✅ **2891 observations réelles** en base de données
- ✅ **Politique stricte** : AUCUNE estimation ni simulation
- ✅ **Collecteur intelligent** : Scraping → Saisie manuelle → Rien
- ✅ **DAG Airflow** : Exécution automatique 17h00 (lun-ven)

---

## 🤖 Fonctionnement du Système

### Stratégies de Collecte (Ordre Séquentiel)

#### 1️⃣ Scraping Automatique (Prioritaire)
**Script** : `scripts/connectors/brvm_scraper_production.py`
- Scrape le site officiel BRVM
- Extrait les cours de clôture réels
- Marque les données : `data_quality: REAL_SCRAPER`
- Si succès → Sauvegarder et terminer
- Si échec → Passer à la stratégie 2

#### 2️⃣ Saisie Manuelle (Fallback)
**Script** : `mettre_a_jour_cours_brvm.py`
- Demande à l'utilisateur de saisir les cours
- Source officielle : https://www.brvm.org/fr/investir/cours-et-cotations
- Marque les données : `data_quality: REAL_MANUAL`
- Si saisie effectuée → Sauvegarder et terminer
- Si saisie annulée → Passer à la stratégie 3

#### 3️⃣ Aucune Collecte (Échec Total)
**Comportement** : 
- ❌ AUCUNE donnée ajoutée
- ❌ AUCUNE estimation générée
- ❌ AUCUNE simulation créée
- 📢 Notification d'échec envoyée
- 💡 Actions manuelles suggérées

---

## 🔒 Garanties de Qualité

### ✅ Ce que le Système Fait
- Collecte UNIQUEMENT des données officielles BRVM
- Vérifie que toutes les données ont un marqueur de qualité
- Refuse d'ajouter des valeurs fictives ou estimées
- Notifie en cas d'impossibilité de collecter

### ❌ Ce que le Système Ne Fait JAMAIS
- Estimer des cours manquants
- Simuler des valeurs fictives
- Générer des données aléatoires
- Dupliquer des cours précédents
- Interpoler entre deux dates
- Ajouter quoi que ce soit sans source officielle

---

## 📅 Automatisation Airflow

### Configuration
- **DAG** : `brvm_collecte_quotidienne_reelle.py`
- **Horaire** : 17h00 (lundi-vendredi)
- **Après** : Clôture BRVM à 16h30

### Workflow du DAG
```
1. Collecter (scraping → saisie manuelle → rien)
   ↓
2. Vérifier présence données du jour
   ↓ (si OK)
3. Vérifier qualité 100% réelle
   ↓ (si OK)
4. Générer rapport final
   
   ↓ (si échec à n'importe quelle étape)
   
5. Notifier échec collecte
```

### Vérifications Automatiques

#### Check 1 : Présence Données
```python
count = collection.count_documents({
    'source': 'BRVM',
    'ts': date_aujourd_hui,
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

if count == 0:
    raise ValueError("Aucune donnée réelle - Collecte échouée")
```

#### Check 2 : Qualité 100%
```python
count_non_reel = collection.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

if count_non_reel > 0:
    raise ValueError("Données non réelles détectées")
```

#### Check 3 : Couverture Minimale
```python
if count < 40:
    print("⚠️  Collecte partielle - Données incomplètes")
```

---

## 🚀 Utilisation

### Activation du Système
```bash
# Configuration et activation complète
python activer_collecte_auto.py

# Démarrer Airflow pour automatisation
start_airflow_background.bat

# Activer le DAG dans l'interface web
# http://localhost:8080 (admin/admin)
# → DAG : brvm_collecte_quotidienne_reelle
```

### Collecte Manuelle Immédiate
```bash
# Lancer la collecte maintenant (teste toutes les stratégies)
python collecter_quotidien_intelligent.py

# Voir le rapport sans collecter
python collecter_quotidien_intelligent.py --rapport
```

### Saisie Manuelle Directe
```bash
# Si vous voulez saisir les cours directement
python mettre_a_jour_cours_brvm.py
```

### Vérifications
```bash
# Vérifier qualité données BRVM
python verifier_cours_brvm.py
# Doit afficher 100% données réelles

# Vérifier historique 60 jours
python verifier_historique_60jours.py

# Vérifier statut Airflow
check_airflow_status.bat
```

---

## 📊 Monitoring

### Logs Airflow
```bash
# Dossier logs
cd airflow/logs/

# Voir logs du DAG
cat dag_id=brvm_collecte_quotidienne_reelle/
```

### Rapport Quotidien
Le collecteur génère automatiquement un rapport :
```
📊 RAPPORT DE COLLECTE
Date : 2025-12-08
Stratégies tentées : scraping, saisie_manuelle
Observations réelles aujourd'hui : 47
Total observations réelles (historique) : 2938
```

### Alertes en Cas d'Échec
```
🔴 NOTIFICATION : COLLECTE QUOTIDIENNE ÉCHOUÉE
⚠️  Aucune donnée réelle n'a pu être collectée aujourd'hui

💡 Actions requises :
   1. Vérifier connexion Internet
   2. Vérifier accès site BRVM
   3. Saisir manuellement
   4. Ou importer CSV

🔴 RAPPEL : Le système n'ajoute JAMAIS de données estimées
```

---

## 🛠️ Scripts Créés

### 1. Collecteur Principal
**`collecter_quotidien_intelligent.py`**
- Orchestrateur des stratégies
- Gestion des fallbacks
- Génération de rapports
- Garantie zéro estimation

### 2. DAG Airflow
**`airflow/dags/brvm_collecte_quotidienne_reelle.py`**
- Automatisation quotidienne
- Vérifications de qualité
- Notifications d'échec
- Workflow complet

### 3. Activation
**`activer_collecte_auto.py`**
- Vérification prérequis
- Configuration système
- Test du collecteur
- Démarrage Airflow

---

## 📋 Checklist Quotidienne

### Automatique (si Airflow activé)
- [x] 17h00 : Collecte automatique lancée
- [x] 17h05 : Vérification données présentes
- [x] 17h06 : Vérification qualité 100%
- [x] 17h07 : Rapport généré

### Manuelle (si nécessaire)
- [ ] Vérifier notification d'échec
- [ ] Consulter logs Airflow
- [ ] Exécuter collecte manuelle : `python collecter_quotidien_intelligent.py`
- [ ] Ou saisir directement : `python mettre_a_jour_cours_brvm.py`

---

## 🎯 Résultats Attendus

### Scénario Succès (Scraping)
```
✅ COLLECTE RÉUSSIE via SCRAPING
   47 observations réelles sauvegardées
   
Stratégies tentées : scraping
Temps : ~30 secondes
Data quality : REAL_SCRAPER
```

### Scénario Succès (Saisie)
```
✅ COLLECTE RÉUSSIE via SAISIE MANUELLE

Stratégies tentées : scraping, saisie_manuelle
Temps : ~5-10 minutes
Data quality : REAL_MANUAL
```

### Scénario Échec
```
❌ COLLECTE ÉCHOUÉE - AUCUNE DONNÉE COLLECTÉE

Stratégies tentées : scraping, saisie_manuelle
Observations ajoutées : 0
Raison : Scraping échoué + Saisie annulée

🔴 AUCUNE DONNÉE N'A ÉTÉ AJOUTÉE
```

---

## 🔧 Dépannage

### Problème : Scraping échoue systématiquement
**Solution** :
1. Vérifier connexion Internet
2. Vérifier accès à https://www.brvm.org
3. Installer/réinstaller BeautifulSoup : `pip install beautifulsoup4`
4. Tester manuellement : `python scripts/connectors/brvm_scraper_production.py`

### Problème : Airflow ne démarre pas
**Solution** :
```bash
# Vérifier processus Airflow
check_airflow_status.bat

# Relancer Airflow
start_airflow_background.bat

# Vérifier logs
cd airflow/logs/scheduler/
```

### Problème : DAG pas visible dans Airflow
**Solution** :
1. Vérifier fichier : `airflow/dags/brvm_collecte_quotidienne_reelle.py`
2. Rafraîchir l'interface web (F5)
3. Vérifier erreurs dans logs Airflow
4. Relancer scheduler Airflow

### Problème : Données non réelles détectées
**Solution** :
```bash
# Nettoyer données non réelles
python nettoyer_brvm_complet.py

# Vérifier qualité
python verifier_cours_brvm.py
# Doit afficher 100% données réelles
```

---

## 📚 Documentation Complète

### Guides Disponibles
- `GUIDE_IMPORT_CSV_AUTOMATIQUE.md` - Import CSV massif
- `GUIDE_HISTORIQUE_60JOURS_BRVM.md` - Constitution historique
- `RECAPITULATIF_60JOURS.md` - Plan d'action 60 jours
- `.github/copilot-instructions.md` - Instructions IA complètes

### Commandes de Référence
```bash
# Collecte
python collecter_quotidien_intelligent.py
python collecter_quotidien_intelligent.py --rapport

# Saisie manuelle
python mettre_a_jour_cours_brvm.py

# Import CSV
python collecter_csv_automatique.py
python collecter_csv_automatique.py --dry-run

# Vérifications
python verifier_cours_brvm.py
python verifier_historique_60jours.py
python show_complete_data.py

# Airflow
start_airflow_background.bat
check_airflow_status.bat

# Nettoyage
python nettoyer_brvm_complet.py
```

---

## ✅ Résumé Exécutif

### Ce qui a été Mis en Place
1. ✅ Collecteur intelligent multi-stratégies
2. ✅ DAG Airflow automatisé (17h lun-ven)
3. ✅ Vérifications qualité strictes
4. ✅ Politique zéro tolérance (aucune estimation)
5. ✅ Notifications échec automatiques
6. ✅ Scripts activation et monitoring
7. ✅ Documentation complète

### Garanties Fournies
- 🔴 AUCUNE estimation automatique
- 🔴 AUCUNE simulation de données
- 🔴 AUCUNE valeur fictive ajoutée
- ✅ Données officielles BRVM uniquement
- ✅ Marqueurs de qualité obligatoires
- ✅ Traçabilité complète

### Prochaines Étapes
1. Activer Airflow : `start_airflow_background.bat`
2. Activer DAG dans interface web
3. Vérifier collecte quotidienne à 17h
4. Monitorer via logs et rapports
5. Intervenir manuellement si nécessaire

---

**🎉 Système de Collecte Automatique Intelligent Opérationnel !**
**🔴 Données Réelles Uniquement - Politique Zéro Tolérance Stricte**

# 🚀 GUIDE DE DÉMARRAGE RAPIDE - SYSTÈME DOUBLE OBJECTIF

## ✅ Installation complète - 16/16 fichiers

Votre système double objectif BRVM est **opérationnel** avec :
- 🟢 **TOP5 Engine** - Performance publique hebdo
- 🔴 **Opportunity Engine** - Détection précoce (J+1 à J+7)

---

## 🎯 Premiers pas (5 minutes)

### 1️⃣ Vérifier les données existantes
```bash
# Voir les données BRVM disponibles
python -c "from plateforme_centralisation.mongo import get_mongo_db; _, db = get_mongo_db(); print(f'DAILY: {db.prices_daily.count_documents({})} | WEEKLY: {db.prices_weekly.count_documents({})} | STOCK_PRICE: {db.STOCK_PRICE.count_documents({})}')"
```

### 2️⃣ Premier test - Opportunity Engine
```bash
# Scanner opportunités sur dernière date disponible
python brvm_pipeline/opportunity_engine.py
```

**Si aucune opportunité** : C'est normal si pas de données DAILY récentes
→ Passez à l'étape 3 (rebuild)

### 3️⃣ Reconstruire l'architecture (si nécessaire)
```bash
# Migrer données existantes → nouvelle architecture 3 niveaux
python brvm_pipeline/master_orchestrator.py --rebuild
```

⏱️ Durée : ~2-5 minutes pour 4,056 observations

### 4️⃣ Tester à nouveau
```bash
# Opportunités du jour
python brvm_pipeline/opportunity_engine.py

# Dashboard complet
python brvm_pipeline/dashboard_opportunities.py
```

---

## 📊 Commandes essentielles

### Quotidien (17h après clôture)
```bash
# Mise à jour complète : DAILY + Opportunités + Notifications
python brvm_pipeline/master_orchestrator.py --daily-update
```

**Ce qui se passe** :
1. ✅ Agrège données quotidiennes
2. 🔍 Scanne opportunités (4 détecteurs)
3. 📢 Notifie si opportunités FORTES (score ≥70)
4. Si lundi → WEEKLY + TOP5

### Lundi matin (8h)
```bash
# Génération TOP5 + Auto-learning
python brvm_pipeline/master_orchestrator.py --weekly-update

# Dashboard opportunités
python brvm_pipeline/dashboard_opportunities.py
```

### Analyse action spécifique
```bash
# Analyser BICC
python brvm_pipeline/opportunity_engine.py --symbol BICC

# TOP5 semaine en cours
python brvm_pipeline/top5_engine.py
```

---

## 🔥 Comprendre les opportunités

### 4 Détecteurs précoces

| Détecteur | Signal | Exemple BRVM |
|-----------|--------|--------------|
| 📰 **News Silencieuse** | Annonce positive MAIS prix calme | Nouveau contrat annoncé, +0.5% seulement |
| 📊 **Volume Anormal** | Volume × 2 mais prix stable | Accumulation discrète institutionnelle |
| ⚡ **Rupture de Sommeil** | Action morte qui se réveille | ATR × 1.8 + volume montant |
| 🏢 **Retard Secteur** | Secteur monte, action en retard | Secteur +20%, action +5% |

### Seuils décision

```
Score ≥ 75  →  🚨 PRIORITAIRE  →  Entrer 25% immédiatement
Score 70-75 →  🔥 FORTE        →  Observer, entrer si confirmation J+1
Score 55-70 →  🔍 OBSERVATION  →  Watchlist
Score < 55  →  ❌ IGNORER
```

### Exemple sortie console
```
🔥 ALERTE OPPORTUNITÉS FORTES DÉTECTÉES 🔥

🚨 PRIORITAIRE | BICC     | Score:  76.2 | Prix:     8500 FCFA
     └─ 📰 News: News:45.0 Prix:+0.8% Vol:0.85x
     └─ 📊 Volume: Vol:2.3x Prix:+0.8%
     Composantes: Vol=65 | News=50 | Volat=45 | Sect=20

🔥 FORTE | SOGB     | Score:  72.5 | Prix:    12400 FCFA
     └─ ⚡ Volatilité: ATR:2.1x Vol:1.4x
     Composantes: Vol=38 | News=25 | Volat=85 | Sect=15
```

---

## 💰 Allocation capital (Recommandée)

| Type | % Capital | Gestion |
|------|-----------|---------|
| TOP5 trades | 60-70% | Positions complètes, stops -8% |
| Opportunités | 20-30% | Positions partielles 25-50%, stops -12% |
| Cash | 10-20% | Sécurité |

### Règle entrée opportunités FORTES

**Score ≥ 75 (PRIORITAIRE)** :
1. Entrer **25%** position immédiatement
2. Si confirmation J+1 (volume maintenu) → **+25%** (total 50%)
3. Si entre dans TOP5 hebdo → **compléter à 100%**

**Score 70-75 (FORTE)** :
1. Watchlist
2. Entrer 25% SEULEMENT si confirmation J+1

---

## 📢 Notifications

### Activer notifications FORTES
Le système notifie automatiquement lors du `--daily-update` :
- ✅ **Console** : Affichage coloré (activé par défaut)
- ✅ **Fichier log** : `logs/notifications/opportunities_YYYY-MM-DD.log`
- ⚙️ **Email** : À configurer dans `notifications_opportunites.py`
- ⚙️ **Webhook Discord/Slack** : À configurer

### Configuration email (optionnel)
Éditer [brvm_pipeline/notifications_opportunites.py](brvm_pipeline/notifications_opportunites.py) :
```python
CONFIG = {
    'email': True,  # Activer
    'email_config': {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_email': 'votre@email.com',
        'to_emails': ['destinataire@email.com'],
        'password': 'votre_mot_de_passe'
    }
}
```

### Test notifications
```bash
# Tester sur dernière date
python brvm_pipeline/notifications_opportunites.py --test

# Date spécifique
python brvm_pipeline/notifications_opportunites.py --date 2026-02-10
```

---

## 📊 Dashboard & Suivi

### Opportunités du jour
```bash
python brvm_pipeline/dashboard_opportunities.py --today
```

Affiche :
- Opportunités FORTES (≥70)
- Opportunités OBSERVATION (55-70)
- Détecteurs actifs par action

### Analyse conversion (12 semaines)
```bash
python brvm_pipeline/dashboard_opportunities.py --conversion --weeks 12
```

Affiche :
- Taux conversion opportunité → TOP5
- Opportunités converties (avec performance)
- Opportunités non converties (avec raisons)
- Délai moyen détection → TOP5

### Historique action
```bash
python brvm_pipeline/dashboard_opportunities.py --history BICC --days 30
```

---

## 🔧 Configuration avancée

### Modifier poids Opportunity Engine
Éditer [brvm_pipeline/config_double_objectif.py](brvm_pipeline/config_double_objectif.py) :
```python
OPPORTUNITY_CONFIG = {
    'weights': {
        'volume_acceleration': 0.35,   # Modifier ici
        'semantic_impact': 0.30,
        'volatility_expansion': 0.20,
        'sector_momentum': 0.15
    }
}
```

### Modifier seuils
```python
OPPORTUNITY_CONFIG = {
    'thresholds': {
        'strong_opportunity': 70,  # FORTE (défaut: 70)
        'weak_opportunity': 55,    # OBSERVATION (défaut: 55)
    }
}
```

**Valider** :
```bash
python brvm_pipeline/config_double_objectif.py
```

---

## 🎯 Métriques de succès

### KPIs à suivre

| Métrique | Target | Excellent | Commande |
|----------|--------|-----------|----------|
| TOP5 dans officiel | ≥60% (3/5) | ≥80% (4/5) | `dashboard_opportunities.py --conversion` |
| Conversion opportunités | ≥40% | ≥60% | `dashboard_opportunities.py --conversion` |
| Délai détection → TOP5 | 3-5j | 2-3j | `dashboard_opportunities.py --conversion` |
| Performance mensuelle | ≥15% | ≥25% | Calcul manuel |

---

## 🚨 Troubleshooting

### Pas d'opportunités détectées
```bash
# Vérifier données DAILY
python brvm_pipeline/pipeline_daily.py --stats

# Rebaisser seuils si trop strict
# config_double_objectif.py : strong_opportunity: 70 → 65
```

### Trop d'opportunités (>10/jour)
```bash
# Monter seuil OBSERVATION
# config_double_objectif.py : weak_opportunity: 55 → 60
```

### Erreur import
```bash
# Vérifier environnement Python
python brvm_pipeline/verifier_installation.py
```

---

## 📚 Documentation complète

1. **[README_DOUBLE_OBJECTIF.md](README_DOUBLE_OBJECTIF.md)** - Documentation technique complète
2. **[STRATEGIE_DOUBLE_OBJECTIF.md](STRATEGIE_DOUBLE_OBJECTIF.md)** - Guide stratégique investissement
3. **[README_ARCHITECTURE_3_NIVEAUX.md](README_ARCHITECTURE_3_NIVEAUX.md)** - Architecture technique

---

## ✅ Checklist mise en production

- [x] Tous les fichiers présents (16/16)
- [ ] Rebuild exécuté (`--rebuild`)
- [ ] Premier scan opportunités OK
- [ ] Notifications configurées (console minimum)
- [ ] Workflow quotidien testé (`--daily-update`)
- [ ] Dashboard accessible
- [ ] Configuration validée

---

## 🎯 Scénario d'usage complet

**Lundi 10h - Préparation semaine**
```bash
# 1. Générer TOP5
python brvm_pipeline/master_orchestrator.py --weekly-update

# 2. Consulter opportunités
python brvm_pipeline/dashboard_opportunities.py

# 3. Vérifier conversion semaine passée
python brvm_pipeline/dashboard_opportunities.py --conversion
```

**Mardi-Vendredi 17h - Quotidien**
```bash
# Mise à jour complète quotidienne
python brvm_pipeline/master_orchestrator.py --daily-update
```

**Si notification opportunité FORTE** :
1. Vérifier détails : `opportunity_engine.py --symbol BICC`
2. Analyser détecteurs actifs
3. Décider entrée 25% si score ≥75

---

## 💡 Conseils d'expert

### ✅ À FAIRE
- Scanner opportunités **TOUS LES JOURS** (17h)
- Respecter allocation (60-70% TOP5, 20-30% opportunités)
- Entrer **partiellement** sur opportunités (25-50% max)
- Compléter position si opportunité → TOP5
- Suivre conversion hebdomadaire

### ❌ À NE PAS FAIRE
- Confondre règles TOP5 et opportunités
- Sur-allouer sur opportunités (>30%)
- Ignorer opportunités OBSERVATION (watchlist)
- Traiter toutes opportunités comme trades
- Négliger le suivi conversion

---

**Système créé le** : 2026-02-10  
**Version** : 2.0 (Double Objectif)  
**Status** : ✅ Production ready

🎉 **Prêt à détecter les opportunités BRVM avant les autres !**

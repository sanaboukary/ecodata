# Configuration des Acteurs - Plateforme de Centralisation

## Vue d'Ensemble

Ce document décrit la configuration complète des acteurs (utilisateurs) de la plateforme basée sur le diagramme de cas d'utilisation.

## 🎭 Les 8 Acteurs de la Plateforme

### 1️⃣ Administrateur Plateforme 
**Rôle**: `admin_plateforme`  
**Icône**: 👨‍💼

#### Responsabilités
- Configure les sources de données (BRVM, FMI, BM, ONU, BAD)
- Définit les rôles et droits d'accès (RBAC)
- Supervise la plateforme (audit, gestion incidents)
- Lance et planifie les collectes automatisées

#### Permissions
✅ **Accès total** aux 5 sources de données  
✅ **Export** (CSV, Excel, JSON, API)  
✅ **Ingestion** (manuelle, planifiée, arrêt, retry)  
✅ **Sources** (ajout, modification, suppression, configuration)  
✅ **Administration** (utilisateurs, rôles, audit, permissions, système)  
✅ **Monitoring** (pipelines, jobs, qualité, alertes)  
✅ **Dashboards** (accès, création, partage)

#### Cas d'Usage Principaux
1. Configurer une nouvelle source (ex: ajouter BRVM)
2. Créer un nouvel utilisateur analyste
3. Auditer les activités de la plateforme
4. Planifier une collecte quotidienne IMF


### 2️⃣ Ingénieur Data / ETL
**Rôle**: `ingenieur_data`  
**Icône**: 🔧

#### Responsabilités
- Met en place les pipelines ETL
- Vérifie la qualité des données
- Gère l'ingestion massive (API, fichiers, scraping)
- Relance les jobs en échec
- Optimise le stockage et le data warehouse

#### Permissions
✅ **Accès** aux 5 sources  
✅ **Export** (CSV, JSON)  
✅ **Ingestion complète** (run, schedule, stop, retry)  
✅ **Configuration** des sources  
✅ **Audit** (consultation logs)  
✅ **Monitoring complet** (pipelines, jobs, qualité, alertes)  
✅ **Dashboards** (consultation)

#### Cas d'Usage Principaux
1. Créer un pipeline WorldBank → MongoDB
2. Relancer un job BRVM échoué
3. Vérifier la qualité des données IMF
4. Optimiser les schémas MongoDB


### 3️⃣ Analyste / Économiste
**Rôle**: `analyste_economiste`  
**Icône**: 📊

#### Responsabilités
- Cherche et explore les indicateurs économiques
- Visualise via dashboards interactifs
- Exporte les résultats pour analyses externes
- Consulte les KPI par source

#### Permissions
✅ **Accès** aux 5 sources  
✅ **Export** (CSV, Excel, JSON)  
✅ **Dashboards** (accès, création personnelle)

#### Cas d'Usage Principaux
1. Rechercher l'indicateur "PIB réel" pour le Bénin
2. Créer un dashboard comparant BRVM et IMF
3. Exporter les données de dette en Excel
4. Consulter les cours boursiers BRVM


### 4️⃣ Lecteur (Stakeholder)
**Rôle**: `lecteur`  
**Icône**: 👀

#### Responsabilités
- Consultation simple des données
- Accès aux dashboards publics
- Vision synthétique des résultats
- Pas de manipulation de données brutes

#### Permissions
✅ **Accès** aux 5 sources (lecture seule)  
✅ **Dashboards** (consultation uniquement)

#### Profils Types
- Investisseur particulier
- Décideur politique
- Bailleur de fonds
- Journaliste économique
- Étudiant en économie

#### Cas d'Usage Principaux
1. Consulter le dashboard BRVM pour suivre ses investissements
2. Voir les tendances macroéconomiques
3. Comparer les indicateurs entre pays


### 5️⃣ Client API Externe
**Rôle**: `client_api`  
**Icône**: 🔌

#### Responsabilités
- Consomme les données via API REST
- Interroge les endpoints programmatiquement
- Intègre les données dans systèmes externes

#### Permissions
✅ **Accès** aux 5 sources via API  
✅ **Export API** (JSON)  
🔑 **Authentification** par token  
⏱️ **Rate limiting** (1000 req/jour par défaut)

#### Exemples de Clients
- Dashboard Power BI
- Application mobile
- Site web externe
- Système de BI interne
- Script Python d'analyse

#### Endpoints Disponibles
```
GET /api/brvm/stocks/
GET /api/brvm/stock/<symbol>/
GET /api/worldbank/indicators/
GET /api/imf/cpi/
GET /api/un/sdg/
GET /api/afdb/summary/
```

#### Cas d'Usage Principaux
1. Connecter Power BI à la plateforme
2. Créer une app mobile de suivi BRVM
3. Automatiser des rapports hebdomadaires


### 6️⃣ Fournisseur de Données
**Rôle**: *Externe* (pas d'utilisateur dans la plateforme)  
**Icône**: 📡

#### Fournisseurs
- **BRVM**: Bourse Régionale des Valeurs Mobilières
- **FMI**: Fonds Monétaire International
- **Banque Mondiale**: World Bank Open Data
- **ONU**: Objectifs de Développement Durable (SDG)
- **BAD**: Banque Africaine de Développement

#### Modes de Publication
- API REST (BRVM, WorldBank, IMF)
- FTP / SFTP
- Site web (scraping)
- Fichiers Excel/CSV
- PDF (extraction via OCR)

#### Intégration
Les connecteurs automatisés (`scripts/connectors/`) récupèrent les données selon les planifications Airflow.


### 7️⃣ Fournisseur d'Identité (MFA / IdP)
**Rôle**: *Système externe*  
**Icône**: 🔐

#### Responsabilités
- Authentification des utilisateurs
- Multi-Factor Authentication (MFA)
- Vérification d'identité

#### Options d'Intégration
- **Azure AD** (Microsoft Entra ID)
- **Google Identity Platform**
- **Keycloak** (open-source)
- **Auth0**
- **Okta**

#### Fonctionnalités
- Connexion SSO (Single Sign-On)
- MFA par SMS/Email/App
- Gestion centralisée des identités
- Audit des connexions


### 8️⃣ Système d'Observabilité
**Rôle**: *Infrastructure*  
**Icône**: 📈

#### Responsabilités
- Surveille les pipelines et l'infrastructure
- Déclenche des alertes en cas de panne
- Produit des logs et métriques pour audit

#### Stack Technique
- **Grafana**: Visualisation métriques
- **Prometheus**: Collecte métriques
- **ELK Stack**: Elasticsearch, Logstash, Kibana (logs)
- **Airflow**: Monitoring DAGs
- **MongoDB**: Logs d'ingestion

#### Métriques Surveillées
- Taux de succès des jobs
- Temps d'exécution des pipelines
- Volume de données ingérées
- Erreurs par source
- Disponibilité de l'API


## 🔐 Système RBAC (Role-Based Access Control)

### Structure Hiérarchique

```
Administrateur Plateforme (toutes permissions)
    ↓
Ingénieur Data (permissions techniques)
    ↓
Analyste/Économiste (permissions métier)
    ↓
Lecteur (lecture seule)
    ↓
Client API (API uniquement)
```

### Matrice de Permissions

| Permission | Admin | Ingénieur | Analyste | Lecteur | API |
|-----------|-------|-----------|----------|---------|-----|
| **Accès Données** |
| Consulter BRVM | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consulter WorldBank | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consulter IMF | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consulter ONU | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consulter BAD | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Export** |
| Export CSV | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export Excel | ✅ | ❌ | ✅ | ❌ | ❌ |
| Export JSON | ✅ | ✅ | ✅ | ❌ | ❌ |
| API REST | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Ingestion** |
| Collecte manuelle | ✅ | ✅ | ❌ | ❌ | ❌ |
| Planifier collecte | ✅ | ✅ | ❌ | ❌ | ❌ |
| Arrêter collecte | ✅ | ✅ | ❌ | ❌ | ❌ |
| Relancer job | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Sources** |
| Ajouter source | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier source | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer source | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configurer source | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Administration** |
| Gérer utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gérer rôles | ✅ | ❌ | ❌ | ❌ | ❌ |
| Consulter audit | ✅ | ✅ | ❌ | ❌ | ❌ |
| Config système | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Monitoring** |
| Voir pipelines | ✅ | ✅ | ❌ | ❌ | ❌ |
| Surveiller jobs | ✅ | ✅ | ❌ | ❌ | ❌ |
| Qualité données | ✅ | ✅ | ❌ | ❌ | ❌ |
| Recevoir alertes | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Dashboards** |
| Consulter | ✅ | ✅ | ✅ | ✅ | ❌ |
| Créer | ✅ | ❌ | ✅ | ❌ | ❌ |
| Partager | ✅ | ❌ | ❌ | ❌ | ❌ |


## 🚀 Mise en Place

### 1. Créer les Rôles et Permissions

```bash
python manage.py init_roles
```

Cette commande crée:
- ✅ 5 rôles
- ✅ 31 permissions réparties en 7 catégories
- ✅ Associations rôles-permissions

### 2. Créer le Premier Administrateur

```bash
python manage.py createsuperuser
```

Puis dans le shell Django:
```python
from users.models import Role, User

admin_role = Role.objects.get(code='admin_plateforme')
admin_user = User.objects.get(username='admin')
admin_user.role = admin_role
admin_user.save()
```

### 3. Créer des Utilisateurs Types

```python
from users.models import Role, User

# Ingénieur Data
engineer = User.objects.create_user(
    username='data_engineer',
    email='engineer@platform.com',
    password='secure_password',
    role=Role.objects.get(code='ingenieur_data'),
    organization='Équipe Technique'
)

# Analyste
analyst = User.objects.create_user(
    username='analyst',
    email='analyst@platform.com',
    password='secure_password',
    role=Role.objects.get(code='analyste_economiste'),
    organization='Service Études'
)

# Lecteur
reader = User.objects.create_user(
    username='investor',
    email='investor@platform.com',
    password='secure_password',
    role=Role.objects.get(code='lecteur'),
    organization='Investisseur Privé'
)
```

### 4. Créer un Client API

```python
import secrets
from users.models import Role, User, APIToken

api_user = User.objects.create_user(
    username='powerbi_client',
    email='api@company.com',
    password='secure_password',
    role=Role.objects.get(code='client_api'),
    organization='BI Team'
)

# Générer un token API
token = APIToken.objects.create(
    user=api_user,
    name='Power BI Dashboard',
    key=secrets.token_urlsafe(32),
    rate_limit=5000
)

print(f"Token API: {token.key}")
```


## 📝 Audit et Traçabilité

Toutes les actions importantes sont tracées dans `AuditLog`:

```python
from users.models import AuditLog

# Enregistrer une action
AuditLog.objects.create(
    user=request.user,
    action='export',
    resource_type='BRVM',
    resource_id='BOAC',
    description='Export CSV de l'action BOAC',
    ip_address=request.META.get('REMOTE_ADDR'),
    metadata={'format': 'CSV', 'rows': 100}
)

# Consulter l'historique
logs = AuditLog.objects.filter(user=my_user).order_by('-timestamp')[:100]
```


## 🔒 Sécurité

### Multi-Factor Authentication (MFA)

```python
# Activer MFA pour un utilisateur
user.mfa_enabled = True
user.mfa_secret = pyotp.random_base32()
user.save()

# Vérifier un code MFA
totp = pyotp.TOTP(user.mfa_secret)
is_valid = totp.verify(code_from_user)
```

### Rate Limiting API

Les tokens API ont une limite de requêtes par jour configurable:

```python
token.rate_limit = 1000  # 1000 requêtes/jour
token.save()
```

### IP Whitelisting

```python
token.allowed_ips = "192.168.1.100\n10.0.0.50"
token.save()
```


## 📊 Tableaux de Bord par Rôle

### Administrateur
- Dashboard global multi-sources
- Monitoring d'ingestion
- Gestion des utilisateurs
- Logs d'audit

### Ingénieur Data
- État des pipelines Airflow
- Qualité des données
- Jobs en cours/échoués
- Métriques de performance

### Analyste
- Dashboards BRVM, WorldBank, IMF, UN, AfDB
- Explorateur de données
- Comparateur d'indicateurs
- Export de rapports

### Lecteur
- Dashboards publics (lecture seule)
- Synthèses par source
- Aucune modification possible


## 🔗 Intégrations Externes

### Connexion SSO (Azure AD)

```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.azuread.AzureADOAuth2',
]

SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = 'your-client-id'
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = 'your-client-secret'
```

### Webhooks pour Alertes

```python
# Envoyer une alerte quand un job échoue
import requests

def notify_job_failure(job_name, error):
    webhook_url = "https://hooks.slack.com/services/..."
    requests.post(webhook_url, json={
        'text': f'❌ Job {job_name} échoué: {error}'
    })
```


## 📚 Documentation API

### Authentication

```bash
# Obtenir un token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "password"}'

# Utiliser le token
curl http://localhost:8000/api/brvm/stocks/ \
  -H "Authorization: Bearer <token>"
```

### Exemples de Requêtes

```bash
# Lister les actions BRVM
GET /api/brvm/stocks/

# Détails d'une action
GET /api/brvm/stock/BOAC/

# Indicateurs WorldBank
GET /api/worldbank/indicators/?country=BEN

# Export CSV
GET /dashboards/export/indicateurs.csv?source=BRVM
```


## ✅ Checklist de Configuration

- [ ] Créer les rôles (`python manage.py init_roles`)
- [ ] Créer le super admin
- [ ] Assigner le rôle admin au super admin
- [ ] Créer des utilisateurs de test pour chaque rôle
- [ ] Configurer MFA pour l'admin
- [ ] Générer des tokens API pour les clients externes
- [ ] Configurer le SSO (optionnel)
- [ ] Tester les permissions de chaque rôle
- [ ] Vérifier les logs d'audit
- [ ] Documenter les utilisateurs créés


## 🎯 Prochaines Étapes

1. **Activer le serveur**: `python manage.py runserver`
2. **Initialiser les rôles**: `python manage.py init_roles`
3. **Créer des utilisateurs de test**
4. **Tester les dashboards** avec chaque rôle
5. **Configurer les alertes** pour l'ingénieur data
6. **Intégrer le SSO** si nécessaire
7. **Générer la documentation API** avec Swagger

---

**Créé le**: 18 novembre 2025  
**Version**: 1.0  
**Auteur**: Configuration automatisée

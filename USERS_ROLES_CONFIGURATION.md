# 🔐 Système de Gestion des Utilisateurs et Rôles (RBAC)

## Configuration des Acteurs selon le Diagramme de Cas d'Utilisation

Ce document décrit l'implémentation complète du système d'authentification, d'autorisation et de gestion des rôles pour la plateforme de centralisation des données économiques.

---

## 📋 Vue d'Ensemble

### Architecture RBAC (Role-Based Access Control)

Le système implémente un contrôle d'accès basé sur les rôles avec 5 acteurs principaux:

1. **👨‍💼 Administrateur Plateforme** - Contrôle total du système
2. **👨‍💻 Ingénieur Data/ETL** - Gestion des pipelines et de la qualité des données
3. **👨‍🔬 Analyste/Économiste** - Exploration et analyse des données
4. **👀 Lecteur (Stakeholder)** - Consultation simple des dashboards
5. **🤖 Client API Externe** - Accès programmatique via API REST

### Acteurs Externes

- **📡 Fournisseurs de données** (BRVM, IMF, World Bank, UN, AfDB)
- **🔐 Fournisseur d'identité (MFA/IdP)** - Authentification sécurisée
- **📊 Système d'observabilité** - Monitoring et alertes

---

## 🏗️ Structure du Système

### Modèles de Données

#### 1. **User** (Utilisateur étendu)
```python
- username, email, password (Django standard)
- organization, phone (informations supplémentaires)
- role (ForeignKey vers Role)
- mfa_enabled, mfa_secret (Multi-Factor Authentication)
- api_token, api_rate_limit (pour les clients API)
- last_login_ip, failed_login_attempts
- account_locked_until (sécurité anti-brute force)
```

#### 2. **Role** (Rôle)
```python
ROLES DISPONIBLES:
- admin_platform: Administrateur Plateforme
- data_engineer: Ingénieur Data/ETL
- analyst_economist: Analyste/Économiste
- reader_stakeholder: Lecteur (Stakeholder)
- api_client: Client API Externe
```

#### 3. **Permission** (Permission granulaire)
```python
CATÉGORIES:
- data_access: Accès aux données
- data_export: Export de données
- data_ingestion: Ingestion de données
- admin_config: Configuration admin
- pipeline_manage: Gestion pipelines
- api_consume: Consommation API
- audit_view: Visualisation audit
```

#### 4. **AuditLog** (Journal d'audit)
```python
Enregistre toutes les actions:
- login, logout
- data_access, data_export, data_ingestion
- config_change, pipeline_run
- api_call, permission_change
```

#### 5. **DataSourceAccess** (Contrôle d'accès par source)
```python
Restrictions granulaires:
- Utilisateur peut accéder à BRVM mais pas IMF
- Peut visualiser mais pas exporter
```

---

## 👥 Configuration des Rôles et Permissions

### 1️⃣ Administrateur Plateforme

**Responsabilités:**
- Configure les sources de données (BRVM, FMI, etc.)
- Définit les rôles et droits d'accès (RBAC)
- Supervise la plateforme (audit des activités)
- Lance ou planifie la collecte automatisée

**Permissions complètes:**
```python
✓ data.view_all, data.view_dashboard, data.view_kpi, data.search_indicators
✓ data.view_brvm, data.view_worldbank, data.view_imf
✓ export.csv, export.excel, export.json
✓ ingestion.trigger, ingestion.schedule, ingestion.monitor, ingestion.retry
✓ admin.manage_users, admin.manage_roles, admin.configure_sources, admin.view_audit
✓ pipeline.create, pipeline.edit, pipeline.delete, pipeline.run, pipeline.validate
✓ audit.view, audit.export
```

**Cas d'usage:**
```python
# 1. Ajouter un nouvel utilisateur avec rôle
@role_required(Role.ADMIN_PLATFORM)
def create_user(request):
    user = User.objects.create_user(
        username='analyst1',
        email='analyst@example.com',
        role=Role.objects.get(code=Role.ANALYST_ECONOMIST)
    )

# 2. Consulter les logs d'audit
@role_required(Role.ADMIN_PLATFORM)
def view_audit_logs(request):
    logs = AuditLog.objects.filter(
        level__in=[AuditLog.LEVEL_WARNING, AuditLog.LEVEL_ERROR]
    )

# 3. Configurer une source de données
@role_required(Role.ADMIN_PLATFORM)
def configure_brvm_source(request):
    # Configuration de la source BRVM
    pass
```

---

### 2️⃣ Ingénieur Data/ETL

**Responsabilités:**
- Met en place les pipelines de collecte et transformation
- Vérifie la qualité des données (contrôles, validation de schémas)
- Gère l'ingestion massive de données (API, fichiers, scraping)
- Relance les jobs en cas d'échec
- Optimise la performance du stockage

**Permissions:**
```python
✓ data.view_all, data.view_dashboard
✓ export.csv, export.json
✓ ingestion.trigger, ingestion.schedule, ingestion.monitor, ingestion.retry
✓ pipeline.create, pipeline.edit, pipeline.delete, pipeline.run, pipeline.validate
✓ audit.view
```

**Cas d'usage:**
```python
# 1. Déclencher une ingestion manuelle
@role_required(Role.DATA_ENGINEER)
@permission_required('ingestion.trigger')
def trigger_brvm_ingestion(request):
    from scripts.pipeline import run_ingestion
    count = run_ingestion('brvm')
    return JsonResponse({'observations': count})

# 2. Relancer un job échoué
@role_required(Role.DATA_ENGINEER)
@permission_required('ingestion.retry')
def retry_failed_job(request, run_id):
    # Logique de relance
    pass

# 3. Valider la qualité des données
@role_required(Role.DATA_ENGINEER)
@permission_required('pipeline.validate')
def validate_data_quality(request):
    _, db = get_mongo_db()
    # Vérifier les schémas, doublons, etc.
    pass
```

---

### 3️⃣ Analyste/Économiste

**Responsabilités:**
- Cherche et explore les indicateurs (PIB, dette, inflation, cours boursiers)
- Visualise les données via tableaux de bord interactifs
- Exporte les résultats (CSV, Excel, JSON) pour analyses
- Consulte les KPI déjà définis par source

**Permissions:**
```python
✓ data.view_all, data.view_dashboard, data.view_kpi, data.search_indicators
✓ data.view_brvm, data.view_worldbank, data.view_imf
✓ export.csv, export.excel, export.json
```

**Cas d'usage:**
```python
# 1. Rechercher des indicateurs économiques
@role_required(Role.ANALYST_ECONOMIST)
@permission_required('data.search_indicators')
def search_economic_indicators(request):
    query = request.GET.get('q')
    _, db = get_mongo_db()
    results = db.curated_observations.find({
        '$text': {'$search': query}
    })
    return JsonResponse({'results': list(results)})

# 2. Exporter des données pour analyse
@role_required(Role.ANALYST_ECONOMIST)
@permission_required('export.excel')
@audit_action(AuditLog.ACTION_DATA_EXPORT)
def export_to_excel(request):
    # Génération du fichier Excel
    pass

# 3. Visualiser les KPI BRVM
@role_required(Role.ANALYST_ECONOMIST)
@source_access_required('BRVM')
def brvm_kpis(request):
    return render(request, 'dashboard/dashboard_brvm.html')
```

---

### 4️⃣ Lecteur (Stakeholder)

**Responsabilités:**
- Acteur "consommateur simple" (investisseur, décideur, bailleur)
- Ne manipule pas la donnée brute
- Consulte des tableaux de bord et exports
- Accède à une vision synthétique des résultats

**Permissions (limitées):**
```python
✓ data.view_dashboard, data.view_kpi
✓ export.csv (basique uniquement)
```

**Cas d'usage:**
```python
# 1. Consulter le dashboard général
@role_required(Role.READER_STAKEHOLDER)
def view_dashboard(request):
    return render(request, 'dashboard/index.html')

# 2. Export CSV simplifié
@role_required(Role.READER_STAKEHOLDER)
@permission_required('export.csv')
def export_summary_csv(request):
    # Export limité aux données agrégées
    pass
```

---

### 5️⃣ Client API Externe

**Responsabilités:**
- Autre système ou application connecté via API REST
- Interroge les endpoints `/indicateurs`, `/observations`, `/pays`
- Exemple: Dashboard Power BI, application mobile

**Permissions:**
```python
✓ api.read
✓ data.view_all
```

**Cas d'usage:**
```python
# 1. Authentification par token
@api_token_required
def api_get_observations(request):
    _, db = get_mongo_db()
    source = request.GET.get('source')
    data = list(db.curated_observations.find({'source': source}).limit(100))
    return JsonResponse({'results': data})

# 2. Génération d'un token API
user = User.objects.get(username='api_client_1')
user.role = Role.objects.get(code=Role.API_CLIENT)
token = user.generate_api_token()
# Utilisation: Authorization: Bearer <token>

# 3. Appel API externe (depuis Power BI, par exemple)
# GET /api/observations?source=BRVM
# Headers: Authorization: Bearer abc123xyz...
```

---

## 🔐 Authentification Multi-Facteurs (MFA)

### Configuration MFA

Le système supporte l'authentification à deux facteurs via TOTP (Time-based One-Time Password):

```python
# 1. Activer MFA pour un utilisateur
user = User.objects.get(username='admin1')
secret = user.regenerate_mfa_secret()

# 2. Générer un QR Code pour Google Authenticator
import pyotp
totp = pyotp.TOTP(secret)
qr_uri = totp.provisioning_uri(
    name=user.email,
    issuer_name='Plateforme Centralisation'
)
# Afficher le QR Code à l'utilisateur

# 3. Vérifier un code MFA lors du login
token = '123456'  # Code de l'application
if user.verify_mfa_token(token):
    # Connexion autorisée
    pass
```

### Codes de Secours

En cas de perte du dispositif MFA, 8 codes de secours sont générés:

```python
# Codes stockés dans user.mfa_backup_codes
['A1B2C3D4', 'E5F6G7H8', ...]
```

---

## 📊 Système d'Audit et Observabilité

### Logs d'Audit Automatiques

Toutes les actions importantes sont enregistrées:

```python
# Log de connexion
AuditLog.objects.create(
    user=request.user,
    action=AuditLog.ACTION_LOGIN,
    level=AuditLog.LEVEL_INFO,
    details={'success': True},
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...'
)

# Log d'export de données
@audit_action(AuditLog.ACTION_DATA_EXPORT, 'BRVM Stock Prices')
def export_brvm_data(request):
    # L'audit est automatique grâce au décorateur
    pass

# Consultation des logs (Admin uniquement)
@role_required(Role.ADMIN_PLATFORM)
def view_audit_logs(request):
    logs = AuditLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).order_by('-timestamp')
    return render(request, 'users/audit_logs.html', {'logs': logs})
```

### Alertes de Sécurité

Le système génère des alertes pour:
- 5+ tentatives de connexion échouées → Verrouillage du compte
- Accès à des ressources non autorisées
- Changements de permissions
- Appels API suspects

```python
# Récupérer les alertes critiques
security_alerts = AuditLog.objects.filter(
    level__in=[AuditLog.LEVEL_WARNING, AuditLog.LEVEL_ERROR, AuditLog.LEVEL_CRITICAL],
    timestamp__gte=timezone.now() - timedelta(hours=24)
)
```

---

## 🚀 Installation et Initialisation

### 1. Créer les tables dans MongoDB

```bash
# Activer l'environnement virtuel
source .venv/Scripts/activate

# Créer les migrations
python manage.py makemigrations users

# Appliquer les migrations
python manage.py migrate users
```

### 2. Initialiser les rôles et permissions

```bash
python manage.py init_roles_permissions
```

**Sortie attendue:**
```
================================================================================
Initialisation des Rôles et Permissions
================================================================================

📋 Création des permissions...
  ✓ data.view_all
  ✓ data.view_dashboard
  ...

👥 Création des rôles...
  ✓ Administrateur Plateforme
  ✓ Ingénieur Data/ETL
  ...

🔗 Association rôles ↔ permissions...
  Administrateur Plateforme:
    ✓ data.view_all
    ✓ export.csv
    ...

================================================================================
✅ Initialisation terminée!
================================================================================

📊 Résumé:
  • Rôles créés: 5
  • Permissions créées: 27
  • Associations créées: 89
```

### 3. Créer le premier administrateur

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@platform.com
# Password: ********
```

```python
# Assigner le rôle d'administrateur
from users.models import User, Role

user = User.objects.get(username='admin')
user.role = Role.objects.get(code=Role.ADMIN_PLATFORM)
user.save()
```

### 4. Créer des utilisateurs de test

```python
from users.models import User, Role, DataSourceAccess

# Ingénieur Data
engineer = User.objects.create_user(
    username='data_eng1',
    email='engineer@platform.com',
    password='SecurePass123!',
    role=Role.objects.get(code=Role.DATA_ENGINEER),
    organization='Équipe Technique'
)

# Analyste Économiste
analyst = User.objects.create_user(
    username='analyst1',
    email='analyst@platform.com',
    password='SecurePass123!',
    role=Role.objects.get(code=Role.ANALYST_ECONOMIST),
    organization='Département Recherche'
)

# Accès aux sources spécifiques
DataSourceAccess.objects.create(
    user=analyst,
    source='BRVM',
    can_read=True,
    can_export=True
)

# Client API
api_client = User.objects.create_user(
    username='api_power_bi',
    email='powerbi@external.com',
    password='APIClient2025!',
    role=Role.objects.get(code=Role.API_CLIENT),
    organization='Power BI External'
)
api_client.generate_api_token()
print(f"Token API: {api_client.api_token}")
```

---

## 📡 Utilisation des APIs

### Endpoints API disponibles

#### 1. **Authentification par Token**

```bash
# Générer un token (interface web)
POST /users/api/generate-token/

# Utiliser le token dans les requêtes
GET /api/brvm/stock/BOAC/
Headers: Authorization: Bearer <votre_token>
```

#### 2. **Exemples d'appels API**

```python
import requests

# Configuration
API_TOKEN = "abc123xyz..."
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Récupérer les observations BRVM
response = requests.get(
    f"{BASE_URL}/api/brvm/stocks/",
    headers=headers
)
data = response.json()

# Récupérer les détails d'une action
response = requests.get(
    f"{BASE_URL}/api/brvm/stock/BOAC/",
    headers=headers
)
stock_data = response.json()

# Export de données (si permission)
response = requests.get(
    f"{BASE_URL}/export/indicateurs.csv",
    headers=headers
)
csv_data = response.text
```

---

## 🔒 Bonnes Pratiques de Sécurité

### 1. Gestion des Mots de Passe

```python
# Validation stricte des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': '...UserAttributeSimilarityValidator'},
    {'NAME': '...MinimumLengthValidator'},  # Minimum 8 caractères
    {'NAME': '...CommonPasswordValidator'},  # Pas de mots courants
    {'NAME': '...NumericPasswordValidator'},  # Pas que des chiffres
]
```

### 2. Protection Anti-Brute Force

```python
# Verrouillage automatique après 5 tentatives échouées
if user.failed_login_attempts >= 5:
    user.lock_account(30)  # 30 minutes
```

### 3. Rate Limiting API

```python
# Limite de 1000 requêtes/heure par défaut
user.api_rate_limit = 1000

# TODO: Implémenter avec Redis
# from django_ratelimit.decorators import ratelimit
# @ratelimit(key='user', rate='1000/h')
```

### 4. Rotation des Tokens API

```python
# Régénérer le token tous les 90 jours
if user.api_token_created_at < timezone.now() - timedelta(days=90):
    user.generate_api_token()
```

---

## 📈 Dashboards par Rôle

### Administrateur: `/users/admin/dashboard/`
- Statistiques utilisateurs
- Logs d'audit en temps réel
- Alertes de sécurité
- Gestion des rôles et permissions

### Ingénieur Data: `/users/engineer/dashboard/`
- État des pipelines ETL
- Statistiques d'ingestion par source
- Relance des jobs échoués
- Validation de la qualité des données

### Analyste: `/` (homepage + dashboards sources)
- Recherche d'indicateurs
- Visualisations interactives (BRVM, WorldBank, etc.)
- Export de données (CSV, Excel, JSON)
- Comparaison multi-sources

### Lecteur: `/` (vue simplifiée)
- Dashboards en lecture seule
- KPI synthétiques
- Export CSV basique

---

## 🧪 Tests

### Test des Permissions

```python
# Test: Un analyste ne peut pas gérer les utilisateurs
analyst = User.objects.get(username='analyst1')
assert not analyst.has_permission('admin.manage_users')

# Test: Un ingénieur peut déclencher une ingestion
engineer = User.objects.get(username='data_eng1')
assert engineer.has_permission('ingestion.trigger')
```

### Test MFA

```python
import pyotp

user = User.objects.get(username='admin')
user.mfa_enabled = True
user.mfa_secret = pyotp.random_base32()
user.save()

totp = pyotp.TOTP(user.mfa_secret)
token = totp.now()

assert user.verify_mfa_token(token) == True
assert user.verify_mfa_token('000000') == False
```

### Test Audit Logs

```python
# Vérifier qu'un log est créé lors de la connexion
initial_count = AuditLog.objects.count()

client.post('/users/login/', {
    'username': 'admin',
    'password': 'admin123'
})

assert AuditLog.objects.count() == initial_count + 1
assert AuditLog.objects.last().action == AuditLog.ACTION_LOGIN
```

---

## 📚 Références

- **Django Authentication**: https://docs.djangoproject.com/en/4.1/topics/auth/
- **PyOTP (MFA)**: https://pyauth.github.io/pyotp/
- **RBAC Best Practices**: https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html

---

**Dernière mise à jour:** 18 novembre 2025  
**Version:** 1.0.0  
**Auteur:** Équipe Plateforme de Centralisation

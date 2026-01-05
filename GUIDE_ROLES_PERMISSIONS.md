# Guide des Rôles et Permissions - Plateforme BRVM

## 📋 Vue d'ensemble

Système de contrôle d'accès basé sur 4 rôles avec permissions granulaires.

---

## 👥 Rôles Utilisateurs

### 1️⃣ LECTEUR (Reader)
**Public cible**: Étudiants, débutants, public général

**Accès autorisé**:
- ✅ Dashboard général
- ✅ Liste des actions BRVM (prix, variations)
- ✅ Publications financières (rapports, communiqués)

**Accès refusé**:
- ❌ Recommandations de trading
- ❌ Alertes personnalisées
- ❌ Analyses techniques avancées
- ❌ Export de données
- ❌ API REST

**Cas d'usage**: Consulter les cours BRVM et lire les publications officielles.

---

### 2️⃣ INVESTISSEUR (Investor)
**Public cible**: Investisseurs particuliers, traders indépendants

**Accès autorisé**:
- ✅ Tout ce que le LECTEUR a +
- ✅ **Recommandations BUY/HOLD/SELL**
- ✅ **Recommandations premium** (high confidence)
- ✅ **Alertes personnalisées** (prix, volumes)
- ✅ Contexte macroéconomique (PIB, inflation)
- ✅ Corrélations macro ↔ BRVM

**Accès refusé**:
- ❌ Analytics avancés (backtest, sentiment NLP)
- ❌ Export de données brutes
- ❌ API REST

**Cas d'usage**: Prendre des décisions d'investissement basées sur les recommandations IA et configurer des alertes.

---

### 3️⃣ ANALYSTE / INGÉNIEUR FINANCIER (Analyst)
**Public cible**: Analystes financiers, SGI, banques d'investissement

**Accès autorisé**:
- ✅ Tout ce que l'INVESTISSEUR a +
- ✅ **Analytics avancés**:
  - Backtesting de stratégies
  - Analyse technique (RSI, MACD, Bollinger)
  - Sentiment NLP sur publications
- ✅ **Export de données** (CSV, Excel)
- ✅ **API REST complète**
- ✅ Accès aux données brutes MongoDB

**Accès refusé**:
- ❌ Administration système
- ❌ Gestion des utilisateurs

**Cas d'usage**: Développer des modèles quantitatifs, backtest de stratégies, intégration API pour outils propriétaires.

---

### 4️⃣ ADMINISTRATEUR (Admin)
**Public cible**: Vous, équipe technique

**Accès autorisé**:
- ✅ **TOUT** (accès complet)
- ✅ Gestion des utilisateurs et rôles
- ✅ Ingestion de données (BRVM, WB, IMF, AfDB)
- ✅ Configuration système
- ✅ Logs et monitoring
- ✅ Interface Django Admin

**Cas d'usage**: Administration complète de la plateforme.

---

## 🗂️ Matrice d'accès par page

| Page/Fonctionnalité | Lecteur | Investisseur | Analyste | Admin |
|---------------------|---------|--------------|----------|-------|
| **Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **Liste actions BRVM** | ✅ | ✅ | ✅ | ✅ |
| **Détail action** | ✅ | ✅ | ✅ | ✅ |
| **Publications financières** | ✅ | ✅ | ✅ | ✅ |
| **Recommandations** | ❌ | ✅ | ✅ | ✅ |
| **Recommandations premium** | ❌ | ✅ | ✅ | ✅ |
| **Alertes** | ❌ | ✅ | ✅ | ✅ |
| **Contexte macro** | ❌ | ✅ | ✅ | ✅ |
| **Analytics avancés** | ❌ | ❌ | ✅ | ✅ |
| **Backtest** | ❌ | ❌ | ✅ | ✅ |
| **Export données** | ❌ | ❌ | ✅ | ✅ |
| **API REST** | ❌ | ❌ | ✅ | ✅ |
| **Administration** | ❌ | ❌ | ❌ | ✅ |
| **Gestion utilisateurs** | ❌ | ❌ | ❌ | ✅ |
| **Ingestion données** | ❌ | ❌ | ❌ | ✅ |

---

## 🚀 Installation et Configuration

### 1. Créer les migrations
```bash
python manage.py makemigrations users
python manage.py migrate
```

### 2. Créer les utilisateurs de test
```bash
python manage.py create_roles
```

**Identifiants créés**:
- **Admin**: `admin` / `admin123`
- **Analyste**: `analyste` / `analyste123`
- **Investisseur**: `investisseur` / `investisseur123`
- **Lecteur**: `lecteur` / `lecteur123`

### 3. Activer le middleware (settings.py)
```python
MIDDLEWARE = [
    # ... autres middlewares
    'users.middleware.RoleBasedAccessMiddleware',
]
```

---

## 💻 Utilisation dans le code

### Protéger une vue avec un rôle
```python
from users.permissions import role_required

@role_required('INVESTOR', 'ANALYST', 'ADMIN')
def recommendations_view(request):
    # Accessible uniquement aux investisseurs, analystes et admin
    ...

@role_required('ANALYST', 'ADMIN')
def analytics_view(request):
    # Accessible uniquement aux analystes et admin
    ...

@role_required('ADMIN')
def manage_users_view(request):
    # Accessible uniquement à l'admin
    ...
```

### Protéger une vue avec une permission
```python
from users.permissions import permission_required

@permission_required('export_data')
def export_csv_view(request):
    # Accessible à ceux qui ont la permission 'export_data'
    ...
```

### Vérifier les permissions dans un template
```django
{% if user.profile.role == 'ADMIN' %}
    <a href="/admin/">Administration</a>
{% endif %}

{% if user.profile.can_access '/recommendations/' %}
    <a href="/recommendations/">Recommandations</a>
{% endif %}
```

---

## 📊 Logs d'accès

Tous les accès sont loggés dans la table `access_logs`:

```python
from users.models import AccessLog

# Voir les derniers accès d'un utilisateur
logs = AccessLog.objects.filter(user=request.user).order_by('-timestamp')[:50]

# Voir les accès refusés
denied = AccessLog.objects.filter(access_granted=False)
```

---

## 🔐 Sécurité

### Bonnes pratiques
1. **Changer les mots de passe par défaut** en production
2. **Activer HTTPS** pour protéger les sessions
3. **Configurer CSRF protection** (déjà activé dans Django)
4. **Limiter les tentatives de connexion** (installer django-axes)
5. **Auditer régulièrement** les logs d'accès

### Variables d'environnement (.env)
```env
# Sessions
SESSION_COOKIE_SECURE=True  # En production avec HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict

# CSRF
CSRF_COOKIE_SECURE=True  # En production avec HTTPS
```

---

## 🎯 Personnalisation

### Ajouter un nouveau rôle
1. Modifier `users/permissions.py`:
```python
ROLE_PERMISSIONS = {
    'NEW_ROLE': {
        'name': 'Nouveau Rôle',
        'permissions': ['view_dashboard', 'custom_permission']
    },
    # ... autres rôles
}
```

2. Ajouter dans `UserProfile.ROLE_CHOICES`
3. Mettre à jour `PAGE_ACCESS`

### Ajouter une nouvelle permission
```python
'ANALYST': {
    'permissions': [
        # ... permissions existantes
        'new_custom_permission',
    ]
}
```

---

## 📞 Support

Pour toute question sur les rôles et permissions, contacter l'administrateur.

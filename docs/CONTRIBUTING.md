# Guide de contribution

Merci de votre intérêt pour contribuer à la Plateforme de Centralisation des Données !

## Comment contribuer

### Signaler un bug

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/votre-repo/issues)
2. Ouvrez une nouvelle issue avec le tag `bug`
3. Décrivez le bug avec :
   - Steps to reproduce
   - Comportement attendu vs observé
   - Environnement (OS, Python version, etc.)
   - Screenshots si applicable

### Proposer une fonctionnalité

1. Ouvrez une issue avec le tag `enhancement`
2. Décrivez la fonctionnalité et son intérêt
3. Attendez la validation avant de commencer le développement

### Soumettre une Pull Request

1. **Forkez** le projet
2. **Créez une branche** : `git checkout -b feature/ma-fonctionnalite`
3. **Commitez** vos changements : `git commit -m 'Ajout de ma fonctionnalité'`
4. **Pushez** : `git push origin feature/ma-fonctionnalite`
5. **Ouvrez une PR** avec une description claire

## Standards de code

### Python

Suivez **PEP 8** :

```bash
# Formater le code
black .

# Vérifier le style
flake8 .

# Trier les imports
isort .
```

### Structure des commits

Format recommandé :
```
type(scope): description courte

Description détaillée si nécessaire

Fixes #123
```

Types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Exemples :
```
feat(dashboard): ajout du comparateur de pays
fix(ingestion): correction du timeout API World Bank
docs(readme): mise à jour des instructions d'installation
```

## Tests

### Exécuter les tests

```bash
# Tous les tests
python manage.py test

# Tests d'une app
python manage.py test dashboard

# Avec couverture
./test.sh --coverage
```

### Écrire des tests

Placez vos tests dans `app/tests/` :

```python
# dashboard/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse

class MyTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_something(self):
        response = self.client.get(reverse('dashboard-index'))
        self.assertEqual(response.status_code, 200)
```

### Couverture minimale

- Nouvelles fonctionnalités : **80%+** de couverture
- Corrections de bugs : ajouter un test de régression

## Documentation

### Docstrings

Utilisez le format Google :

```python
def ma_fonction(param1, param2):
    """Description courte de la fonction.
    
    Description plus détaillée si nécessaire.
    
    Args:
        param1 (str): Description du paramètre 1
        param2 (int): Description du paramètre 2
    
    Returns:
        bool: Description de la valeur de retour
    
    Raises:
        ValueError: Quand le paramètre est invalide
    """
    pass
```

### Mise à jour de la doc

Si vous ajoutez une fonctionnalité, mettez à jour :
- `README.md`
- `docs/USAGE.md` ou autre doc pertinente
- Docstrings du code

## Environnement de développement

### Installation

```bash
# Cloner le repo
git clone <url>
cd "Implementation plateforme"

# Setup
./setup.sh --dev

# Activer l'env
source .venv/Scripts/activate
```

### Outils recommandés

- **IDE** : VS Code avec extensions Python
- **Formatter** : Black
- **Linter** : Flake8
- **Type checker** : mypy (optionnel)

### Configuration VS Code

`.vscode/settings.json` :
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

## Workflow Git

### Branches

- `main` : Production stable
- `develop` : Développement en cours
- `feature/*` : Nouvelles fonctionnalités
- `fix/*` : Corrections de bugs
- `hotfix/*` : Corrections urgentes

### Merge strategy

- Utilisez **Squash and merge** pour les PRs
- Gardez un historique propre

### Avant de merger

1. ✅ Tests passent
2. ✅ Code formatté (black)
3. ✅ Pas de conflits
4. ✅ Documentation mise à jour
5. ✅ Review approuvée

## Revue de code

### Checklist pour les reviewers

- [ ] Le code est lisible et bien documenté
- [ ] Les tests sont présents et passent
- [ ] Pas de code dupliqué
- [ ] Gestion correcte des erreurs
- [ ] Performance acceptable
- [ ] Sécurité : pas de vulnérabilités évidentes

### Temps de review

Comptez 24-48h pour une review. Soyez patient !

## Ajouter une source de données

1. Créez un connecteur dans `scripts/connectors/`
2. Implémentez `extract()`, `transform()`, `load()`
3. Ajoutez la commande dans `ingestion/management/commands/`
4. Écrivez des tests
5. Documentez dans `docs/ETL.md`

Exemple minimaliste :

```python
# scripts/connectors/nouvelle_source.py
def extract():
    """Récupère les données"""
    return []

def transform(data):
    """Normalise les données"""
    return []

def load(data):
    """Charge dans MongoDB"""
    pass

if __name__ == "__main__":
    data = extract()
    normalized = transform(data)
    load(normalized)
```

## Questions ?

- Ouvrez une [Discussion](https://github.com/votre-repo/discussions)
- Contactez : votre-email@example.com

## Code de conduite

- Soyez respectueux
- Acceptez les critiques constructives
- Focalisez sur ce qui est meilleur pour le projet
- Montrez de l'empathie

---

Merci de contribuer ! 🎉

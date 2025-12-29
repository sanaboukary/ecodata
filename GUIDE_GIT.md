# 🚀 Guide Git - Push vers GitHub

## Scripts Automatiques Créés

### 1️⃣ Push avec message personnalisé

```bash
./push_github.sh "Votre message de commit"
```

**Exemples :**
```bash
./push_github.sh "Fix: Correction bug prédictions"
./push_github.sh "Feature: Ajout nouveaux indicateurs BRVM"
./push_github.sh "Update: Amélioration interface recommandations"
```

### 2️⃣ Push ultra-rapide

```bash
./push_rapide.sh
```

Message automatique avec date/heure : `Update: Modifications du 2025-12-29 16:45`

## Commandes Git Manuelles

### Vérifier l'état
```bash
git status
```

### Voir les différences
```bash
git diff                    # Changements non staged
git diff --staged          # Changements staged
```

### Ajouter des fichiers
```bash
git add .                          # Tous les fichiers
git add fichier.py                 # Un fichier spécifique
git add dashboard/                 # Un dossier complet
```

### Créer un commit
```bash
git commit -m "Votre message"
```

### Pousser vers GitHub
```bash
git push                           # Branche actuelle
git push origin main              # Branche main spécifiquement
```

### Annuler des modifications
```bash
git checkout -- fichier.py         # Annuler modifs d'un fichier
git reset HEAD fichier.py          # Unstage un fichier
git reset --soft HEAD~1            # Annuler dernier commit (garder modifs)
git reset --hard HEAD~1            # Annuler dernier commit (tout supprimer)
```

### Voir l'historique
```bash
git log                            # Historique complet
git log --oneline                  # Historique condensé
git log -5                         # 5 derniers commits
```

## Workflow Recommandé

### Pour petites modifications
```bash
./push_rapide.sh
```

### Pour modifications importantes
```bash
./push_github.sh "Feature: Description claire de la fonctionnalité"
```

### Pour corrections de bugs
```bash
./push_github.sh "Fix: Correction du bug X dans Y"
```

### Pour mises à jour de données
```bash
./push_github.sh "Data: Mise à jour cours BRVM du $(date +%d-%m-%Y)"
```

## Messages de Commit - Conventions

### Préfixes recommandés
- `Feature:` - Nouvelle fonctionnalité
- `Fix:` - Correction de bug
- `Update:` - Mise à jour
- `Data:` - Modifications de données
- `Docs:` - Documentation
- `Style:` - Modifications CSS/UI
- `Refactor:` - Refactorisation code
- `Test:` - Ajout/modification tests
- `Chore:` - Tâches maintenance

### Exemples de bons messages
```
✅ Feature: Ajout système de prédictions ML avec charts rouge/vert
✅ Fix: Correction erreur 500 sur API stock_prediction
✅ Data: Collecte automatique 47 actions BRVM
✅ Update: Amélioration performance dashboard WorldBank
✅ Docs: Ajout guide utilisation API REST
```

### À éviter
```
❌ update
❌ fix bug
❌ modif
❌ test
```

## Vérifications Avant Push

### 1. Tester localement
```bash
python manage.py runserver
# Vérifier que tout fonctionne
```

### 2. Vérifier la qualité des données
```bash
python show_complete_data.py
python verifier_connexion_db.py
```

### 3. Vérifier les fichiers à envoyer
```bash
git status
git diff
```

### 4. Push !
```bash
./push_github.sh "Votre message"
```

## Résolution de Problèmes

### Conflit de merge
```bash
git pull origin main           # Récupérer les changements
# Résoudre conflits dans les fichiers
git add .
git commit -m "Merge: Résolution conflits"
git push
```

### Fichiers trop gros
```bash
# Ajouter au .gitignore
echo "fichier_volumineux.zip" >> .gitignore
git rm --cached fichier_volumineux.zip
git commit -m "Remove: Fichier volumineux"
```

### Push refusé
```bash
git pull --rebase origin main  # Récupérer et rebaser
git push
```

## Raccourcis Utiles

```bash
# Alias Git (ajouter dans ~/.gitconfig)
[alias]
    st = status
    co = commit
    cm = commit -m
    br = branch
    ps = push
    pl = pull
    lg = log --oneline --graph --decorate
```

## Lien du Dépôt

🔗 **GitHub Repository:** https://github.com/sanaboukary/ecodata

---

**Dernière mise à jour:** 29 décembre 2025

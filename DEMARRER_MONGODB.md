# DEMARRER MONGODB - Guide Windows

## ⚠️ MongoDB doit être démarré AVANT de vérifier les données

### Option 1: Service Windows (Recommandé)
```cmd
# PowerShell en tant qu'Administrateur
net start MongoDB
```

### Option 2: MongoDB Compass
1. Ouvrir MongoDB Compass
2. Cliquer "Connect" sur localhost:27017
3. Cela démarre automatiquement MongoDB

### Option 3: Démarrage manuel
```bash
# Trouver MongoDB
"C:/Program Files/MongoDB/Server/6.0/bin/mongod.exe" --dbpath "C:/data/db"

# OU si installé ailleurs
"C:/Program Files/MongoDB/Server/7.0/bin/mongod.exe" --dbpath "C:/data/db"
```

### Vérifier que MongoDB tourne
```bash
# Dans Git Bash
ps aux | grep mongod

# OU tester la connexion
python check_db_simple.py
```

## Ensuite, vérifier les données RÉELLES
```bash
python verifier_donnees_reelles.py
```

## Politique ZÉRO TOLÉRANCE
- ✅ **REAL_MANUAL**: Données saisies manuellement (BRVM)
- ✅ **REAL_SCRAPER**: Données scrapées du site BRVM
- ❌ **Toute autre valeur**: DONNÉES SIMULÉES - À SUPPRIMER!

## Nettoyer les données simulées
```bash
python nettoyer_donnees_simulees.py
```

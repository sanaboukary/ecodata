# Guide d'utilisation

## Dashboard principal

### Accéder au dashboard
Ouvrez votre navigateur et allez sur : **http://localhost:8000**

Le dashboard affiche :
- Vue d'ensemble des indicateurs
- Graphiques de tendances
- Dernières mises à jour

## Explorateur de données

### Accès
URL : **http://localhost:8000/explorer/**

### Fonctionnalités

#### 1. Recherche d'indicateurs
- Tapez le nom d'un indicateur dans la barre de recherche
- L'autocomplétion vous suggère des indicateurs disponibles
- Sélectionnez un ou plusieurs indicateurs

#### 2. Sélection de pays
- Recherchez un pays par nom
- Ajoutez plusieurs pays pour comparaison
- Visualisez les données côte à côte

#### 3. Filtrage temporel
- Choisissez une plage de dates
- Filtrez par année, décennie, etc.

#### 4. Export des données
- Cliquez sur "Exporter CSV"
- Les données filtrées sont téléchargées
- Format compatible Excel

#### 5. Favoris
- Sauvegardez vos recherches favorites
- Accédez rapidement aux indicateurs fréquents

## Comparateur

### Accès
URL : **http://localhost:8000/comparateur/**

### Usage
1. Sélectionnez 2+ pays
2. Choisissez un indicateur commun
3. Visualisez la comparaison graphique
4. Exportez les résultats

## Administration

### Accès
URL : **http://localhost:8000/administration/**

Nécessite une authentification admin.

### Fonctionnalités admin
- Gestion des sources de données
- Visualisation des logs d'ingestion
- Statistiques d'utilisation
- Configuration système

## API REST

### Endpoints disponibles

#### Santé de l'ingestion
```bash
GET /api/ingestion/health/
```

Réponse :
```json
{
  "status": "ok",
  "mongodb": "connected",
  "last_ingestion": "2025-11-06T10:30:00Z"
}
```

#### Démarrer l'ingestion
```bash
POST /api/ingestion/start/
Content-Type: application/json

{
  "scripts_dir": "./scripts",
  "pattern": "*.py"
}
```

Réponse :
```json
{
  "status": "started",
  "message": "Ingestion démarrée"
}
```

#### Liste des KPIs
```bash
GET /api/kpis/
```

#### Données de l'explorateur
```bash
GET /explorer/data/?indicator=GDP&country=BEN&start_year=2010&end_year=2020
```

## Commandes de gestion

### Ingestion manuelle

#### Par source spécifique
```bash
# BRVM
python manage.py ingest_source --source brvm

# Banque Mondiale
python manage.py ingest_source --source worldbank --years 2010-2020

# FMI
python manage.py ingest_source --source imf

# ONU (SDG)
python manage.py ingest_source --source un

# BAD (AfDB)
python manage.py ingest_source --source afdb
```

#### Options disponibles
```bash
python manage.py ingest_source --help

Options:
  --source TEXT    Source de données (brvm, worldbank, imf, un, afdb)
  --years TEXT     Plage d'années (ex: 2010-2020)
  --countries TEXT Liste de pays (ex: BEN,TGO,CIV)
  --indicators TEXT Liste d'indicateurs spécifiques
  --verbose        Mode verbeux
```

### Scheduler automatique

#### Démarrer le scheduler BRVM
```bash
python manage.py start_scheduler
```

Le scheduler :
- Récupère les données BRVM toutes les heures
- Tourne en continu (arrêter avec Ctrl+C)
- Log les opérations dans `logs/scheduler.log`

#### En arrière-plan (Linux/Mac)
```bash
nohup python manage.py start_scheduler > logs/scheduler.log 2>&1 &
```

#### Arrêter le scheduler
```bash
# Trouver le PID
ps aux | grep start_scheduler

# Tuer le processus
kill <PID>
```

### Autres commandes utiles

#### Nettoyer les données anciennes
```bash
python manage.py cleanup_old_data --days 365
```

#### Vérifier l'intégrité des données
```bash
python manage.py check_data_integrity
```

#### Statistiques
```bash
python manage.py data_stats
```

## Exports

### Export CSV depuis l'explorateur
1. Configurez vos filtres
2. Cliquez sur "Exporter CSV"
3. Le fichier est téléchargé automatiquement

### Export CSV depuis le comparateur
```bash
GET /comparateur/export/?countries=BEN,TGO&indicator=GDP
```

### Export via API
```bash
GET /explorer/export/?format=csv&indicator=GDP&country=BEN
```

## Gestion des favoris

### Ajouter un favori
```bash
POST /explorer/favorite/
Content-Type: application/json

{
  "indicator": "GDP",
  "country": "BEN",
  "name": "PIB Bénin"
}
```

### Liste des favoris
```bash
GET /explorer/favorites/
```

## Monitoring

### Logs applicatifs
Les logs sont stockés dans `logs/` :
- `server.log` : logs du serveur Django
- `scheduler.log` : logs du scheduler
- `ingestion.log` : logs d'ingestion

### Visualiser les logs en temps réel
```bash
tail -f logs/server.log
tail -f logs/scheduler.log
```

### Rotation des logs
Les logs sont automatiquement archivés après 30 jours.

## Bonnes pratiques

### Performance
- Limitez les plages de dates pour les exports
- Utilisez les filtres pour réduire les données
- Mettez en cache les requêtes fréquentes

### Sécurité
- Changez `DJANGO_SECRET_KEY` en production
- Désactivez `DEBUG=False` en production
- Utilisez HTTPS en production
- Authentifiez les endpoints sensibles

### Maintenance
- Exécutez les mises à jour d'ingestion régulièrement
- Surveillez l'espace disque MongoDB
- Sauvegardez régulièrement la base de données

## Dépannage

### Le dashboard ne charge pas
1. Vérifiez que le serveur est démarré
2. Vérifiez MongoDB : `mongo --eval "db.version()"`
3. Consultez les logs : `tail -f logs/server.log`

### Pas de données dans l'explorateur
1. Lancez une ingestion : `python manage.py ingest_source --source worldbank`
2. Vérifiez MongoDB : `mongo centralisation_db` puis `db.indicators.count()`
3. Rechargez la page

### L'ingestion échoue
1. Vérifiez la connexion Internet
2. Vérifiez les logs : `tail -f logs/ingestion.log`
3. Testez la connexion MongoDB
4. Réessayez avec `--verbose` pour plus de détails

## Support

Pour toute question :
- Consultez les logs d'erreur
- Vérifiez la [documentation API](API.md)
- Référez-vous à l'[architecture ETL](ETL.md)

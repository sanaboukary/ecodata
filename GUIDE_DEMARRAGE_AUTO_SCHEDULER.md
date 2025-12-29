# ============================================================================
# Guide d'installation du démarrage automatique du scheduler
# ============================================================================

## 🎯 Objectif
Configurer le démarrage automatique du scheduler à **8h50 chaque jour**

## 📋 Prérequis
- Windows 10/11
- Droits administrateur
- PowerShell

## 🚀 Installation (2 méthodes)

### Méthode 1 : Automatique (Recommandée)

1. **Ouvrir PowerShell en tant qu'administrateur**
   - Clic droit sur le menu Démarrer → "Windows PowerShell (Admin)"
   - Ou chercher "PowerShell" → Clic droit → "Exécuter en tant qu'administrateur"

2. **Naviguer vers le projet**
   ```powershell
   cd "E:\DISQUE C\Desktop\Implementation plateforme"
   ```

3. **Autoriser l'exécution de scripts** (si première fois)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Exécuter le script d'installation**
   ```powershell
   .\setup_scheduler_task.ps1
   ```

5. **Suivre les instructions**
   - Le script va créer la tâche planifiée
   - Vous pouvez tester immédiatement (optionnel)

### Méthode 2 : Manuelle

1. **Ouvrir le Planificateur de tâches**
   - Touche Windows + R
   - Taper : `taskschd.msc`
   - Appuyer sur Entrée

2. **Créer une nouvelle tâche**
   - Clic droit sur "Bibliothèque du Planificateur de tâches"
   - "Créer une tâche..." (pas "Créer une tâche de base")

3. **Onglet Général**
   - Nom : `PlateformeScheduler`
   - Description : `Démarre le scheduler de la plateforme à 8h50`
   - Cocher "Exécuter même si l'utilisateur n'est pas connecté" (optionnel)

4. **Onglet Déclencheurs**
   - Clic "Nouveau..."
   - Commencer la tâche : "Selon une planification"
   - Quotidien
   - Heure : 08:50:00
   - Répéter tous les jours : 1
   - OK

5. **Onglet Actions**
   - Clic "Nouveau..."
   - Action : "Démarrer un programme"
   - Programme : `cmd.exe`
   - Arguments : `/c "E:\DISQUE C\Desktop\Implementation plateforme\start_scheduler_daily.bat"`
   - Commencer dans : `E:\DISQUE C\Desktop\Implementation plateforme`
   - OK

6. **Onglet Paramètres**
   - Cocher "Autoriser le démarrage de la tâche à la demande"
   - Cocher "Exécuter la tâche dès que possible après un démarrage planifié manqué"
   - OK

## ✅ Vérification

### Vérifier que la tâche est créée
```powershell
Get-ScheduledTask -TaskName "PlateformeScheduler"
```

### Tester immédiatement (sans attendre 8h50)
```powershell
Start-ScheduledTask -TaskName "PlateformeScheduler"
```

### Vérifier que le scheduler tourne
```powershell
Get-Process python | Where-Object { $_.MainWindowTitle -like "Scheduler*" }
```

### Voir les logs
Les logs sont dans : `logs\scheduler_YYYYMMDD.log`

## 🛠️ Gestion de la tâche

### Désactiver temporairement
```powershell
Disable-ScheduledTask -TaskName "PlateformeScheduler"
```

### Réactiver
```powershell
Enable-ScheduledTask -TaskName "PlateformeScheduler"
```

### Supprimer la tâche
```powershell
Unregister-ScheduledTask -TaskName "PlateformeScheduler" -Confirm:$false
```

### Modifier l'heure (exemple : 9h00 au lieu de 8h50)
1. Ouvrir le Planificateur de tâches (`taskschd.msc`)
2. Trouver "PlateformeScheduler"
3. Clic droit → "Propriétés"
4. Onglet "Déclencheurs"
5. Double-clic sur le déclencheur
6. Modifier l'heure
7. OK

## 📊 Fonctionnement

**À 8h50 chaque jour**, la tâche planifiée va :

1. ✅ Vérifier si un scheduler tourne déjà (et l'arrêter si nécessaire)
2. ✅ Démarrer un nouveau scheduler en arrière-plan
3. ✅ Créer un fichier de log : `logs\scheduler_YYYYMMDD.log`
4. ✅ Le scheduler va collecter automatiquement :
   - **BRVM** : Toutes les heures de 9h à 16h (lundi-vendredi)
   - **WorldBank** : Le 15 du mois à 2h00
   - **IMF** : Le 1er du mois à 2h30
   - **AfDB & UN SDG** : Tous les trimestres (jan/avr/jul/oct) à 3h00/3h15

## 🔍 Dépannage

### La tâche ne démarre pas
1. Vérifier les logs : `logs\scheduler_*.log`
2. Vérifier que MongoDB est actif (port 27017)
3. Tester manuellement : `start_scheduler_daily.bat`

### Arrêter manuellement le scheduler
```cmd
taskkill /FI "WINDOWTITLE eq Scheduler*" /F
```

### Permission refusée lors de la création de la tâche
- Exécuter PowerShell **en tant qu'administrateur**

### Le scheduler se ferme immédiatement
- Vérifier les dépendances : `.venv\Scripts\python.exe` existe
- Vérifier Django : `python manage.py check`
- Vérifier MongoDB : `mongosh --eval "db.version()"`

## 📝 Notes importantes

- Le scheduler tourne **en continu** une fois démarré (pas besoin de redémarrer toutes les heures)
- Les collectes sont programmées **à l'intérieur** du scheduler selon les horaires configurés
- Si l'ordinateur est éteint à 8h50, la tâche démarrera dès l'allumage (option "Exécuter dès que possible après un démarrage manqué")
- Un seul scheduler peut tourner à la fois (le script arrête l'ancien avant de démarrer le nouveau)

## 🎉 Avantages de cette solution

✅ **Démarrage automatique** - Plus besoin de lancer manuellement  
✅ **Résilient** - Redémarre automatiquement après un crash/redémarrage PC  
✅ **Logs** - Tous les événements sont enregistrés  
✅ **Léger** - APScheduler est plus simple qu'Airflow sous Windows  
✅ **Fiable** - Testé sous Windows 10/11  

## 📞 Support

En cas de problème, vérifier :
1. Les logs dans `logs/scheduler_*.log`
2. Le statut de la tâche : `Get-ScheduledTask -TaskName "PlateformeScheduler"`
3. Les processus Python actifs : `Get-Process python`

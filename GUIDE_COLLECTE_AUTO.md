# CONFIGURATION DE LA COLLECTE AUTOMATIQUE
## Toutes les 25 minutes pour BRVM + Planning mensuel/trimestriel pour autres sources

### 📋 RÉSUMÉ DE LA CONFIGURATION

**Fichiers créés :**
1. `collect_all_sources_smart.bat` - Script intelligent de collecte
2. `setup_auto_collect_task.ps1` - Configuration PowerShell de la tâche
3. `CONFIGURER_COLLECTE_AUTO.bat` - Script de configuration avec droits admin

### ⚙️ FRÉQUENCES DE COLLECTE

#### BRVM (Bourse)
- **Fréquence** : Toutes les 25 minutes
- **Horaires** : 8h00 - 20h00 (heures de travail)
- **Jours** : Tous les jours

#### WorldBank (Banque Mondiale)
- **Fréquence** : 1 fois par mois
- **Date** : Le 15 de chaque mois
- **Indicateurs** : Population, PIB, Inflation, Chômage, Éducation

#### IMF (Fonds Monétaire International)
- **Fréquence** : 1 fois par mois
- **Date** : Le 1er de chaque mois
- **Indicateurs** : Indices des prix, PIB réel

#### UN SDG & AfDB
- **Fréquence** : Trimestrielle
- **Dates** : 01/01, 01/04, 01/07, 01/10
- **Indicateurs** : Objectifs de développement durable, Croissance, Inflation

### 🚀 INSTALLATION

**ÉTAPE 1 : Lancer la configuration**
```bash
# Clic droit sur CONFIGURER_COLLECTE_AUTO.bat
# Sélectionner "Exécuter en tant qu'administrateur"
```

**ÉTAPE 2 : Vérifier l'installation**
```powershell
Get-ScheduledTask -TaskName "PlateformeCollecteAuto" | Get-ScheduledTaskInfo
```

### ✅ VÉRIFICATION

**Voir les logs en temps réel :**
```bash
tail -f logs/smart_collect_*.log
```

**Vérifier les dernières collectes BRVM :**
```bash
.venv\Scripts\python.exe check_brvm_updates.py
```

**Déclencher manuellement :**
```bash
# Pour tester immédiatement
.\collect_all_sources_smart.bat

# Ou via le Gestionnaire des tâches :
# Clic droit sur "PlateformeCollecteAuto" > Exécuter
```

### 📊 MONITORING

**Gestionnaire des tâches Windows :**
1. Ouvrir le Gestionnaire des tâches
2. Onglet "Planificateur de tâches"
3. Chercher "PlateformeCollecteAuto"
4. Voir : Dernière exécution, Prochaine exécution, Historique

**Logs disponibles :**
- `logs/smart_collect_YYYYMMDD.log` - Logs quotidiens de collecte
- `logs/brvm_auto_collect.log` - Si vous utilisez l'ancien script

### 🔧 GESTION

**Désactiver temporairement :**
```powershell
Disable-ScheduledTask -TaskName "PlateformeCollecteAuto"
```

**Réactiver :**
```powershell
Enable-ScheduledTask -TaskName "PlateformeCollecteAuto"
```

**Modifier la fréquence :**
1. Éditer `setup_auto_collect_task.ps1`
2. Changer `-RepetitionInterval (New-TimeSpan -Minutes 25)` à la durée souhaitée
3. Relancer `CONFIGURER_COLLECTE_AUTO.bat` en admin

**Supprimer la tâche :**
```powershell
Unregister-ScheduledTask -TaskName "PlateformeCollecteAuto" -Confirm:$false
```

### 📈 STATISTIQUES ATTENDUES

**Par jour (25 min = ~29 exécutions de 8h à 20h) :**
- BRVM : ~29 × 47 actions = **~1,363 observations/jour**

**Par mois :**
- BRVM : ~40,890 observations
- WorldBank : ~75 observations (5 indicateurs × 15 pays)
- IMF : ~20 observations (2 indicateurs × 10 pays)

**Par trimestre :**
- UN SDG : ~16 observations
- AfDB : ~16 observations

### ⚠️ DÉPANNAGE

**La tâche ne s'exécute pas :**
1. Vérifier les droits admin lors de la création
2. Vérifier que le chemin du script est correct
3. Consulter l'historique dans le Gestionnaire des tâches

**Pas de nouvelles données :**
1. Vérifier les logs : `logs/smart_collect_*.log`
2. Tester manuellement : `.\collect_all_sources_smart.bat`
3. Vérifier MongoDB : `check_brvm_updates.py`

**Erreurs dans les logs :**
- Vérifier la connexion MongoDB
- Vérifier les variables d'environnement (.env)
- Tester les sources individuellement

### 📝 NOTES IMPORTANTES

- La tâche s'exécute même si vous n'êtes pas connecté
- Les logs sont conservés par jour (un fichier par jour)
- Toutes les sources utilisent des données mock si les API réelles ne sont pas configurées
- BRVM collecte 47 actions de la bourse ouest-africaine
- Les pays couverts : Bénin, Burkina Faso, Côte d'Ivoire, Ghana, Guinée, Liberia, Mali, Niger, Nigeria, Sénégal, Togo, Gambie, Guinée-Bissau, Sierra Leone, Cap-Vert

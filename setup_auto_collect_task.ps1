# Script de configuration de la tâche planifiée
# Collecte BRVM toutes les 25 minutes + autres sources selon planning

$taskName = "PlateformeCollecteAuto"
$scriptPath = "E:\DISQUE C\Desktop\Implementation plateforme\collect_all_sources_smart.bat"
$workingDir = "E:\DISQUE C\Desktop\Implementation plateforme"

# Action : Exécuter le script de collecte
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`"" -WorkingDirectory $workingDir

# Déclencheur : Toutes les 25 minutes de 8h à 18h, tous les jours
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Répétition : Toutes les 25 minutes pendant 12 heures (8h-20h)
$trigger.Repetition = New-ScheduledTaskTrigger -Once -At 8:00AM -RepetitionInterval (New-TimeSpan -Minutes 25) -RepetitionDuration (New-TimeSpan -Hours 12) | Select-Object -ExpandProperty Repetition

# Paramètres : Exécuter même si l'utilisateur n'est pas connecté
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Settings : Autoriser l'exécution à la demande, ne pas arrêter si longue durée
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Enregistrer la tâche
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Write-Host "============================================"
Write-Host "TACHE PLANIFIEE CONFIGUREE AVEC SUCCES"
Write-Host "============================================"
Write-Host ""
Write-Host "Nom: $taskName"
Write-Host "Frequence: Toutes les 25 minutes (8h-20h)"
Write-Host "Script: $scriptPath"
Write-Host ""
Write-Host "Contenu:"
Write-Host "  - BRVM: Toutes les 25 min"
Write-Host "  - WorldBank: Le 15 de chaque mois"
Write-Host "  - IMF: Le 1er de chaque mois"
Write-Host "  - UN SDG & AfDB: Debut de trimestre (01/01, 01/04, 01/07, 01/10)"
Write-Host ""

# Afficher les prochaines exécutions
Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo | Select-Object TaskName, LastRunTime, NextRunTime | Format-List

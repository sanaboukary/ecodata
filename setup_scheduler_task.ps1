# ============================================================================
# Script PowerShell pour créer une tâche planifiée Windows
# Démarre le scheduler automatiquement à 8h50 chaque jour
# ============================================================================

$TaskName = "PlateformeScheduler"
$ScriptPath = Join-Path $PSScriptRoot "start_scheduler_daily.bat"
$WorkingDir = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Configuration Tache Planifiee Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si la tâche existe déjà
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "[INFO] Tache '$TaskName' existe deja" -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous la remplacer? (O/N)"
    
    if ($response -eq "O" -or $response -eq "o") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Ancienne tache supprimee" -ForegroundColor Green
    } else {
        Write-Host "[ANNULE] Configuration abandonnee" -ForegroundColor Red
        exit
    }
}

# Créer l'action (commande à exécuter)
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Créer le déclencheur (8h50 chaque jour)
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "08:50"

# Paramètres de la tâche
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)

# Utilisateur actuel
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# Enregistrer la tâche
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Demarre automatiquement le scheduler de la plateforme de centralisation a 8h50 chaque jour" `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "[OK] Tache planifiee creee avec succes!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details de la tache:" -ForegroundColor Cyan
    Write-Host "  Nom       : $TaskName" -ForegroundColor White
    Write-Host "  Heure     : 8h50 (tous les jours)" -ForegroundColor White
    Write-Host "  Script    : $ScriptPath" -ForegroundColor White
    Write-Host "  Utilisateur: $env:USERNAME" -ForegroundColor White
    Write-Host ""
    Write-Host "Commandes utiles:" -ForegroundColor Yellow
    Write-Host "  Afficher la tache  : Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Executer maintenant: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Desactiver         : Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Supprimer          : Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    
    # Demander si on veut tester immédiatement
    $test = Read-Host "Voulez-vous tester le demarrage maintenant? (O/N)"
    if ($test -eq "O" -or $test -eq "o") {
        Write-Host ""
        Write-Host "[INFO] Execution de la tache..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
        
        # Vérifier si le scheduler tourne
        $process = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "Scheduler*" }
        if ($process) {
            Write-Host "[OK] Scheduler demarre avec succes (PID: $($process.Id))" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Verifiez les logs dans le dossier 'logs/'" -ForegroundColor Yellow
        }
    }
    
} catch {
    Write-Host ""
    Write-Host "[ERREUR] Impossible de creer la tache planifiee" -ForegroundColor Red
    Write-Host "Message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Assurez-vous d'executer ce script en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Configuration terminee!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

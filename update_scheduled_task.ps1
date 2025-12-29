# Script pour modifier la tâche planifiée - Collecte BRVM toutes les 25 minutes

# Exporter la tâche actuelle
$taskPath = "E:\DISQUE C\Desktop\Implementation plateforme\task_temp.xml"
Export-ScheduledTask -TaskName "PlateformeScheduler" | Out-File $taskPath

# Lire et modifier le XML
[xml]$taskXml = Get-Content $taskPath

# Modifier le trigger pour répétition toutes les 25 minutes
$repetition = $taskXml.Task.Triggers.CalendarTrigger.Repetition
if ($repetition -eq $null) {
    $repetition = $taskXml.CreateElement("Repetition", $taskXml.Task.NamespaceURI)
    $taskXml.Task.Triggers.CalendarTrigger.AppendChild($repetition) | Out-Null
}

# Créer ou modifier les éléments Interval et Duration
$interval = $taskXml.CreateElement("Interval", $taskXml.Task.NamespaceURI)
$interval.InnerText = "PT25M"
$duration = $taskXml.CreateElement("Duration", $taskXml.Task.NamespaceURI)
$duration.InnerText = "P1D"

# Nettoyer les anciens éléments s'ils existent
$taskXml.Task.Triggers.CalendarTrigger.Repetition.RemoveAll()
$taskXml.Task.Triggers.CalendarTrigger.Repetition.AppendChild($interval) | Out-Null
$taskXml.Task.Triggers.CalendarTrigger.Repetition.AppendChild($duration) | Out-Null

# Modifier l'action pour utiliser le script de collecte rapide
$taskXml.Task.Actions.Exec.Command = "cmd.exe"
$taskXml.Task.Actions.Exec.Arguments = '/c "E:\DISQUE C\Desktop\Implementation plateforme\collect_brvm_25min.bat"'

# Sauvegarder
$taskXml.Save($taskPath)

# Réimporter la tâche
Register-ScheduledTask -TaskName "PlateformeScheduler" -Xml (Get-Content $taskPath | Out-String) -Force | Out-Null

# Nettoyer
Remove-Item $taskPath

Write-Host "Tache modifiee avec succes !"
Write-Host "  - Collecte BRVM toutes les 25 minutes"
Write-Host "  - Demarre a 08:00 chaque jour"
Write-Host "  - Logs dans: logs\brvm_auto_collect.log"

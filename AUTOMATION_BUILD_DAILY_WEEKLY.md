# Automatisation (anti-oubli) : build daily / weekly

## Objectif
Ne plus oublier de lancer la construction :
- `prices_daily` (chaque soir)
- `prices_weekly` (chaque lundi)

Ces scripts utilisent le Python du venv si présent : `.venv/Scripts/python.exe`.

## Exécution manuelle
- Daily (aujourd'hui) : `RUN_BUILD_DAILY.cmd`
- Daily (hier, si tu as oublié) : `RUN_BUILD_DAILY.cmd --yesterday`
- Daily (date précise) : `RUN_BUILD_DAILY.cmd --date 2026-02-21`
- Weekly : `RUN_BUILD_WEEKLY.cmd`

## Planificateur de tâches Windows (recommandé)
Ouvre : Menu Démarrer → **Planificateur de tâches** → **Créer une tâche…**

### Tâche 1 — Daily (lun-ven)
- **Déclencheur** : Quotidien, du lundi au vendredi, à une heure après ta dernière collecte (ex: 18:30 ou 19:00)
- **Action** : Démarrer un programme
  - Programme/script : `E:\DISQUE C\Desktop\Implementation plateforme\RUN_BUILD_DAILY.cmd`
  - Démarrer dans (important) : `E:\DISQUE C\Desktop\Implementation plateforme`
- **Option utile** : Cocher "Exécuter même si l’utilisateur n’est pas connecté" si tu veux.

### Tâche 2 — Weekly (lundi)
- **Déclencheur** : Hebdomadaire, lundi (ex: 07:00)
- **Action** :
  - Programme/script : `E:\DISQUE C\Desktop\Implementation plateforme\RUN_BUILD_WEEKLY.cmd`
  - Démarrer dans : `E:\DISQUE C\Desktop\Implementation plateforme`

## Astuce si tu as raté le soir
Le lendemain matin (ou à tout moment) :
- `RUN_BUILD_DAILY.cmd --yesterday`
Puis si besoin :
- `RUN_BUILD_WEEKLY.cmd`

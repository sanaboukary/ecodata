# BRVM Pipeline Professionnelle

## Structure

- collecter_publications_brvm.py : collecte des publications et données brutes
- extraction_semantique_brvm.py : extraction sémantique et scoring
- agregateur_semantique_actions.py : agrégation des signaux sémantiques par action
- analyse_ia_simple.py : analyse IA, scoring technique et sémantique
- decision_finale_brvm.py : moteur de décision unifié par horizon (semaine, mois, trimestre, annuel)
- explain_decision_brvm.py : génération d'explications professionnelles pour chaque décision
- orchestrateur_brvm.py : automatisation de l'exécution du pipeline

## Usage

Lancer le pipeline complet :
```
./.venv/Scripts/python.exe brvm_pipeline/orchestrateur_brvm.py
```

Chaque script peut être lancé individuellement pour debug ou analyse spécifique.

## Logique de décision

La décision finale dépend de l'horizon sélectionné :
- Semaine : momentum, volatilité, technique
- Mois : catalyseur, confirmation, corrélation
- Trimestre : fondamentaux, trajectoire
- Annuel : dividendes, sécurité, volatilité faible

Les justifications sont affichées et exportées pour chaque action.

# 🎯 ARCHITECTURE 3 NIVEAUX - GUIDE COMPLET

[Voir README.md pour le guide complet](README_ARCHITECTURE_3_NIVEAUX.md)

## 🚀 DÉMARRAGE RAPIDE

### 1. Test initial
```bash
.venv\Scripts\python.exe brvm_pipeline/test_rapide.py
```

### 2. Reconstruction complète (première fois)
```bash
.venv\Scripts\python.exe brvm_pipeline/master_orchestrator.py --rebuild
```

### 3. Générer TOP5
```bash
.venv\Scripts\python.exe brvm_pipeline/top5_engine.py
```

---

## 📋 WORKFLOWS

### Quotidien (17h)
```bash
.venv\Scripts\python.exe brvm_pipeline/master_orchestrator.py --daily-update
```

### Hebdomadaire (lundi 8h)
```bash
.venv\Scripts\python.exe brvm_pipeline/master_orchestrator.py --weekly-update
```

---

## ⭐ FORMULE TOP5

```
= 0.30 × Expected_Return
+ 0.25 × Volume_Acceleration
+ 0.20 × Semantic_Score
+ 0.15 × WOS_Setup
+ 0.10 × Risk_Reward
```

**Objectif** : Être dans les 5 plus fortes hausses BRVM

---

Consultez [README_ARCHITECTURE_3_NIVEAUX.md](README_ARCHITECTURE_3_NIVEAUX.md) pour la documentation complète.

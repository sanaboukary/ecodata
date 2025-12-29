# 📋 Guide de Mise à Jour des Cours BRVM Réels

## 🎯 Objectif
Mettre à jour quotidiennement les cours BRVM avec les **vrais prix du marché** pour des analyses et trading fiables.

## 🕒 Quand mettre à jour ?
**Tous les jours à 17h30** (après la clôture BRVM à 16h30 GMT)

---

## 📝 Méthode 1 : Mise à Jour Rapide (RECOMMANDÉE)

### Étape 1 : Consulter les cours BRVM
Aller sur l'une de ces sources :
- **Site officiel** : https://www.brvm.org/fr/investir/cours-et-cotations
- **Bulletin quotidien** : PDF reçu par email (si abonné)
- **Courtier** : SGI, Impaxis, etc.

### Étape 2 : Ouvrir le fichier de mise à jour
```bash
# Ouvrir dans votre éditeur
notepad mettre_a_jour_cours_brvm_rapide.py
# ou
code mettre_a_jour_cours_brvm_rapide.py
```

### Étape 3 : Remplir les prix réels
Remplacer les `0` par les vrais cours :
```python
COURS_BRVM_AUJOURDHUI = {
    'SNTS': 13900,   # ← Remplacer par le vrai prix du jour
    'ECOC': 7500,    # ← Remplacer par le vrai prix du jour
    'BICC': 8200,    # ← Remplacer par le vrai prix du jour
    # ... etc
}
```

### Étape 4 : Exécuter la mise à jour
```bash
python mettre_a_jour_cours_brvm_rapide.py
```

### Étape 5 : Relancer l'analyse IA
```bash
python lancer_analyse_ia_complete.py
```

---

## 🤖 Méthode 2 : Collecte Semi-Automatique

### Option A : Bulletin PDF
Si vous recevez le bulletin quotidien par email :

1. **Télécharger le PDF** dans le dossier `bulletins/`
2. **Extraire les cours** :
```bash
python extraire_cours_bulletin_pdf.py bulletins/bulletin_2025-12-08.pdf
```
3. Le script met à jour automatiquement la base

### Option B : API Courtier (si disponible)
Si votre courtier (SGI, Impaxis) fournit une API :

1. **Configurer les identifiants** dans `.env` :
```env
COURTIER_API_URL=https://api.courtier.com
COURTIER_API_KEY=votre_cle_ici
```

2. **Collecter automatiquement** :
```bash
python collecter_cours_courtier.py
```

---

## 🔍 Vérification Après Mise à Jour

### Vérifier les cours en base
```bash
python verifier_cours_brvm.py
```

Sortie attendue :
```
✅ 46 cours BRVM présents
✅ Dernière mise à jour: 2025-12-08 17:35:00
✅ Tous les cours datent de moins de 24h
```

### Comparer avec le marché
```bash
python comparer_cours_marche.py
```

Affiche les écarts entre vos prix et les prix du marché.

---

## ⚠️ Points d'Attention

### 1. Prix Incohérents
Si un prix semble anormal (variation > 10%), le système affichera une alerte :
```
⚠️ ALERTE: SNTS +15.3% (13900 → 16000 FCFA)
   Vérifier si le prix est correct avant validation
```

### 2. Actions Manquantes
Si certaines actions ne sont pas cotées un jour :
- Laisser le prix à `0` dans le fichier
- Le système conservera le prix du jour précédent

### 3. Volumes
Si vous avez accès aux volumes réels, ajoutez-les :
```python
COURS_BRVM_AUJOURDHUI = {
    'SNTS': {'prix': 13900, 'volume': 245000},  # ← Format avec volume
    'ECOC': {'prix': 7500, 'volume': 12500},
}
```

---

## 📊 Automatisation Future

### Option 1 : Web Scraping BRVM
**Statut** : Site BRVM retourne 404 (décembre 2025)
**Action** : Contacter la BRVM pour accès API

### Option 2 : API Officielle BRVM
**Coût** : Variable (contacter commercial@brvm.org)
**Avantages** : Données temps réel, historique complet

### Option 3 : Intégration Courtier
**Recommandé** : Si vous êtes client SGI, Impaxis, etc.
**Avantages** : Données officielles, support technique

---

## 📱 Mise à Jour depuis Mobile

### Via Email
1. **Envoyer un email** à votre adresse avec sujet "MAJ BRVM"
2. **Format corps email** :
```
SNTS=13900
ECOC=7500
BICC=8200
```
3. Le système parse l'email et met à jour automatiquement

### Via Telegram Bot (à configurer)
```
/update_brvm
SNTS 13900
ECOC 7500
BICC 8200
```

---

## 🆘 Dépannage

### Erreur : "Aucun prix renseigné"
**Cause** : Tous les prix sont à 0
**Solution** : Remplir au moins 1 prix > 0

### Erreur : "Connexion MongoDB"
**Cause** : MongoDB n'est pas démarré
**Solution** : 
```bash
net start MongoDB
```

### Erreur : "Import Django failed"
**Cause** : Environnement virtuel non activé
**Solution** :
```bash
source .venv/Scripts/activate  # Git Bash
# ou
.venv\Scripts\activate  # CMD
```

---

## 📈 Workflow Hebdomadaire Complet

### Lundi-Vendredi (17h30)
```bash
# 1. Mettre à jour les cours du jour
python mettre_a_jour_cours_brvm_rapide.py

# 2. Vérifier (optionnel)
python verifier_cours_brvm.py
```

### Dimanche (20h00)
```bash
# 1. Analyse IA hebdomadaire
python lancer_analyse_ia_complete.py

# 2. Consulter recommandations
# - Dashboard: http://localhost:8000/dashboard/brvm/
# - Fichier: recommandations_ia_latest.json

# 3. Diagnostic détaillé
python diagnostic_analyse_ia.py
```

---

## 💡 Conseils d'Expert

1. **Toujours vérifier** les cours avant de trader
2. **Comparer** avec au moins 2 sources (BRVM + courtier)
3. **Noter** les variations anormales (> 5%)
4. **Sauvegarder** les bulletins PDF pour audit
5. **Tester** les signaux IA sur un compte démo d'abord

---

## 📞 Support

**Problème technique** : Vérifier `check_system_status.py`
**Données incohérentes** : Consulter `STRATEGIE_COLLECTE_BRVM_REELLE.md`
**Questions BRVM** : https://www.brvm.org/fr/contact

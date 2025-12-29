"""
═══════════════════════════════════════════════════════════════════════════════
                    GUIDE - TABLEAU DE BORD BRVM EN TEMPS RÉEL
═══════════════════════════════════════════════════════════════════════════════

✅ VOTRE TABLEAU DE BORD EST DÉJÀ CONFIGURÉ POUR LE TEMPS RÉEL !

🔴 CONNEXION PERMANENTE ACTIVE
═══════════════════════════════════════════════════════════════════════════════

Le tableau de bord est DÉJÀ connecté en permanence à la base de données :

1. 📊 Mise à jour automatique : TOUTES LES 10 SECONDES
   - Graphiques actualisés en direct
   - Indicateurs techniques recalculés
   - Signal d'analyse mis à jour

2. 🔌 Connexion MongoDB : PERMANENTE
   - Accès direct aux données stockées
   - Pas de déconnexion automatique
   - Lecture en temps réel

3. 🔴 Mode LIVE : ACTIVÉ
   - Récupération des données BRVM en direct
   - Cache intelligent (30 secondes)
   - Fallback sur MongoDB si erreur

4. 📈 Données actualisées automatiquement :
   ✓ Prix (Open/High/Low/Close)
   ✓ Volume
   ✓ Moyennes mobiles (MA5, MA10, MA20)
   ✓ RSI (Relative Strength Index)
   ✓ Signal d'achat/vente
   ✓ Support/Résistance


🚀 COMMENT DÉMARRER LE TABLEAU DE BORD
═══════════════════════════════════════════════════════════════════════════════

MÉTHODE 1 - Double-clic sur le fichier (RECOMMANDÉ)
────────────────────────────────────────────────────────────────────────────────
1. Ouvrir l'Explorateur Windows
2. Double-cliquer sur : DEMARRER_DASHBOARD_BRVM.bat
3. Le tableau de bord démarre automatiquement
4. Ouvrir : http://127.0.0.1:8050


MÉTHODE 2 - Ligne de commande
────────────────────────────────────────────────────────────────────────────────
cd "E:/DISQUE C/Desktop/Implementation plateforme"
.venv/Scripts/python.exe dashboard_brvm_expert.py


📊 COMMENT UTILISER L'ANALYSE EN TEMPS RÉEL
═══════════════════════════════════════════════════════════════════════════════

1. SÉLECTIONNER UNE ACTION
   - Utiliser le dropdown en haut
   - Choisir parmi 47 actions BRVM
   - Ou "BRVM Composite" pour tout voir

2. OBSERVER LE SIGNAL D'ANALYSE
   🟢 ACHAT FORT : Tendance très positive, bon moment d'achat
   🟢 ACHAT : Tendance positive, envisager l'achat
   ⚪ NEUTRE : Pas de signal clair, attendre
   🔴 VENTE : Tendance négative, envisager la vente
   🔴 VENTE FORTE : Tendance très négative, vendre

3. VÉRIFIER LES INDICATEURS TECHNIQUES
   - RSI < 30 : Action sous-évaluée (opportunité d'achat)
   - RSI > 70 : Action surévaluée (risque de correction)
   - Prix > MA5/MA10 : Tendance haussière
   - Volume élevé : Fort intérêt du marché

4. ANALYSER LE GRAPHIQUE
   - Chandeliers verts : Hausse
   - Chandeliers rouges : Baisse
   - Prix proche du support : Bon point d'entrée
   - Prix proche de la résistance : Attention


🔄 FRÉQUENCE DE MISE À JOUR
═══════════════════════════════════════════════════════════════════════════════

• Graphiques : 10 secondes
• Données BRVM : 30 secondes (cache)
• MongoDB : Lecture instantanée
• Indicateurs : Recalculés à chaque mise à jour


💡 CONSEILS POUR L'ANALYSE
═══════════════════════════════════════════════════════════════════════════════

✓ Ne pas se fier à UN SEUL indicateur
✓ Attendre la convergence de plusieurs signaux :
  - Signal d'analyse + RSI + Moyennes mobiles
  - Volume élevé confirme la tendance
  - Prix au-dessus des MA = Confirmation haussière

✓ Utiliser les variations :
  - 1J : Tendance immédiate
  - 5J : Tendance court terme
  - 10J : Tendance moyen terme

✓ Surveiller la volatilité :
  - Faible (<2%) : Action stable, moins risquée
  - Élevée (>5%) : Action volatile, plus risquée


🛠️ DÉPANNAGE
═══════════════════════════════════════════════════════════════════════════════

Problème : "Données insuffisantes"
Solution : 
  1. Attendre quelques minutes (les données se chargent)
  2. Vérifier que MongoDB est actif : docker start centralisation_db
  3. Lancer une collecte : python collecte_brvm_multiple.py -n 20

Problème : Le tableau de bord ne s'actualise pas
Solution :
  1. Vérifier que le tableau de bord est lancé
  2. Rafraîchir la page (F5)
  3. Vider le cache du navigateur (Ctrl+Shift+Delete)

Problème : "Erreur de connexion"
Solution :
  1. Vérifier Docker Desktop est lancé
  2. Démarrer MongoDB : docker start centralisation_db
  3. Relancer le tableau de bord


📞 RÉSUMÉ RAPIDE
═══════════════════════════════════════════════════════════════════════════════

✅ Connexion permanente : DÉJÀ CONFIGURÉE
✅ Mise à jour automatique : 10 SECONDES
✅ Mode temps réel : ACTIVÉ
✅ Pas de configuration supplémentaire nécessaire !

➡️ Double-cliquer sur DEMARRER_DASHBOARD_BRVM.bat
➡️ Ouvrir http://127.0.0.1:8050
➡️ Commencer l'analyse !

═══════════════════════════════════════════════════════════════════════════════
"""

print(__doc__)

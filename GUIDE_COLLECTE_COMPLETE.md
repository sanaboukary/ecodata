================================================================================
GUIDE COLLECTE DONNÉES COMPLÈTES BRVM - 8 Décembre 2025
================================================================================

🎯 OBJECTIF: Collecter TOUTES les données pour chaque action (cours + fondamentaux)

📋 DONNÉES À COLLECTER (par action):
================================================================================

1. COURS ET VOLUME:
   ✓ Prix d'ouverture (open)
   ✓ Prix le plus haut (high)
   ✓ Prix le plus bas (low)
   ✓ Prix de clôture (close)
   ✓ Volume échangé (volume)
   ✓ Variation du jour (%)
   ✓ Variation 90 jours (%)

2. VALORISATION:
   ✓ Capitalisation boursière
   ✓ P/E Ratio (Price/Earnings)
   ✓ P/B Ratio (Price/Book)
   ✓ Prix moyen 90 jours
   ✓ Maximum 90 jours
   ✓ Minimum 90 jours
   ✓ Volume moyen 90 jours

3. FONDAMENTAUX:
   ✓ ROE (Return on Equity) %
   ✓ Beta (volatilité vs marché)
   ✓ Dette/Capitaux propres
   ✓ Dividende %

================================================================================
📖 PROCÉDURE DE COLLECTE
================================================================================

ÉTAPE 1: Aller sur BRVM.org
   URL: https://www.brvm.org/fr/investir/cours-et-cotations

ÉTAPE 2: Pour CHAQUE action (commencez par TOP 10):
   1. Cliquer sur le nom de l'action (ex: SNTS)
   2. Vous verrez une page avec TOUTES les données (comme votre screenshot)
   3. Noter:
      - CAPITALISATION: _____ FCFA
      - P/E RATIO: _____
      - P/B RATIO: _____
      - ROE: _____ %
      - BETA: _____
      - DETTE/CAPITAUX: _____
      - VOLUME: _____
      - VOLUME MOY: _____
      - MAX 90J: _____ FCFA
      - MIN 90J: _____ FCFA
      - PRIX MOYEN: _____ FCFA
      - VARIATION 90J: _____ %
      - DIVIDENDE: _____ %

ÉTAPE 3: Remplir le fichier
   Fichier: collecter_donnees_completes_8dec.py
   
   Exemple pour SNTS:
   
   'SNTS': {
       'close': 15500,              # Prix de clôture
       'open': 15400,               # Ouverture
       'high': 15600,               # Plus haut
       'low': 15300,                # Plus bas
       'volume': 8500,              # Volume
       'variation_jour': 2.3,       # Variation jour (%)
       'variation_90j': -36.79,     # Variation 90j (%)
       'capitalisation': 1500000000,# Capitalisation (FCFA)
       'pe_ratio': 12.5,            # P/E Ratio
       'pb_ratio': 2.3,             # P/B Ratio
       'prix_moyen_90j': 9135,      # Prix moyen 90j
       'max_90j': 19938,            # Maximum 90j
       'min_90j': 1737,             # Minimum 90j
       'volume_moyen_90j': 5798,    # Volume moyen 90j
       'roe': 15.2,                 # ROE (%)
       'beta': 1.05,                # Beta
       'dette_capitaux': 0.45,      # Dette/Capitaux
       'dividende': 5.5,            # Dividende (%)
   },

ÉTAPE 4: Tester
   python collecter_donnees_completes_8dec.py

ÉTAPE 5: Insérer en base
   python collecter_donnees_completes_8dec.py --apply

================================================================================
⚡ COLLECTE RAPIDE (Option recommandée)
================================================================================

Si collecter les 47 actions prend trop de temps, commencez par TOP 10:

1. SNTS (Sonatel)
2. UNLC (Unilever)
3. SGBC (SGBCI)
4. SIVC (SIVOA)
5. ONTBF (ONATEL)
6. SICG (SIC Groupe)
7. NTLC (Nestlé CI)
8. ETIT (Ecobank TI)
9. BICC (BICICI)
10. SLBC (Solibra)

Collectez TOUTES les données pour ces 10 actions d'abord, puis les autres plus tard.

================================================================================
💡 ASTUCES
================================================================================

• Si une donnée n'est pas disponible: mettre 0
  Exemple: 'pe_ratio': 0 si P/E non affiché

• Si volume/variation non disponibles: mettre 0
  Exemple: 'volume': 0, 'variation_jour': 0

• Gardez le format exact (virgules, accolades, guillemets)
  Python est sensible à la syntaxe!

• Vérifiez après chaque 5 actions:
  python collecter_donnees_completes_8dec.py
  
================================================================================
📊 STRUCTURE DES DONNÉES
================================================================================

Chaque action aura dans MongoDB:

{
  "source": "BRVM",
  "dataset": "STOCK_COMPLETE",
  "key": "SNTS",
  "ts": "2025-12-08",
  "value": 15500,
  "attrs": {
    "close": 15500,
    "open": 15400,
    "high": 15600,
    "low": 15300,
    "volume": 8500,
    "day_change_pct": 2.3,
    "change_90d_pct": -36.79,
    "market_cap": 1500000000,
    "pe_ratio": 12.5,
    "pb_ratio": 2.3,
    "avg_price_90d": 9135,
    "high_90d": 19938,
    "low_90d": 1737,
    "avg_volume_90d": 5798,
    "roe": 15.2,
    "beta": 1.05,
    "debt_to_equity": 0.45,
    "dividend_yield": 5.5,
    "data_quality": "REAL_MANUAL",
    "data_completeness": "FULL"
  }
}

================================================================================
✅ CHECKLIST
================================================================================

[ ] Fichier collecter_donnees_completes_8dec.py ouvert
[ ] BRVM.org ouvert sur page cotations
[ ] Commencé par SNTS (première action)
[ ] Copié TOUTES les 18 données pour SNTS
[ ] Testé: python collecter_donnees_completes_8dec.py
[ ] Aucune erreur Python
[ ] Continué avec les 9 autres actions TOP 10
[ ] Appliqué: python collecter_donnees_completes_8dec.py --apply
[ ] Vérifié insertion: python verifier_prix_aujourdhui.py

================================================================================

Bon courage! Cette collecte va créer la base de données la plus complète
pour votre système de recommandations IA! 🚀

================================================================================

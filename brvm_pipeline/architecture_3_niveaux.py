#!/usr/bin/env python3
"""
🏗️ ARCHITECTURE 3 NIVEAUX - BRVM STOCK PICKING HEBDOMADAIRE

PRINCIPE FONDAMENTAL :
- Niveau 1 (RAW) : Collectes intraday NON MODIFIABLES
- Niveau 2 (DAILY) : Source de vérité quotidienne  
- Niveau 3 (WEEKLY) : Base de décision unique

OBJECTIF : Être dans le TOP 5 des plus fortes hausses hebdomadaires BRVM
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# COLLECTIONS MONGODB (3 NIVEAUX)
# ============================================================================

COLLECTIONS = {
    'RAW': 'prices_intraday_raw',      # Niveau 1 - INTANGIBLE
    'DAILY': 'prices_daily',            # Niveau 2 - SOURCE DE VÉRITÉ
    'WEEKLY': 'prices_weekly',          # Niveau 3 - DÉCISIONNEL
    'TOP5': 'top5_weekly_brvm',         # Résultats finaux
    'LEARNING': 'autolearning_results'  # Feedback RichBourse
}

# ============================================================================
# CALIBRATION BRVM (INDICATEURS TECHNIQUES)
# ============================================================================

BRVM_CALIBRATION = {
    # RSI calibré BRVM (pas US/EU)
    'RSI': {
        'period': 14,
        'oversold': 40,      # Pas 30 !
        'overbought': 65,    # Pas 70 !
        'neutral_low': 45,
        'neutral_high': 55
    },
    
    # ATR% normalisé
    'ATR': {
        'period': 8,
        'low': 8,           # < 8% = range mort
        'normal_low': 8,
        'normal_high': 25,
        'high': 25          # > 25% = bruit
    },
    
    # SMA hebdomadaire
    'SMA': {
        'fast': 5,          # 5 semaines
        'slow': 10          # 10 semaines
    },
    
    # Volume
    'VOLUME': {
        'period': 8,        # Moyenne sur 8 semaines
        'threshold': 1.5    # Accélération si > 1.5x moyenne
    },
    
    # Volatilité
    'VOLATILITY': {
        'period': 12,       # Normalisé sur 12 semaines
        'threshold': 0.15   # 15% volatilité hebdo
    }
}

# ============================================================================
# FORMULE TOP5 SCORE (OBJECTIF FINAL)
# ============================================================================

TOP5_WEIGHTS = {
    'expected_return': 0.30,      # Gain potentiel (le plus important)
    'volume_acceleration': 0.25,  # Liquidité soudaine
    'semantic_score': 0.20,       # Annonces/publications
    'wos_setup': 0.15,            # Setup technique (WOS)
    'risk_reward': 0.10           # Ratio risque/rendement
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_current_week():
    """Retourne semaine ISO actuelle (format YYYY-Www)"""
    return datetime.now().strftime("%Y-W%V")

def get_week_boundaries(week_str):
    """
    Retourne les dates de début et fin de semaine
    Input: "2026-W06"
    Output: (datetime lundi, datetime dimanche)
    """
    year, week = week_str.split('-W')
    year = int(year)
    week = int(week)
    
    # Premier jour de l'année
    jan1 = datetime(year, 1, 1)
    # Premier lundi de l'année
    days_to_monday = (7 - jan1.weekday()) % 7
    if days_to_monday == 0 and jan1.weekday() != 0:
        days_to_monday = 7
    first_monday = jan1 + timedelta(days=days_to_monday)
    
    # Lundi de la semaine demandée
    week_start = first_monday + timedelta(weeks=week-1)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end

def create_indexes():
    """Créer les indexes MongoDB pour performance"""
    print("\n🔧 Création des indexes MongoDB...")
    
    # RAW - index sur datetime (jamais modifié)
    db[COLLECTIONS['RAW']].create_index([("symbol", 1), ("datetime", -1)])
    db[COLLECTIONS['RAW']].create_index([("date", 1)])
    
    # DAILY - index sur date (source de vérité)
    db[COLLECTIONS['DAILY']].create_index([("symbol", 1), ("date", -1)], unique=True)
    
    # WEEKLY - index sur week (base décision)
    db[COLLECTIONS['WEEKLY']].create_index([("symbol", 1), ("week", -1)], unique=True)
    
    # TOP5 - index sur week
    db[COLLECTIONS['TOP5']].create_index([("week", -1)])
    
    # LEARNING - index sur week + symbol
    db[COLLECTIONS['LEARNING']].create_index([("week", -1), ("symbol", 1)])
    
    print("✅ Indexes créés")

def verify_architecture():
    """Vérifier que l'architecture 3 niveaux fonctionne"""
    print("\n" + "="*80)
    print("🏗️  VÉRIFICATION ARCHITECTURE 3 NIVEAUX")
    print("="*80 + "\n")
    
    for name, collection in COLLECTIONS.items():
        count = db[collection].count_documents({})
        print(f"{'📦 ' + name:<20} ({collection:<30}) : {count:>6,} documents")
    
    print("\n" + "-"*80)
    print("CALIBRATION BRVM :")
    print("-"*80)
    print(f"  RSI        : {BRVM_CALIBRATION['RSI']['oversold']}-{BRVM_CALIBRATION['RSI']['overbought']} (pas 30-70)")
    print(f"  ATR%       : {BRVM_CALIBRATION['ATR']['normal_low']}-{BRVM_CALIBRATION['ATR']['normal_high']}% (pas 5-15%)")
    print(f"  SMA        : {BRVM_CALIBRATION['SMA']['fast']}/{BRVM_CALIBRATION['SMA']['slow']} semaines")
    print(f"  Volume     : moyenne {BRVM_CALIBRATION['VOLUME']['period']} semaines")
    
    print("\n" + "-"*80)
    print("FORMULE TOP5 SCORE :")
    print("-"*80)
    print(f"  Expected Return      : {TOP5_WEIGHTS['expected_return']:.0%}")
    print(f"  Volume Acceleration  : {TOP5_WEIGHTS['volume_acceleration']:.0%}")
    print(f"  Semantic Score       : {TOP5_WEIGHTS['semantic_score']:.0%}")
    print(f"  WOS Setup            : {TOP5_WEIGHTS['wos_setup']:.0%}")
    print(f"  Risk/Reward          : {TOP5_WEIGHTS['risk_reward']:.0%}")
    
    print("\n" + "="*80 + "\n")

def show_data_flow():
    """Afficher le flux de données"""
    print("\n📊 FLUX DE DONNÉES (ARCHITECTURE):\n")
    print("┌─────────────────────────────────────────────────┐")
    print("│  NIVEAU 1 - RAW (prices_intraday_raw)         │")
    print("│  ➜ Collecte toutes les 30-60 min              │")
    print("│  ➜ JAMAIS modifié, JAMAIS supprimé            │")
    print("│  ➜ Utilisé pour : volume relatif, breakouts   │")
    print("└─────────────────────────────────────────────────┘")
    print("                    ⬇")
    print("┌─────────────────────────────────────────────────┐")
    print("│  NIVEAU 2 - DAILY (prices_daily)              │")
    print("│  ➜ 1 ligne par action/jour (clôture)          │")
    print("│  ➜ SOURCE DE VÉRITÉ                            │")
    print("│  ➜ Alimente RSI, ATR, SMA, volatilité         │")
    print("└─────────────────────────────────────────────────┘")
    print("                    ⬇")
    print("┌─────────────────────────────────────────────────┐")
    print("│  NIVEAU 3 - WEEKLY (prices_weekly)            │")
    print("│  ➜ Agrégation mathématique pure               │")
    print("│  ➜ Open lundi / Close vendredi                │")
    print("│  ➜ SEULE BASE DE DÉCISION                     │")
    print("└─────────────────────────────────────────────────┘")
    print("                    ⬇")
    print("┌─────────────────────────────────────────────────┐")
    print("│  TOP5 ENGINE                                   │")
    print("│  ➜ Score = 0.30×Return + 0.25×Volume +        │")
    print("│            0.20×Semantic + 0.15×WOS +          │")
    print("│            0.10×RR                             │")
    print("└─────────────────────────────────────────────────┘")
    print()

if __name__ == "__main__":
    print("\n🚀 Initialisation Architecture 3 Niveaux BRVM\n")
    
    # Créer indexes
    create_indexes()
    
    # Vérifier état
    verify_architecture()
    
    # Afficher flux
    show_data_flow()
    
    print("✅ Architecture prête\n")

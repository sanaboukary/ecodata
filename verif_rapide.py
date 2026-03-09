#!/usr/bin/env python3
"""Vérification rapide des attributs"""
import os, sys, django
from pathlib import Path

BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Récupérer une observation récente
obs = db.curated_observations.find_one({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
}, sort=[('ts', -1)])

if obs:
    attrs = obs.get('attrs', {})
    print(f"Action: {obs['key']}")
    print(f"\nAttributs dashboard:")
    print(f"  market_cap: {attrs.get('market_cap', 'MANQUANT')}")
    print(f"  pe_ratio: {attrs.get('pe_ratio', 'MANQUANT')}")
    print(f"  sector: {attrs.get('sector', 'MANQUANT')}")
    print(f"  day_change_pct: {attrs.get('day_change_pct', 'MANQUANT')}")
    print(f"  consensus_score: {attrs.get('consensus_score', 'MANQUANT')}")
    print(f"  recommendation: {attrs.get('recommendation', 'MANQUANT')}")
    print(f"  target_price: {attrs.get('target_price', 'MANQUANT')}")
    print(f"  dividend_yield: {attrs.get('dividend_yield', 'MANQUANT')}")
    print(f"  shares_outstanding: {attrs.get('shares_outstanding', 'MANQUANT')}")

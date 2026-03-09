#!/usr/bin/env python3
"""Test direct TOP5"""
import os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

print("1. Imports...")
import django
django.setup()

print("2. Django setup OK")
from brvm_pipeline.top5_engine import generate_top5

print("3. Appel generate_top5...")
generate_top5('2026-W02')

print("4. Terminé")

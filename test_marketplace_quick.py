"""
Test rapide du marketplace
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, r'E:\DISQUE C\Desktop\Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

print("✅ Django configuré")

try:
    from dashboard.data_marketplace import get_data_stats
    print("✅ Import data_marketplace OK")
    
    stats = get_data_stats()
    print(f"✅ Stats récupérées : {stats['total']} observations totales")
    print(f"   - BRVM: {stats['brvm']['total_obs']}")
    print(f"   - Publications: {stats['publications']['total_obs']}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

try:
    from dashboard.data_marketplace import data_marketplace_page
    print("✅ Import data_marketplace_page OK")
except Exception as e:
    print(f"❌ Erreur import page: {e}")
    import traceback
    traceback.print_exc()

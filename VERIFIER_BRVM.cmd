@echo off
chcp 65001 >nul
title Verification BRVM
color 0A

echo ================================================================================
echo                     VERIFICATION DONNEES BRVM
echo ================================================================================
echo.

python -c "import os, sys; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings'); import django; django.setup(); from plateforme_centralisation.mongo import get_mongo_db; _, db = get_mongo_db(); total = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}); print(f'Total cours BRVM: {total}'); latest = db.curated_observations.find_one({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}, sort=[('ts', -1)]) if total > 0 else None; print(f'Derniere date: {latest.get(\"ts\", \"N/A\")[:10]}' if latest else 'Aucune donnee'); print(f'Qualite: {latest.get(\"attrs\", {}).get(\"data_quality\", \"N/A\")}' if latest else '')"

echo.
echo ================================================================================
echo   Dashboard: http://127.0.0.1:8000/brvm/
echo ================================================================================
echo.
pause

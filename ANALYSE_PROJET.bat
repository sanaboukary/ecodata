@echo off
echo ================================================================================
echo ANALYSE COMPLETE DU PROJET - RAPPORT POST-COLLECTE
echo ================================================================================
echo.

cd "E:\DISQUE C\Desktop\Implementation plateforme"
call .venv\Scripts\activate.bat

echo == VERIFICATION CONNEXION MONGODB ==
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print('✓ MongoDB connecte'); db = client.centralisation_db; print(f'✓ Base: {db.name}'); print(f'✓ Collections: {db.list_collection_names()}')"
echo.

echo == STATISTIQUES BRVM ==
python -c "from pymongo import MongoClient; from datetime import datetime; client = MongoClient('mongodb://localhost:27017'); db = client.centralisation_db; today = datetime.now().strftime('%%Y-%%m-%%d'); obs_today = db.curated_observations.count_documents({'source': 'BRVM', 'ts': today}); obs_total = db.curated_observations.count_documents({'source': 'BRVM'}); obs_real = db.curated_observations.count_documents({'source': 'BRVM', 'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}}); actions = len(db.curated_observations.distinct('key', {'source': 'BRVM'})); print(f'Observations aujourdhui ({today}): {obs_today}'); print(f'Observations BRVM totales: {obs_total:,}'); print(f'Observations reelles: {obs_real:,} ({obs_real/max(obs_total,1)*100:.1f}%%)'); print(f'Actions distinctes: {actions}')"
echo.

echo == ECHANTILLON DONNEES DU JOUR ==
python -c "from pymongo import MongoClient; from datetime import datetime; client = MongoClient('mongodb://localhost:27017'); db = client.centralisation_db; today = datetime.now().strftime('%%Y-%%m-%%d'); docs = list(db.curated_observations.find({'source': 'BRVM', 'ts': today}).limit(10)); print(f'Nombre dobservations aujourdhui: {len(docs)}'); [print(f'{d.get(\"key\", \"N/A\"):12} : {d.get(\"value\", 0):>10.2f} FCFA  [{d.get(\"attrs\", {}).get(\"data_quality\", \"UNKNOWN\")}]') for d in docs]"
echo.

echo ================================================================================
echo ANALYSE TERMINEE
echo ================================================================================
pause

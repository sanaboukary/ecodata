@echo off
color 0A
cls
echo.
echo ================================================================================
echo               COLLECTE PUBLICATIONS BRVM - RESULTAT
echo ================================================================================
echo.
python -c "import sys, os; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings'); import django; django.setup(); from plateforme_centralisation.mongo import get_mongo_db; _, db = get_mongo_db(); total = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'}); print(f'\n Total publications: {total}\n'); pipeline = [{'$match': {'source': 'BRVM_PUBLICATION'}}, {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}}, {'$sort': {'count': -1}}]; print(' Par categorie:'); [print(f'   {item[chr(95)+chr(105)+chr(100)]:25s} : {item[chr(99)+chr(111)+chr(117)+chr(110)+chr(116)]:3d}') for item in db.curated_observations.aggregate(pipeline)]"
echo.
echo ================================================================================
echo.
echo  Prochaine etape : Analyser le sentiment
echo  Commande : ANALYSER_SENTIMENT.cmd
echo.
echo  Ou voir dashboard : http://127.0.0.1:8000/brvm/publications/
echo.
echo ================================================================================
pause

@echo off
echo ================================================================================
echo                            DONNEES BRVM
echo ================================================================================
echo.

.venv\Scripts\python.exe -c "from pymongo import MongoClient; db = MongoClient('mongodb://localhost:27017').centralisation_db; total = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}); print(f'Total observations BRVM: {total}'); print(); actions = []; for obs in db.curated_observations.find({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}).sort('timestamp', -1).limit(50): k = obs.get('key', ''); a = obs.get('attrs', {}); if k and '_' not in k and len(k) <= 10 and k not in [x[0] for x in actions]: actions.append((k, a.get('nom', 'N/A')[:20], a.get('cours', 0), a.get('variation_pct', 0), a.get('volume', 0), a.get('ouverture', 0), a.get('haut', 0), a.get('bas', 0))); print(f\"{'SYM':<8} {'NOM':<22} {'COURS':>10} {'VAR%%':>8} {'VOLUME':>10} {'OUV':>10} {'HAUT':>10} {'BAS':>10}\"); print('-'*95); [print(f'{x[0]:<8} {x[1]:<22} {x[2]:>10,.2f} {x[3]:>7.2f}%% {x[4]:>10,} {x[5]:>10,.2f} {x[6]:>10,.2f} {x[7]:>10,.2f}') for x in sorted(actions)]; print(); print('================================================================================')"

pause

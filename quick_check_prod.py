#!/usr/bin/env python3
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

decisions = list(db.decisions_finales_brvm.find({'horizon': 'SEMAINE'}))

print(f'\n{len(decisions)} recommandations\n')

if decisions:
    for dec in decisions:
        symbol = dec.get('symbol')
        alpha = dec.get('alpha_score')
        signal = dec.get('signal')
        stop = dec.get('stop_loss')
        target = dec.get('take_profit')
        
        bugs = []
        if alpha is None or alpha == 0:
            bugs.append('ALPHA=None')
        if not signal or signal == 'N/A':
            bugs.append('Signal=None')
        if not stop:
            bugs.append('Stop=None')
        if not target:
            bugs.append('Target=None')
        
        status = '❌' if bugs else '✅'
        bug_str = ', '.join(bugs) if bugs else 'OK'
        
        print(f'{status} {symbol}: ALPHA={alpha}, Signal={signal}, Stop={stop}, Target={target} | {bug_str}')
else:
    print('Aucune recommandation trouvée')

#!/usr/bin/env python3
from plateforme_centralisation.mongo import get_mongo_db
_, db = get_mongo_db()

print('=' * 80)
print('DIAGNOSTIC PRODUCTION - READY FOR 10,000 CLIENTS?')
print('=' * 80)

decisions = list(db.decisions_finales_brvm.find({'horizon': 'SEMAINE'}))

print(f'\n[RECOMMANDATIONS] {len(decisions)} générées\n')

bugs_critiques = []

for dec in decisions:
    symbol = dec.get('symbol')
    alpha = dec.get('alpha_score')
    signal = dec.get('signal')
    stop = dec.get('stop_loss')
    target = dec.get('take_profit')
    
    print(f'[{symbol}]')
    
    # BUG 1: ALPHA = 0 ou None
    if alpha is None or alpha == 0:
        print(f'  ❌ BUG CRITIQUE: ALPHA_SCORE = {alpha} (devrait être 54-74)')
        bugs_critiques.append(f'{symbol}: ALPHA manquant')
    else:
        print(f'  ✓ ALPHA: {alpha:.1f}/100')
    
    # BUG 2: Signal manquant
    if not signal or signal == 'N/A':
        print(f'  ❌ BUG CRITIQUE: SIGNAL = {signal} (devrait être SELL/HOLD)')
        bugs_critiques.append(f'{symbol}: Signal manquant')
    else:
        print(f'  ✓ Signal: {signal}')
    
    # MANQUE: Stop loss / Take profit
    if not stop:
        print(f'  ⚠️ ATTENTION: Pas de stop_loss défini')
    if not target:
        print(f'  ⚠️ ATTENTION: Pas de take_profit défini')
    
    print()

print('=' * 80)
print('VERDICT PRODUCTION:')
print('=' * 80)

if bugs_critiques:
    print(f'\n❌ PAS PRÊT - {len(bugs_critiques)} bugs critiques:')
    for bug in bugs_critiques:
        print(f'   - {bug}')
    print('\n[ACTION REQUISE]')
    print('  1. Corriger sauvegarde alpha_score dans MongoDB')
    print('  2. Corriger sauvegarde signal (SELL/HOLD)')
    print('  3. Ajouter stop_loss et take_profit')
    print('  4. Tester 1-2 semaines AVANT 10,000 clients')
else:
    print('✅ PRÊT pour production (après validation 8 semaines Option A)')

print('=' * 80)

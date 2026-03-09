from pymongo import MongoClient

db = MongoClient()['centralisation_db']
weeks = sorted(db.prices_weekly.distinct('week'))
last = weeks[-1]

print(f"\n=== RECOMMANDATIONS BRVM - {last} ===\n")

obs = list(db.prices_weekly.find({'week': last}))
tradable = [o for o in obs if (o.get('atr_pct') or 0) >= 6 and (o.get('atr_pct') or 0) <= 25 and o.get('rsi')]

print(f"Actions tradables: {len(tradable)}\n")

recos = []
for t in tradable:
    atr, rsi = t.get('atr_pct', 10), t.get('rsi', 50)
    if not (25 <= rsi <= 55): continue
    
    stop, target = max(atr, 4.), 2.6 * atr
    rr = round(target / stop, 2)
    
    if rr < 2.3: continue
    
    wos = 70 if (40 <= rsi <= 50 and 8 <= atr <= 18) else 65
    er = round((target * 0.65) - (stop * 0.35), 2)
    
    if er < 5:continue
    
    recos.append({'s': t['symbol'], 'rr': rr, 'er': er, 'stop': round(stop, 1), 'target': round(target, 1), 'wos': wos, 'atr': atr, 'rsi': rsi, 'prix': t.get('close', 0)})

recos.sort(key=lambda x: x['er'], reverse=True)

if not recos:
    print("⚠️  TOL ZÉRO: Aucune reco cette semaine\n")
else:
    print(f"✅ {len(recos)} RECOMMANDATIONS:\n")
    print(f"{'#':<3} {'SYM':<6} {'RR':<6} {'ER%':<6} {'STOP%':<7} {'TARGET%':<8} {'WOS':<5}")
    print("-"*50)
    for i, r in enumerate(recos, 1):
        print(f"{i:<3} {r['s']:<6} {r['rr']:<6.2f} {r['er']:<6.1f} {r['stop']:<7.1f} {r['target']:<8.1f} {r['wos']:<5}")
    
    print(f"\n🎯 TOP 1: {recos[0]['s']} | RR={recos[0]['rr']} | ER={recos[0]['er']}% | Prix={recos[0]['prix']:.0f}")
    print(f"   Stop:{recos[0]['stop']}% | Target:{recos[0]['target']}%")
    print(f"\n📜 RÈGLE: MAX 1-2 positions, STOP OBLIGATOIRE\n")

#!/usr/bin/env python3
"""Dashboard recommandations - Output vers fichier"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["centralisation_db"]

output = []

output.append("\n" + "="*90)
output.append(f"RECOMMANDATIONS HEBDOMADAIRES BRVM - SEMAINE {datetime.now().strftime('%Y-W%U')}")
output.append("="*90 + "\n")

top5 = list(db.top5_weekly_brvm.find().sort([("rank", 1)]).limit(5))

if not top5:
    output.append("Aucune recommandation TOP5 disponible\n")
else:
    for t in top5:
        rank = t.get('rank', 0)
        symbol = t.get('symbol', 'N/A')
        classe = t.get('classe', 'N/A')
        conf = t.get('confidence', 0)
        gain = t.get('gain_attendu') or t.get('expected_return') or 0
        rr = t.get('rr', 0)
        wos = t.get('wos', 0)
        
        prix_entree = t.get('prix_entree', 0)
        prix_cible = t.get('prix_cible', 0)
        stop = t.get('stop', 0)
        atr = t.get('atr_pct', 0)
        score_top5 = t.get('top5_score', 0)
        
        output.append(f"\n[#{rank}] {symbol} - Classe {classe} (Score TOP5: {score_top5:.1f})")
        output.append("="*88)
        output.append(f"")
        output.append(f"  [METRIQUES CLES]")
        output.append(f"     Confiance      : {conf:.0f}%")
        output.append(f"     Gain attendu   : +{gain:.1f}%")
        output.append(f"     Risk/Reward    : {rr:.2f}")
        output.append(f"     WOS (Setup)    : {wos:.1f}/100")
        output.append(f"")
        output.append(f"  [PRIX]")
        output.append(f"     Entree         : {prix_entree:.0f} FCFA")
        output.append(f"     Cible          : {prix_cible:.0f} FCFA  (+{gain:.1f}%)")
        output.append(f"     Stop Loss      : {stop:.0f} FCFA  (-{((prix_entree-stop)/prix_entree*100) if prix_entree else 0:.1f}%)")
        output.append(f"")
        output.append(f"  [TECHNIQUES]")
        output.append(f"     ATR% (volatil) : {atr:.1f}%")
        output.append("")

output.append("="*90)
output.append(f"  {len(top5)} opportunites hebdomadaires identifiees")
output.append(f"  Mise a jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
output.append("="*90 + "\n")

# Print to console
for line in output:
    print(line)

# Save to file
with open("dashboard_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("\n[INFO] Dashboard sauvegarde dans: dashboard_output.txt\n")

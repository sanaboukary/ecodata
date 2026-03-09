"""Test rapide: comparer prix collectés vs TOP5 dashboard"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*70)
print("COMPARAISON PRIX FRAIS (collecte horaire) VS TOP5 (dashboard)")
print("="*70 + "\n")

# Lire TOP5
top5 = list(db.top5_weekly_brvm.find().sort("rank", 1).limit(5))

if not top5:
    print("❌ Aucun TOP5 trouvé. Lancez: python pipeline_brvm.py\n")
else:
    print(f"{'Rang':<6}{'Symbol':<8}{'Prix TOP5':<15}{'Prix FRAIS':<15}{'Écart':<12}{'Status'}")
    print("-" * 70)
    
    for doc in top5:
        symbol = doc.get("symbol", "")
        prix_top5 = doc.get("prix_entree", 0)
        
        # Prix frais de la dernière collecte
        frais = db.prices_daily.find_one(
            {"symbol": symbol},
            sort=[("date", -1)]
        )
        
        if frais:
            prix_frais = frais.get("close", 0)
            ecart = prix_frais - prix_top5
            ecart_pct = (ecart / prix_top5 * 100) if prix_top5 > 0 else 0
            
            if abs(ecart_pct) < 0.5:
                status = "✅ FRAIS"
            else:
                status = f"⚠️  STALE ({ecart_pct:+.1f}%)"
            
            print(
                f"{doc.get('rank', 0):<6}"
                f"{symbol:<8}"
                f"{prix_top5:>12,.0f} F  "
                f"{prix_frais:>12,.0f} F  "
                f"{ecart:>+10,.0f}  "
                f"{status}"
            )
        else:
            print(
                f"{doc.get('rank', 0):<6}"
                f"{symbol:<8}"
                f"{prix_top5:>12,.0f} F  "
                f"{'N/A':>12}  "
                f"{'N/A':>10}  "
                f"❌ Pas collecté"
            )
    
    print("\n" + "="*70)
    print("Si vous voyez ⚠️ STALE, relancez le pipeline pour actualiser:")
    print("  .venv\\Scripts\\python.exe pipeline_brvm.py")
    print("="*70 + "\n")

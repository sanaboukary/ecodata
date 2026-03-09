"""
Vérification des prix FRAIS vs STALE - Diagnostic dashboard BRVM
"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def verifier_prix_frais():
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print(" DIAGNOSTIQUE: PRIX FRAIS (prices_daily) VS PRIX AFFICHÉS (top5_weekly_brvm)")
    print("="*80 + "\n")
    
    # Lire TOP5 actuel du dashboard
    top5_docs = list(db.top5_weekly_brvm.find().sort("rank", 1))
    
    if not top5_docs:
        print("[ERREUR] Aucun TOP5 trouvé dans la base. Relancez le pipeline.")
        return
    
    print(f"{'Rang':<6} {'Symbol':<8} {'Prix TOP5':<12} {'Prix FRAIS':<12} {'Delta':<10} {'Date Collecte':<20}")
    print("-" * 80)
    
    for doc in top5_docs:
        symbol = doc.get("symbol", "")
        prix_top5 = doc.get("prix_entree", 0)
        
        # Récupérer le dernier prix collecté
        dernier_prix_doc = db.prices_daily.find_one(
            {"symbol": symbol},
            sort=[("date", -1)]
        )
        
        if dernier_prix_doc:
            prix_frais = dernier_prix_doc.get("close", 0)
            date_collecte = dernier_prix_doc.get("date", "N/A")
            delta = prix_frais - prix_top5
            delta_pct = (delta / prix_top5 * 100) if prix_top5 > 0 else 0
            
            status = "✓ FRAIS" if abs(delta_pct) < 0.1 else "✗ STALE"
            
            print(
                f"{doc.get('rank', 0):<6} "
                f"{symbol:<8} "
                f"{prix_top5:>10,.0f} F  "
                f"{prix_frais:>10,.0f} F  "
                f"{delta:>+8,.0f}  "
                f"{str(date_collecte)[:19]:<20} "
                f"{status}"
            )
        else:
            print(
                f"{doc.get('rank', 0):<6} "
                f"{symbol:<8} "
                f"{prix_top5:>10,.0f} F  "
                f"{'N/A':>12}  "
                f"{'N/A':>10}  "
                f"{'Pas de collecte':20} "
                f"✗ MANQUANT"
            )
    
    print("\n" + "="*80)
    print("LÉGENDE:")
    print("  ✓ FRAIS    : Le prix TOP5 correspond au dernier prix collecté (delta < 0.1%)")
    print("  ✗ STALE    : Le prix TOP5 est différent du dernier prix collecté (ancien)")
    print("  ✗ MANQUANT : Aucune donnée de prix trouvée dans prices_daily")
    print("="*80 + "\n")
    
    # Statistiques collecte horaire
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    collectes_aujourdhui = db.prices_daily.count_documents({
        "date": {"$regex": f"^{today_str}"}
    })
    
    print(f"Collectes aujourd'hui ({today_str}): {collectes_aujourdhui} documents")
    print(f"Vérification effectuée: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return top5_docs


if __name__ == "__main__":
    verifier_prix_frais()

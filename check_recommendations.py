"""
Vérification rapide des recommandations générées
"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Compter les recommandations
count = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE"})
print(f"\n📊 Recommandations hebdomadaires dans MongoDB: {count}\n")

if count > 0:
    decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}))
    
    # Statistiques
    total_confiance = sum(d.get("confiance", 0) for d in decisions)
    total_gain = sum(d.get("gain_attendu", 0) for d in decisions)
    
    print(f"Confiance moyenne: {total_confiance/count:.1f}%")
    print(f"Gain attendu moyen: {total_gain/count:.1f}%\n")
    
    print("Recommandations générées:")
    for d in decisions:
        symbol = d.get("symbol", "?")
        conf = d.get("confiance", 0)
        gain = d.get("gain_attendu", 0)
        prix = d.get("prix_actuel", 0)
        print(f"  ✅ {symbol}: {conf}% confiance, {gain}% gain attendu, prix {prix}")
else:
    print("❌ Aucune recommandation trouvée")

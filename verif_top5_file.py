"""Verifier TOP5 et ecrire dans fichier"""
from pymongo import MongoClient

db = MongoClient('mongodb://localhost:27017/')['centralisation_db']

# Compter
count = db.top5_weekly_brvm.count_documents({})

# Lire TOP5
top5 = list(db.top5_weekly_brvm.find({}, {'_id': 0}).sort([('rank', 1)]))

# Ecrire dans fichier
with open('verif_top5.txt', 'w', encoding='utf-8') as f:
    f.write(f"=== VERIFICATION TOP5 ===\n\n")
    f.write(f"Nombre total: {count}\n\n")
    
    if top5:
        for t in top5:
            f.write(f"#{t['rank']} {t['symbol']} - Classe {t['classe']}\n")
            f.write(f"  Prix entree: {t['prix_entree']:.0f} FCFA\n")
            f.write(f"  Prix cible: {t['prix_cible']:.0f} FCFA\n")
            f.write(f"  Gain: +{t['gain_attendu']:.1f}%\n")
            f.write(f"  Confiance: {t['confidence']}%\n")
            f.write(f"  WOS: {t['wos']:.1f}\n")
            f.write(f"  TOP5 Score: {t['top5_score']:.2f}\n")
            f.write(f"  Justification: {t['justification']}\n")
            f.write("\n")
    else:
        f.write("AUCUNE DONNEE TOP5!\n")

print("Fichier verif_top5.txt cree")

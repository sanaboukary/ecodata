# Script de diagnostic détaillé : Génère un rapport complet sur l'historique de prix weekly
from pymongo import MongoClient
import csv

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["centralisation_db"]

symbols = db.prices_weekly.distinct("symbol")

rapport = []
rapport.append(["Symbol", "Semaines_disponibles", "Closes_valides", "Semaines_manquantes", "Closes_nuls_ou_absents"])

for symbol in sorted(symbols):
    docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1))
    n = len(docs)
    n_valid = sum(1 for d in docs if d.get("close") not in (None, 0))
    semaines_manquantes = max(0, 9 - n)
    closes_nuls = n - n_valid
    rapport.append([symbol, n, n_valid, semaines_manquantes, closes_nuls])

# Écriture CSV
with open("rapport_prices_weekly.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rapport)

print("\nRapport détaillé généré : rapport_prices_weekly.csv\n")
print("Colonnes : Symbol, Semaines_disponibles, Closes_valides, Semaines_manquantes, Closes_nuls_ou_absents")
print("Ouvre le fichier CSV pour l'analyse complète.")

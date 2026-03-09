#!/usr/bin/env python3
"""Vérifier combien de semaines on peut générer depuis DAILY"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def get_week_number(date_str):
    """Convertir date YYYY-MM-DD en semaine ISO"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%Y-W%V")

def main():
    _, db = get_mongo_db()
    
    print("\n📅 ANALYSE DAILY → WEEKLY\n")
    
    # Dates uniques dans DAILY
    dates = db.prices_daily.distinct('date', {})
    dates.sort()
    
    print(f"Dates DAILY: {len(dates)}")
    print(f"Première: {dates[0]}")
    print(f"Dernière: {dates[-1]}")
    
    # Semaines théoriques
    weeks = set()
    for date_str in dates:
        week = get_week_number(date_str)
        weeks.add(week)
    
    weeks_sorted = sorted(weeks)
    print(f"\n📊 Semaines théoriques à créer: {len(weeks_sorted)}")
    print(f"De {weeks_sorted[0]} à {weeks_sorted[-1]}")
    print(f"\nToutes les semaines:")
    for w in weeks_sorted:
        count = sum(1 for d in dates if get_week_number(d) == w)
        print(f"  {w}: {count} jours")
    
    # Comparaison avec WEEKLY existant
    weekly_weeks = db.prices_weekly.distinct('week', {})
    print(f"\n✅ Semaines WEEKLY créées: {len(weekly_weeks)}")
    print(f"   {sorted(weekly_weeks)}")
    
    missing = set(weeks_sorted) - set(weekly_weeks)
    if missing:
        print(f"\n❌ Semaines manquantes: {len(missing)}")
        print(f"   {sorted(missing)}")

if __name__ == '__main__':
    main()

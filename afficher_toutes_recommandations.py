"""
Affichage complet des recommandations DUAL MOTOR
"""

from pymongo import MongoClient
from datetime import datetime

# MongoDB
client = MongoClient('localhost', 27017)
db = client['centralisation_db']

print("\n" + "="*80)
print("📊 RECOMMANDATIONS DUAL MOTOR - BRVM")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# ============================================================================
# DONNÉES DISPONIBLES
# ============================================================================

weeks = db.prices_weekly.distinct('week')
weeks.sort()
print(f"📅 Semaines disponibles: {len(weeks)}")
if weeks:
    print(f"   Première: {weeks[0]}")
    print(f"   Dernière: {weeks[-1]}")
    print(f"   5 dernières: {weeks[-5:]}")

print(f"\n📊 Observations BRVM total: {db.curated_observations.count_documents({})}")
print(f"📊 Données hebdomadaires: {db.prices_weekly.count_documents({})}")
print(f"📊 Données quotidiennes: {db.prices_daily.count_documents({})}")

print("\n" + "="*80)
print("MOTEUR 1: WOS STABLE (2-8 semaines)")
print("="*80 + "\n")

# Décisions WOS STABLE
wos_count = db.decisions_finales_brvm.count_documents({})
print(f"Total décisions WOS STABLE: {wos_count}")

if wos_count > 0:
    # Chercher les plus récentes
    wos_decisions = list(db.decisions_finales_brvm.find({}).sort([
        ('created_at', -1), ('_id', -1)
    ]).limit(10))
    
    # Grouper par semaine si disponible
    by_week = {}
    for dec in wos_decisions:
        week = dec.get('week', 'N/A')
        if week not in by_week:
            by_week[week] = []
        by_week[week].append(dec)
    
    print(f"\nSemaines avec décisions: {list(by_week.keys())}")
    
    # Afficher la semaine la plus récente
    for week in sorted(by_week.keys(), reverse=True)[:1]:
        decisions = by_week[week]
        print(f"\n📅 Semaine {week}:")
        print(f"   Positions: {len(decisions)}")
        
        for i, dec in enumerate(decisions, 1):
            symbol = dec.get('symbol', 'N/A')
            decision = dec.get('decision', 'N/A')
            wos = dec.get('wos_score', dec.get('score', 'N/A'))
            close = dec.get('close', 0)
            target = dec.get('target_price', 0)
            
            print(f"\n   {i}. {symbol} - {decision}")
            print(f"      Prix: {close:.0f} FCFA | Target: {target:.0f} FCFA")
            print(f"      WOS Score: {wos}")
            
            # Métriques experts si disponibles
            vol_z = dec.get('volume_zscore')
            accel = dec.get('acceleration')
            if vol_z is not None:
                print(f"      Volume Z-score: {vol_z:+.1f}")
            if accel is not None:
                print(f"      Accélération: {accel:+.1f}%")
else:
    print("⚠️  Aucune décision WOS STABLE trouvée")
    print("\n💡 Pour générer:")
    print("   python analyse_ia_simple.py")
    print("   python decision_finale_brvm.py")

print("\n" + "="*80)
print("MOTEUR 2: EXPLOSION 7-10 JOURS (Opportuniste)")
print("="*80 + "\n")

# Décisions EXPLOSION 7J
exp_count = db.decisions_explosion_7j.count_documents({})
print(f"Total décisions EXPLOSION 7J: {exp_count}")

if exp_count > 0:
    exp_decisions = list(db.decisions_explosion_7j.find({}).sort('generated_at', -1).limit(5))
    
    # Grouper par semaine
    by_week_exp = {}
    for dec in exp_decisions:
        week = dec.get('week', 'N/A')
        if week not in by_week_exp:
            by_week_exp[week] = []
        by_week_exp[week].append(dec)
    
    print(f"\nSemaines avec décisions: {list(by_week_exp.keys())}")
    
    # Afficher la semaine la plus récente
    for week in sorted(by_week_exp.keys(), reverse=True)[:1]:
        decisions = by_week_exp[week]
        print(f"\n📅 Semaine {week}:")
        print(f"   Positions: {len(decisions)}")
        
        for i, dec in enumerate(decisions, 1):
            symbol = dec.get('symbol', 'N/A')
            score = dec.get('explosion_score', 'N/A')
            close = dec.get('close', 0)
            target_pct = dec.get('target_pct', 0)
            stop_pct = dec.get('stop_pct', 0)
            
            print(f"\n   {i}. {symbol} - EXPLOSION SCORE: {score}")
            print(f"      Prix: {close:.0f} FCFA")
            print(f"      Stop: -{stop_pct:.1f}% | Target: +{target_pct:.1f}%")
            print(f"      Horizon: {dec.get('horizon', '7-10 jours')}")
            
            # Détails
            print(f"      Breakout: {dec.get('breakout_score', 0)}/100")
            print(f"      Volume Z: {dec.get('volume_zscore_score', 0)}/100")
            print(f"      Accélération: {dec.get('acceleration_score', 0)}/100")
            print(f"      Prob TOP5: {dec.get('prob_top5', 0):.1f}%")
else:
    print("⚠️  Aucune décision EXPLOSION 7J trouvée")
    print("\n💡 Pour générer:")
    print("   python explosion_7j_detector.py")
    print("   ou")
    print("   python explosion_7j_detector.py --week 2026-W06")

print("\n" + "="*80)
print("📊 RÉSUMÉ")
print("="*80)

print(f"\n✅ MOTEUR 1 (WOS STABLE): {wos_count} décisions")
print(f"✅ MOTEUR 2 (EXPLOSION 7J): {exp_count} décisions")
print(f"\n💡 Allocation suggérée:")
print(f"   60% capital → WOS STABLE (3-6 positions)")
print(f"   30% capital → EXPLOSION 7J (1-2 positions)")
print(f"   10% capital → Cash réserve")

print("\n" + "="*80)
print("🚀 COMMANDES UTILES")
print("="*80)

print("\nGénérer/actualiser recommandations:")
print("  python analyse_ia_simple.py")
print("  python decision_finale_brvm.py")
print("  python explosion_7j_detector.py")

print("\nComparer les deux moteurs:")
print("  python comparer_dual_motor.py")

print("\nAfficher track record EXPLOSION:")
print("  python explosion_7j_detector.py --track-record")

print("\n" + "="*80 + "\n")

#!/usr/bin/env python3
"""
SUIVI AUTOMATIQUE DES RECOMMANDATIONS
Vérifie la performance réelle des recommandations IA pour améliorer le système
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

print("=" * 80)
print("📈 SUIVI PERFORMANCE RECOMMANDATIONS - APPRENTISSAGE CONTINU")
print("=" * 80)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Collection pour historique recommandations (créer si n'existe pas)
collection_tracking = db['recommandations_tracking']

# Charger toutes les recommandations validées des 7 derniers jours
import glob
rapports_valides = glob.glob('recommandations_validees_*.json')
rapports_valides.sort(reverse=True)

print(f"\n📊 {len(rapports_valides)} rapports de recommandations trouvés")

performances = []

for rapport_file in rapports_valides[:7]:  # 7 derniers jours
    try:
        with open(rapport_file, 'r', encoding='utf-8') as f:
            rapport = json.load(f)
        
        date_reco = rapport.get('date_validation', '')[:10]
        if not date_reco:
            continue
        
        # Vérifier chaque recommandation validée
        for reco in rapport.get('top_validees', []):
            symbol = reco['symbol']
            prix_reco = reco['prix_actuel']
            score_ia = reco['score']
            score_confiance = reco['score_confiance']
            
            # Trouver prix 7 jours après
            date_7j_apres = (datetime.fromisoformat(date_reco) + timedelta(days=7)).strftime('%Y-%m-%d')
            
            obs_7j = db.curated_observations.find_one({
                'source': 'BRVM',
                'key': symbol,
                'ts': date_7j_apres
            })
            
            if obs_7j:
                prix_7j = obs_7j['value']
                performance_7j = ((prix_7j - prix_reco) / prix_reco) * 100
                
                # Déterminer si recommandation était bonne
                success = performance_7j >= 5  # Au moins +5% = succès
                
                performances.append({
                    'symbol': symbol,
                    'date_reco': date_reco,
                    'prix_reco': prix_reco,
                    'prix_7j': prix_7j,
                    'performance_7j': performance_7j,
                    'score_ia': score_ia,
                    'score_confiance': score_confiance,
                    'success': success
                })
                
                # Sauvegarder dans collection tracking
                collection_tracking.update_one(
                    {
                        'symbol': symbol,
                        'date_reco': date_reco
                    },
                    {
                        '$set': {
                            'symbol': symbol,
                            'date_reco': date_reco,
                            'prix_reco': prix_reco,
                            'prix_7j': prix_7j,
                            'performance_7j': performance_7j,
                            'score_ia': score_ia,
                            'score_confiance': score_confiance,
                            'success': success,
                            'last_updated': datetime.now().isoformat()
                        }
                    },
                    upsert=True
                )
    
    except Exception as e:
        print(f"⚠️  Erreur lecture {rapport_file}: {e}")
        continue

# Statistiques
if performances:
    print(f"\n📊 STATISTIQUES DE PERFORMANCE")
    print("=" * 80)
    
    total = len(performances)
    succes = sum(1 for p in performances if p['success'])
    win_rate = (succes / total * 100) if total > 0 else 0
    
    perfs_values = [p['performance_7j'] for p in performances]
    avg_return = sum(perfs_values) / len(perfs_values) if perfs_values else 0
    max_gain = max(perfs_values) if perfs_values else 0
    max_perte = min(perfs_values) if perfs_values else 0
    
    print(f"\n✅ WIN RATE: {win_rate:.1f}% ({succes}/{total} recommandations gagnantes)")
    print(f"📈 Rendement moyen: {avg_return:+.2f}%")
    print(f"🟢 Meilleur gain: {max_gain:+.2f}%")
    print(f"🔴 Pire perte: {max_perte:+.2f}%")
    
    # Analyse par score IA
    print(f"\n📊 PERFORMANCE PAR SCORE IA:")
    for seuil in [80, 75, 70, 60]:
        filtered = [p for p in performances if p['score_ia'] >= seuil]
        if filtered:
            success_rate = sum(1 for p in filtered if p['success']) / len(filtered) * 100
            avg_perf = sum(p['performance_7j'] for p in filtered) / len(filtered)
            print(f"   Score ≥{seuil}: {success_rate:.1f}% win rate, {avg_perf:+.2f}% avg return ({len(filtered)} recos)")
    
    # Analyse par confiance
    print(f"\n📊 PERFORMANCE PAR CONFIANCE:")
    for seuil in [90, 80, 70]:
        filtered = [p for p in performances if p['score_confiance'] >= seuil]
        if filtered:
            success_rate = sum(1 for p in filtered if p['success']) / len(filtered) * 100
            avg_perf = sum(p['performance_7j'] for p in filtered) / len(filtered)
            print(f"   Confiance ≥{seuil}%: {success_rate:.1f}% win rate, {avg_perf:+.2f}% avg return ({len(filtered)} recos)")
    
    # Meilleures et pires recommandations
    print(f"\n🏆 TOP 3 MEILLEURES RECOMMANDATIONS:")
    top3 = sorted(performances, key=lambda x: x['performance_7j'], reverse=True)[:3]
    for i, p in enumerate(top3, 1):
        print(f"   {i}. {p['symbol']:12} {p['date_reco']}  {p['performance_7j']:+6.2f}%  (Score IA: {p['score_ia']})")
    
    print(f"\n📉 TOP 3 PIRES RECOMMANDATIONS:")
    bottom3 = sorted(performances, key=lambda x: x['performance_7j'])[:3]
    for i, p in enumerate(bottom3, 1):
        print(f"   {i}. {p['symbol']:12} {p['date_reco']}  {p['performance_7j']:+6.2f}%  (Score IA: {p['score_ia']})")
    
    # Recommandations d'amélioration
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATIONS D'AMÉLIORATION")
    print("=" * 80)
    
    if win_rate < 60:
        print("\n❌ WIN RATE INSUFFISANT (<60%)")
        print("   Actions correctives:")
        print("   1. Augmenter seuil score IA minimum (actuellement ≥60, passer à ≥70)")
        print("   2. Augmenter seuil confiance minimum (actuellement ≥70%, passer à ≥80%)")
        print("   3. Réduire volatilité max acceptée (actuellement <30%, passer à <20%)")
        print("   4. Collecter plus de données (historique 60 jours minimum)")
    
    elif win_rate < 75:
        print("\n⚠️  WIN RATE MOYEN (60-75%)")
        print("   Actions correctives:")
        print("   1. Affiner critères de sélection (seuil confiance à ≥75%)")
        print("   2. Intégrer analyse fondamentale (P/E, ROE, dividendes)")
        print("   3. Ajouter filtres sectoriels (éviter secteurs en crise)")
    
    elif win_rate < 85:
        print("\n🟡 WIN RATE BON (75-85%)")
        print("   Actions d'optimisation:")
        print("   1. Fine-tuning des poids du scoring")
        print("   2. Analyse des recommandations perdantes pour pattern")
        print("   3. Ajuster take-profit/stop-loss dynamiquement")
    
    else:
        print("\n✅ WIN RATE EXCELLENT (≥85%)")
        print("   Système performant - Maintenir et monitorer")
    
    # Sauil recommandé
    # Trouver seuil optimal
    print("\n📊 SEUILS OPTIMAUX RECOMMANDÉS:")
    
    # Test différents seuils confiance
    best_seuil = 70
    best_win_rate = 0
    
    for seuil in range(70, 100, 5):
        filtered = [p for p in performances if p['score_confiance'] >= seuil]
        if len(filtered) >= 5:  # Au moins 5 recommandations
            wr = sum(1 for p in filtered if p['success']) / len(filtered) * 100
            if wr > best_win_rate:
                best_win_rate = wr
                best_seuil = seuil
    
    print(f"   🎯 Seuil confiance optimal: ≥{best_seuil}% (win rate: {best_win_rate:.1f}%)")
    
    # Sauvegarder statistiques
    stats = {
        'date_analyse': datetime.now().isoformat(),
        'periode': f"{performances[0]['date_reco']} à {performances[-1]['date_reco']}",
        'total_recommandations': total,
        'win_rate': win_rate,
        'rendement_moyen': avg_return,
        'max_gain': max_gain,
        'max_perte': max_perte,
        'seuil_confiance_optimal': best_seuil,
        'performances_detaillees': performances
    }
    
    filename = f"stats_performance_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Statistiques sauvegardées: {filename}")

else:
    print("\n⚠️  Pas assez de données pour statistiques")
    print("   Attendre au moins 7 jours après première recommandation")

print("\n" + "=" * 80)
print("✅ ANALYSE TERMINÉE")
print("=" * 80)

client.close()

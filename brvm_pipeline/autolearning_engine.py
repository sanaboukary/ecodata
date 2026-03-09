#!/usr/bin/env python3
"""
🧠 AUTO-LEARNING ENGINE - AJUSTEMENT AUTOMATIQUE DES POIDS

PRINCIPE :
- Chaque fin de semaine : récupérer TOP5 officiel RichBourse
- Comparer avec nos recommandations
- Marquer succès/échec
- Ajuster automatiquement les poids sur 3 mois glissants

OBJECTIF :
Maximiser le taux de présence dans le vrai TOP5 BRVM

MÉTHODE :
Gradient descent simple sur les poids (contrainte : somme = 1.0)
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION
# ============================================================================

COLLECTION_TOP5 = "top5_weekly_brvm"
COLLECTION_LEARNING = "autolearning_results"
COLLECTION_WEIGHTS = "autolearning_weights"

# Période d'analyse (3 mois glissants)
LEARNING_PERIOD_WEEKS = 12

# Learning rate
LEARNING_RATE = 0.05  # 5% ajustement par itération

# ============================================================================
# RÉCUPÉRATION TOP5 OFFICIEL RICHBOURSE
# ============================================================================

def fetch_official_top5(week_str):
    """
    Récupérer le TOP5 officiel de RichBourse pour une semaine
    
    👉 MANUEL pour le moment (à automatiser avec scraping RichBourse)
    
    Args:
        week_str: Semaine ISO (YYYY-Www)
    
    Returns:
        list of dict: [{'symbol': 'ABJC', 'gain_pct': 15.2}, ...]
    """
    # Vérifier si déjà enregistré
    existing = db[COLLECTION_LEARNING].find_one({
        'week': week_str,
        'type': 'OFFICIAL_TOP5'
    })
    
    if existing:
        return existing.get('top5', [])
    
    # Si pas encore enregistré, retourner vide
    # (l'utilisateur doit enregistrer manuellement)
    return []

def register_official_top5(week_str, top5_data):
    """
    Enregistrer le TOP5 officiel RichBourse
    
    Args:
        week_str: Semaine ISO
        top5_data: [
            {'symbol': 'ABJC', 'gain_pct': 15.2},
            {'symbol': 'BICC', 'gain_pct': 12.5},
            ...
        ]
    """
    doc = {
        'week': week_str,
        'type': 'OFFICIAL_TOP5',
        'source': 'RichBourse',
        'top5': top5_data,
        'registered_at': datetime.now()
    }
    
    db[COLLECTION_LEARNING].update_one(
        {'week': week_str, 'type': 'OFFICIAL_TOP5'},
        {'$set': doc},
        upsert=True
    )
    
    print(f"✅ TOP5 officiel enregistré : {week_str}")
    for i, item in enumerate(top5_data, 1):
        print(f"   {i}. {item['symbol']} : +{item['gain_pct']:.2f}%")

# ============================================================================
# COMPARAISON & SCORING
# ============================================================================

def compare_top5(week_str):
    """
    Comparer notre TOP5 avec le TOP5 officiel
    
    Returns:
        dict: {
            'week': str,
            'our_top5': list,
            'official_top5': list,
            'matches': int,
            'success_rate': float,
            'details': list
        }
    """
    # Notre TOP5
    our_top5 = list(db[COLLECTION_TOP5].find({'week': week_str}).sort('rank', 1))
    
    # TOP5 officiel
    official = fetch_official_top5(week_str)
    
    if not official:
        print(f"⚠️  Pas de TOP5 officiel pour {week_str}")
        return None
    
    our_symbols = [t['symbol'] for t in our_top5]
    official_symbols = [t['symbol'] for t in official]
    
    # Matches
    matches = set(our_symbols) & set(official_symbols)
    success_rate = len(matches) / 5 * 100  # Sur 5 possibles
    
    # Détails
    details = []
    for symbol in our_symbols:
        in_official = symbol in official_symbols
        official_rank = official_symbols.index(symbol) + 1 if in_official else None
        
        details.append({
            'symbol': symbol,
            'our_rank': our_symbols.index(symbol) + 1,
            'in_official': in_official,
            'official_rank': official_rank,
            'hit': in_official
        })
    
    result = {
        'week': week_str,
        'our_top5': our_symbols,
        'official_top5': official_symbols,
        'matches': len(matches),
        'matches_symbols': list(matches),
        'success_rate': success_rate,
        'details': details,
        'compared_at': datetime.now()
    }
    
    # Sauvegarder
    db[COLLECTION_LEARNING].update_one(
        {'week': week_str, 'type': 'COMPARISON'},
        {'$set': result},
        upsert=True
    )
    
    return result

# ============================================================================
# ANALYSE PERFORMANCE (3 MOIS GLISSANTS)
# ============================================================================

def analyze_performance():
    """
    Analyser les performances sur 3 mois glissants
    
    Returns:
        dict: Stats globales
    """
    # Dernières 12 semaines
    comparisons = list(db[COLLECTION_LEARNING].find({
        'type': 'COMPARISON'
    }).sort('week', -1).limit(LEARNING_PERIOD_WEEKS))
    
    if not comparisons:
        print("❌ Aucune comparaison disponible")
        return None
    
    total_weeks = len(comparisons)
    total_matches = sum(c['matches'] for c in comparisons)
    avg_success_rate = sum(c['success_rate'] for c in comparisons) / total_weeks
    
    # Par composante (analyse avancée)
    component_impact = {
        'expected_return': 0,
        'volume_acceleration': 0,
        'semantic_score': 0,
        'wos_setup': 0,
        'risk_reward': 0
    }
    
    # Pour chaque comparaison, identifier quelles composantes ont aidé
    for comp in comparisons:
        for detail in comp['details']:
            if detail['hit']:
                # Ce symbole était dans le TOP5 officiel
                # Récupérer ses scores de composantes
                our_top5_item = db[COLLECTION_TOP5].find_one({
                    'week': comp['week'],
                    'symbol': detail['symbol']
                })
                
                if our_top5_item and 'components' in our_top5_item:
                    components = our_top5_item['components']
                    # Les composantes fortes ont contribué au succès
                    for key, value in components.items():
                        component_impact[key] += value
    
    # Normaliser
    for key in component_impact:
        component_impact[key] /= total_matches if total_matches > 0 else 1
    
    stats = {
        'period_weeks': total_weeks,
        'total_possible': total_weeks * 5,
        'total_matches': total_matches,
        'avg_success_rate': round(avg_success_rate, 2),
        'component_impact': component_impact,
        'analyzed_at': datetime.now()
    }
    
    return stats

# ============================================================================
# AJUSTEMENT DES POIDS (GRADIENT DESCENT SIMPLE)
# ============================================================================

def adjust_weights():
    """
    Ajuster les poids automatiquement
    
    Méthode :
    - Identifier quelles composantes ont le plus contribué aux succès
    - Augmenter leur poids
    - Diminuer poids des composantes moins performantes
    - Contrainte : somme = 1.0
    """
    stats = analyze_performance()
    
    if not stats:
        print("❌ Pas assez de données pour ajuster les poids")
        return None
    
    print("\n" + "="*80)
    print("🧠 AJUSTEMENT AUTOMATIQUE DES POIDS")
    print("="*80 + "\n")
    
    print(f"📊 Performance sur {stats['period_weeks']} semaines :")
    print(f"   Matches : {stats['total_matches']}/{stats['total_possible']}")
    print(f"   Taux de réussite : {stats['avg_success_rate']:.1f}%\n")
    
    # Poids actuels
    current_weights_doc = db[COLLECTION_WEIGHTS].find_one({}, sort=[('version', -1)])
    
    if current_weights_doc:
        current_weights = current_weights_doc['weights']
        version = current_weights_doc['version'] + 1
    else:
        # Poids par défaut
        current_weights = {
            'expected_return': 0.30,
            'volume_acceleration': 0.25,
            'semantic_score': 0.20,
            'wos_setup': 0.15,
            'risk_reward': 0.10
        }
        version = 1
    
    print("Poids actuels :")
    for key, val in current_weights.items():
        print(f"   {key:<25} : {val:.2%}")
    
    # Impact des composantes (normalisé)
    component_impact = stats['component_impact']
    total_impact = sum(component_impact.values())
    
    if total_impact == 0:
        print("\n⚠️  Aucun impact détecté, pas d'ajustement")
        return current_weights
    
    # Normaliser impact sur 0-1
    normalized_impact = {k: v/total_impact for k, v in component_impact.items()}
    
    print("\n📈 Impact normalisé (succès) :")
    for key, val in sorted(normalized_impact.items(), key=lambda x: x[1], reverse=True):
        print(f"   {key:<25} : {val:.2%}")
    
    # Nouveau poids = poids actuel + learning_rate × (impact - poids_actuel)
    new_weights = {}
    for key in current_weights:
        target = normalized_impact.get(key, 0)
        adjustment = LEARNING_RATE * (target - current_weights[key])
        new_weights[key] = current_weights[key] + adjustment
    
    # Normaliser pour que somme = 1.0
    total = sum(new_weights.values())
    new_weights = {k: v/total for k, v in new_weights.items()}
    
    print("\n🔧 Nouveaux poids (après ajustement) :")
    for key, val in new_weights.items():
        delta = val - current_weights[key]
        sign = '+' if delta >= 0 else ''
        print(f"   {key:<25} : {val:.2%} ({sign}{delta:.2%})")
    
    # Sauvegarder
    new_weights_doc = {
        'version': version,
        'weights': new_weights,
        'previous_weights': current_weights,
        'stats': stats,
        'learning_rate': LEARNING_RATE,
        'created_at': datetime.now()
    }
    
    db[COLLECTION_WEIGHTS].insert_one(new_weights_doc)
    
    print(f"\n✅ Poids v{version} sauvegardés")
    print("="*80 + "\n")
    
    return new_weights

# ============================================================================
# AFFICHAGE HISTORIQUE
# ============================================================================

def show_learning_history():
    """Afficher l'historique des comparaisons"""
    comparisons = list(db[COLLECTION_LEARNING].find({
        'type': 'COMPARISON'
    }).sort('week', -1).limit(12))
    
    if not comparisons:
        print("❌ Aucun historique")
        return
    
    print("\n" + "="*80)
    print("📊 HISTORIQUE AUTO-LEARNING (12 dernières semaines)")
    print("="*80 + "\n")
    
    print(f"{'SEMAINE':<12} {'MATCHES':<10} {'TAUX':<10} {'NOS ACTIONS':<40}")
    print("-"*80)
    
    for comp in comparisons:
        our = ', '.join(comp['our_top5'][:3])
        matches = ', '.join(comp['matches_symbols']) if comp['matches_symbols'] else '-'
        
        print(
            f"{comp['week']:<12} "
            f"{comp['matches']}/5{'':<6} "
            f"{comp['success_rate']:>5.1f}%{'':<5} "
            f"{our}..."
        )
    
    print("\n" + "="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Interface principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Learning Engine')
    parser.add_argument('--register', help='Enregistrer TOP5 officiel (JSON file)')
    parser.add_argument('--week', help='Semaine (YYYY-Www)')
    parser.add_argument('--compare', action='store_true', help='Comparer avec officiel')
    parser.add_argument('--analyze', action='store_true', help='Analyser performance')
    parser.add_argument('--adjust', action='store_true', help='Ajuster poids')
    parser.add_argument('--history', action='store_true', help='Afficher historique')
    
    args = parser.parse_args()
    
    if args.register and args.week:
        # Charger JSON
        with open(args.register, 'r') as f:
            top5_data = json.load(f)
        register_official_top5(args.week, top5_data)
    
    elif args.compare and args.week:
        result = compare_top5(args.week)
        if result:
            print(f"\n✅ Semaine {args.week}")
            print(f"   Notre TOP5   : {', '.join(result['our_top5'])}")
            print(f"   TOP5 officiel: {', '.join(result['official_top5'])}")
            print(f"   Matches      : {result['matches']}/5 ({result['success_rate']:.1f}%)")
    
    elif args.analyze:
        stats = analyze_performance()
        if stats:
            print("\n📊 Performance 3 mois :")
            print(f"   Semaines     : {stats['period_weeks']}")
            print(f"   Matches      : {stats['total_matches']}/{stats['total_possible']}")
            print(f"   Taux moyen   : {stats['avg_success_rate']:.1f}%")
    
    elif args.adjust:
        adjust_weights()
    
    elif args.history:
        show_learning_history()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

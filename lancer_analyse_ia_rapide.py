"""
Script optimisé pour générer rapidement des recommandations BRVM
Version simplifiée sans requêtes MongoDB lourdes
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import timezone
import json

def calculate_technical_indicators(prices):
    """Calcul rapide des indicateurs techniques"""
    if len(prices) < 5:
        return None
    
    # Prix actuels
    current = prices[0]['value']
    prev = prices[1]['value'] if len(prices) > 1 else current
    
    # Variation
    variation = ((current - prev) / prev * 100) if prev > 0 else 0
    
    # Moyennes mobiles simples
    prices_values = [p['value'] for p in prices]
    sma5 = sum(prices_values[:5]) / 5 if len(prices) >= 5 else current
    sma10 = sum(prices_values[:10]) / 10 if len(prices) >= 10 else current
    sma20 = sum(prices_values[:20]) / 20 if len(prices) >= 20 else current
    
    # RSI simplifié
    gains = [prices_values[i-1] - prices_values[i] for i in range(1, min(14, len(prices_values))) if prices_values[i-1] > prices_values[i]]
    losses = [prices_values[i] - prices_values[i-1] for i in range(1, min(14, len(prices_values))) if prices_values[i] > prices_values[i-1]]
    
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    # Signal technique
    signal_score = 0
    signal_reasons = []
    
    # Tendance haussière
    if current > sma5 > sma10:
        signal_score += 20
        signal_reasons.append("Tendance haussière (prix > SMA5 > SMA10)")
    
    # RSI survendu (bon moment d'achat)
    if rsi < 30:
        signal_score += 25
        signal_reasons.append(f"RSI survendu ({rsi:.1f})")
    elif rsi > 70:
        signal_score -= 20
        signal_reasons.append(f"RSI suracheté ({rsi:.1f})")
    
    # Momentum positif
    if variation > 2:
        signal_score += 15
        signal_reasons.append(f"Momentum positif (+{variation:.1f}%)")
    elif variation < -2:
        signal_score -= 15
        signal_reasons.append(f"Momentum négatif ({variation:.1f}%)")
    
    # Volume analysis (si disponible)
    volumes = [p.get('attrs', {}).get('volume', 0) for p in prices if p.get('attrs', {}).get('volume')]
    if len(volumes) >= 2:
        avg_volume = sum(volumes[:5]) / 5 if len(volumes) >= 5 else sum(volumes) / len(volumes)
        current_volume = volumes[0]
        if current_volume > avg_volume * 1.5:
            signal_score += 10
            signal_reasons.append("Volume élevé")
    
    return {
        'current_price': current,
        'variation': variation,
        'sma5': sma5,
        'sma10': sma10,
        'sma20': sma20,
        'rsi': rsi,
        'signal_score': signal_score,
        'signal_reasons': signal_reasons
    }

def generate_signal(indicators, fundamentals=None):
    """Génère un signal d'achat/vente/conservation"""
    score = indicators['signal_score']
    
    # Ajout facteurs fondamentaux si disponibles
    if fundamentals:
        pe = fundamentals.get('pe_ratio', 0)
        if pe > 0 and pe < 15:
            score += 15
            indicators['signal_reasons'].append(f"P/E attractif ({pe:.1f})")
        
        dividend_yield = fundamentals.get('dividend_yield', 0)
        if dividend_yield > 5:
            score += 10
            indicators['signal_reasons'].append(f"Dividende élevé ({dividend_yield:.1f}%)")
    
    # Déterminer le signal
    if score >= 50:
        return 'ACHAT FORT', score, 85 + (score - 50) / 5
    elif score >= 30:
        return 'ACHAT', score, 70 + (score - 30) / 2
    elif score <= -30:
        return 'VENTE', score, 65
    elif score <= -50:
        return 'VENTE FORT', score, 75
    else:
        return 'CONSERVER', score, 60

def main():
    print("\n" + "="*90)
    print("🚀 ANALYSE IA RAPIDE - RECOMMANDATIONS BRVM")
    print("="*90)
    
    # Connexion MongoDB
    _, db = get_mongo_db()
    
    # Date limite (60 jours)
    threshold_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    
    # Récupérer toutes les actions BRVM
    print("\n📊 COLLECTE DES DONNÉES BRVM...")
    print("-" * 90)
    
    pipeline = [
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': '$key'}},
        {'$sort': {'_id': 1}}
    ]
    
    actions = list(db.curated_observations.aggregate(pipeline, allowDiskUse=True, maxTimeMS=30000))
    print(f"   ✓ {len(actions)} actions trouvées")
    
    # Analyser chaque action
    recommendations = {
        'buy_signals': [],
        'sell_signals': [],
        'hold_signals': [],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_analyzed': 0
    }
    
    print("\n⚙️ ANALYSE EN COURS...")
    print("-" * 90)
    
    for i, action_doc in enumerate(actions, 1):
        symbol = action_doc['_id']
        
        # Récupérer historique prix (limité à 60 derniers jours)
        prices = list(db.curated_observations.find({
            'source': 'BRVM',
            'key': symbol,
            'ts': {'$gte': threshold_date}
        }).sort('ts', -1).limit(60))
        
        if len(prices) < 5:
            print(f"   ⊘ {i:2d}. {symbol:15} - Données insuffisantes ({len(prices)} observations)")
            continue
        
        # Calcul indicateurs techniques
        indicators = calculate_technical_indicators(prices)
        if not indicators:
            continue
        
        # Récupérer données fondamentales (si disponibles)
        fundamentals_doc = db.curated_observations.find_one({
            'source': 'BRVM_FUNDAMENTALS',
            'key': symbol
        })
        
        fundamentals = fundamentals_doc.get('attrs', {}) if fundamentals_doc else None
        
        # Générer signal
        signal, score, confidence = generate_signal(indicators, fundamentals)
        
        recommendation = {
            'symbol': symbol,
            'signal': signal,
            'current_price': indicators['current_price'],
            'variation_daily': indicators['variation'],
            'rsi': indicators['rsi'],
            'signal_score': score,
            'confidence': confidence,
            'reasons': indicators['signal_reasons'][:5],  # Top 5 raisons
            'sma5': indicators['sma5'],
            'sma10': indicators['sma10'],
            'sma20': indicators['sma20'],
            'data_points': len(prices)
        }
        
        # Ajouter prix cible et stop loss pour signaux d'achat
        if 'ACHAT' in signal:
            target_gain = 0.15 if signal == 'ACHAT FORT' else 0.10
            recommendation['target_price'] = indicators['current_price'] * (1 + target_gain)
            recommendation['stop_loss'] = indicators['current_price'] * 0.95
            recommendation['potential_gain'] = target_gain * 100
            recommendations['buy_signals'].append(recommendation)
            status = "🟢 ACHAT"
        elif 'VENTE' in signal:
            recommendations['sell_signals'].append(recommendation)
            status = "🔴 VENTE"
        else:
            recommendations['hold_signals'].append(recommendation)
            status = "🟡 CONSERVER"
        
        print(f"   {status} {i:2d}. {symbol:15} Prix: {indicators['current_price']:>8.0f} FCFA  " +
              f"RSI: {indicators['rsi']:>5.1f}  Score: {score:>4.0f}  Conf: {confidence:>4.1f}%")
        
        recommendations['total_analyzed'] += 1
    
    # Trier les recommandations
    recommendations['buy_signals'].sort(key=lambda x: x['confidence'], reverse=True)
    recommendations['sell_signals'].sort(key=lambda x: x['confidence'], reverse=True)
    recommendations['hold_signals'].sort(key=lambda x: x['rsi'])
    
    # Sauvegarder dans MongoDB
    print("\n" + "="*90)
    print("💾 SAUVEGARDE DES RECOMMANDATIONS...")
    print("-" * 90)
    
    result = db.daily_recommendations.insert_one({
        'date': datetime.now(timezone.utc),
        'total_analyzed': recommendations['total_analyzed'],
        'buy_count': len(recommendations['buy_signals']),
        'sell_count': len(recommendations['sell_signals']),
        'hold_count': len(recommendations['hold_signals']),
        'recommendations': recommendations['buy_signals'] + recommendations['sell_signals'] + recommendations['hold_signals']
    })
    
    print(f"   ✓ Sauvegardé avec ID: {result.inserted_id}")
    
    # Sauvegarder aussi dans un fichier JSON
    with open('recommandations_ia_latest.json', 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"   ✓ Exporté vers: recommandations_ia_latest.json")
    
    # Afficher résumé
    print("\n" + "="*90)
    print("✅ RÉSULTATS DE L'ANALYSE IA")
    print("="*90)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   • Actions analysées: {recommendations['total_analyzed']}")
    print(f"   • Signaux d'ACHAT: {len(recommendations['buy_signals'])}")
    print(f"   • Signaux de VENTE: {len(recommendations['sell_signals'])}")
    print(f"   • À CONSERVER: {len(recommendations['hold_signals'])}")
    
    # Top 10 signaux d'achat
    if recommendations['buy_signals']:
        print(f"\n🟢 TOP 10 RECOMMANDATIONS D'ACHAT:")
        print("-" * 90)
        for i, rec in enumerate(recommendations['buy_signals'][:10], 1):
            print(f"\n{i}. {rec['symbol']} - {rec['signal']}")
            print(f"   Prix: {rec['current_price']:.0f} FCFA → Objectif: {rec.get('target_price', 0):.0f} FCFA " +
                  f"(+{rec.get('potential_gain', 0):.1f}%)")
            print(f"   Stop Loss: {rec.get('stop_loss', 0):.0f} FCFA")
            print(f"   Confiance: {rec['confidence']:.1f}% | RSI: {rec['rsi']:.1f}")
            print(f"   Raisons: {', '.join(rec['reasons'][:3])}")
    
    # Top 5 signaux de vente
    if recommendations['sell_signals']:
        print(f"\n🔴 TOP 5 RECOMMANDATIONS DE VENTE:")
        print("-" * 90)
        for i, rec in enumerate(recommendations['sell_signals'][:5], 1):
            print(f"\n{i}. {rec['symbol']} - {rec['signal']}")
            print(f"   Prix: {rec['current_price']:.0f} FCFA")
            print(f"   Confiance: {rec['confidence']:.1f}% | RSI: {rec['rsi']:.1f}")
            print(f"   Raisons: {', '.join(rec['reasons'][:3])}")
    
    print("\n" + "="*90)
    print("✅ ANALYSE TERMINÉE - Recommandations disponibles sur le dashboard")
    print("="*90)
    
    return recommendations

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

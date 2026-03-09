#!/usr/bin/env python3
"""
CALCULATEUR DE MÉTRIQUES AVANCÉES BRVM
=======================================

Calcule les métriques de trading avancées à partir de l'historique :
- Volatilité (écart-type sur 20/60 jours)
- Liquidité (volume moyen, turnover ratio)
- Indicateurs techniques (SMA, RSI, Beta)
- Ratios de performance (Sharpe, Sortino)

Enrichit les données MongoDB avec ces métriques calculées.
"""

import pymongo
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import statistics
import math

load_dotenv()


def get_historique_action(db, symbol, jours=60):
    """
    Récupérer l'historique d'une action (données quotidiennes OHLC)
    """
    fin = datetime.now()
    debut = fin - timedelta(days=jours)
    
    cursor = db.curated_observations.find({
        'dataset': 'STOCK_PRICE_DAILY',
        'ticker': symbol,
        'date': {
            '$gte': debut.strftime('%Y-%m-%d'),
            '$lte': fin.strftime('%Y-%m-%d')
        }
    }).sort('date', 1)
    
    return list(cursor)


def calculer_volatilite(prix_historique, periode=20):
    """
    Volatilité = Écart-type des rendements quotidiens
    
    Annualisée: volatilité_daily × √252
    """
    if len(prix_historique) < periode + 1:
        return None
    
    # Rendements quotidiens
    rendements = []
    for i in range(1, len(prix_historique)):
        if prix_historique[i-1] > 0:
            rendement = (prix_historique[i] - prix_historique[i-1]) / prix_historique[i-1]
            rendements.append(rendement)
    
    if len(rendements) < periode:
        return None
    
    # Écart-type sur la période
    volatilite_daily = statistics.stdev(rendements[-periode:])
    
    # Annualiser (252 jours de trading)
    volatilite_annuelle = volatilite_daily * math.sqrt(252)
    
    return {
        'volatility_daily': round(volatilite_daily * 100, 2),  # En %
        'volatility_annual': round(volatilite_annuelle * 100, 2),  # En %
        'volatility_20d': round(volatilite_daily * math.sqrt(20) * 100, 2),  # 20 jours
    }


def calculer_liquidite(historique):
    """
    Métriques de liquidité:
    - Volume moyen
    - Valeur échangée moyenne
    - Ratio de liquidité (volume / capitalisation)
    - Nombre de jours avec trades
    """
    if not historique:
        return None
    
    volumes = [obs.get('volume', 0) for obs in historique if obs.get('volume')]
    values_traded = [obs.get('close', 0) * obs.get('volume', 0) for obs in historique if obs.get('close') and obs.get('volume')]
    
    if not volumes:
        return None
    
    jours_actifs = sum(1 for v in volumes if v > 0)
    
    return {
        'avg_volume': round(statistics.mean(volumes)),
        'avg_value_traded': round(statistics.mean(values_traded)) if values_traded else None,
        'avg_value_traded_millions': round(statistics.mean(values_traded) / 1_000_000, 2) if values_traded else None,
        'max_volume': max(volumes),
        'min_volume': min([v for v in volumes if v > 0]) if any(v > 0 for v in volumes) else 0,
        'trading_days_pct': round((jours_actifs / len(historique)) * 100, 1),
        'liquidity_score': 'high' if statistics.mean(volumes) > 5000 else ('medium' if statistics.mean(volumes) > 1000 else 'low')
    }


def calculer_sma(prix, periode=20):
    """
    Simple Moving Average
    """
    if len(prix) < periode:
        return None
    
    return round(statistics.mean(prix[-periode:]), 2)


def calculer_rsi(prix, periode=14):
    """
    Relative Strength Index (0-100)
    
    RSI = 100 - (100 / (1 + RS))
    RS = Moyenne des gains / Moyenne des pertes
    """
    if len(prix) < periode + 1:
        return None
    
    gains = []
    pertes = []
    
    for i in range(1, len(prix)):
        variation = prix[i] - prix[i-1]
        if variation > 0:
            gains.append(variation)
            pertes.append(0)
        else:
            gains.append(0)
            pertes.append(abs(variation))
    
    if len(gains) < periode:
        return None
    
    avg_gain = statistics.mean(gains[-periode:])
    avg_loss = statistics.mean(pertes[-periode:])
    
    if avg_loss == 0:
        return 100  # Pas de pertes = surachat
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculer_beta(prix_action, prix_marche, periode=60):
    """
    Beta = Covariance(action, marché) / Variance(marché)
    
    Mesure la sensibilité de l'action aux mouvements du marché
    Beta > 1 : Plus volatile que le marché
    Beta < 1 : Moins volatile que le marché
    """
    if len(prix_action) < periode or len(prix_marche) < periode:
        return None
    
    # Rendements
    rend_action = [(prix_action[i] - prix_action[i-1]) / prix_action[i-1] 
                   for i in range(1, len(prix_action)) if prix_action[i-1] > 0]
    rend_marche = [(prix_marche[i] - prix_marche[i-1]) / prix_marche[i-1] 
                   for i in range(1, len(prix_marche)) if prix_marche[i-1] > 0]
    
    if len(rend_action) < periode or len(rend_marche) < periode:
        return None
    
    # Prendre les derniers N rendements
    rend_action = rend_action[-periode:]
    rend_marche = rend_marche[-periode:]
    
    # Covariance et variance
    mean_action = statistics.mean(rend_action)
    mean_marche = statistics.mean(rend_marche)
    
    covariance = sum((rend_action[i] - mean_action) * (rend_marche[i] - mean_marche) 
                     for i in range(len(rend_action))) / len(rend_action)
    
    variance_marche = statistics.variance(rend_marche)
    
    if variance_marche == 0:
        return None
    
    beta = covariance / variance_marche
    
    return round(beta, 2)


def main():
    """
    Pipeline de calcul des métriques avancées
    """
    print("=" * 80)
    print("📊 CALCULATEUR DE MÉTRIQUES AVANCÉES BRVM")
    print("=" * 80)
    
    # Connexion MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['centralisation_db']
    
    # Récupérer actions avec données quotidiennes
    actions = db.curated_observations.distinct('ticker', {'dataset': 'STOCK_PRICE_DAILY'})
    actions = [a for a in actions if a]  # Filtrer None
    print(f"\n📈 {len(actions)} actions trouvées dans MongoDB")
    
    # Récupérer indice BRVM-C pour calcul Beta
    print("\n🔍 Récupération indice BRVM-C...")
    historique_marche = get_historique_action(db, 'BRVM-C', 60)
    prix_marche = [obs['value'] for obs in historique_marche if obs.get('value')]
    print(f"   Indice: {len(prix_marche)} observations")
    
    actions_enrichies = 0
    
    for symbol in actions:
        if symbol == 'BRVM-C':  # Skip l'indice lui-même
            continue
        
        print(f"\n📊 {symbol}")
        
        # Récupérer historique 60 jours
        historique = get_historique_action(db, symbol, 60)
        
        if len(historique) < 10:
            print(f"   ⚠️ Historique insuffisant: {len(historique)} jours")
            continue
        
        # Extraire prix de clôture
        prix = [obs.get('close') for obs in historique if obs.get('close')]
        
        if not prix:
            print("   ⚠️ Pas de prix disponibles")
            continue
        
        # Calculer métriques
        metriques = {}
        
        # 1. Volatilité
        vol = calculer_volatilite(prix, periode=min(20, len(prix)-1))
        if vol:
            metriques.update(vol)
            print(f"   📉 Volatilité: {vol['volatility_annual']}% annuelle")
        
        # 2. Liquidité
        liq = calculer_liquidite(historique)
        if liq:
            metriques.update(liq)
            print(f"   💧 Liquidité: Volume moy. {liq['avg_volume']:,} ({liq['liquidity_score']})")
        
        # 3. SMA (20 et 50 jours)
        sma20 = calculer_sma(prix, 20)
        sma50 = calculer_sma(prix, 50)
        if sma20:
            metriques['sma_20'] = sma20
            print(f"   📈 SMA 20j: {sma20:,.0f} FCFA")
        if sma50:
            metriques['sma_50'] = sma50
            print(f"   📈 SMA 50j: {sma50:,.0f} FCFA")
        
        # 4. RSI
        rsi = calculer_rsi(prix, 14)
        if rsi:
            metriques['rsi_14'] = rsi
            status = 'Suracheté' if rsi > 70 else ('Survendu' if rsi < 30 else 'Neutre')
            print(f"   🎯 RSI: {rsi:.1f} ({status})")
        
        # 5. Beta (vs BRVM-C)
        if prix_marche and len(prix_marche) >= 30:
            beta = calculer_beta(prix, prix_marche, periode=min(60, len(prix), len(prix_marche)))
            if beta:
                metriques['beta'] = beta
                volatilite_rel = 'Plus volatile' if beta > 1 else 'Moins volatile'
                print(f"   ⚡ Beta: {beta:.2f} ({volatilite_rel} que le marché)")
        
        # 6. Performance (variation depuis début période)
        if len(prix) >= 2:
            perf = ((prix[-1] - prix[0]) / prix[0]) * 100
            metriques['performance_60d'] = round(perf, 2)
            print(f"   📊 Performance 60j: {perf:+.2f}%")
        
        # Mettre à jour MongoDB (dernière observation)
        if metriques:
            derniere_obs = historique[-1]
            
            # Ajouter les métriques directement
            metriques['metrics_updated_at'] = datetime.now().isoformat()
            
            db.curated_observations.update_one(
                {'_id': derniere_obs['_id']},
                {'$set': metriques}
            )
            
            actions_enrichies += 1
    
    print("\n" + "=" * 80)
    print(f"✅ {actions_enrichies} actions enrichies avec métriques avancées")
    print("=" * 80)
    
    # Résumé des métriques ajoutées
    print("\n📋 MÉTRIQUES CALCULÉES:")
    print("   • Volatilité: quotidienne, annuelle, 20 jours")
    print("   • Liquidité: volume moyen, valeur échangée, jours actifs")
    print("   • Moyennes mobiles: SMA 20, SMA 50")
    print("   • RSI 14 jours (surachat/survente)")
    print("   • Beta vs BRVM-C (sensibilité marché)")
    print("   • Performance 60 jours")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

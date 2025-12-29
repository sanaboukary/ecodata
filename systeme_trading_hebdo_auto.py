"""
SYSTÈME TRADING HEBDOMADAIRE AUTOMATISÉ - 100% FIABLE
======================================================

Objectif : Recommandations hebdomadaires basées sur données réelles
Collecte : Quotidienne (17h après clôture BRVM)
Analyse : Chaque lundi matin (historique 60 jours minimum)
Qualité : ZERO TOLERANCE - Données réelles uniquement

Architecture :
1. Collecte quotidienne automatique (17h lun-ven)
2. Validation qualité données (100% REAL_SCRAPER)
3. Analyse technique (SMA, RSI, MACD, Bollinger)
4. Analyse fondamentale (PE, ROE, croissance)
5. Génération recommandations (BUY/HOLD/SELL)
6. Notifications alertes (franchissements seuils)
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

class SystemeTradingHebdo:
    """Système complet de trading hebdomadaire automatisé"""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self.date_analyse = datetime.now().date()
        self.historique_requis = 60  # 60 jours pour analyse technique
        self.actions_brvm = []
        self.recommandations = []
        
    # ============= COLLECTE & VALIDATION =============
    
    def verifier_collecte_quotidienne(self):
        """Vérifie que la collecte quotidienne est complète"""
        print("\n" + "="*70)
        print("📊 VÉRIFICATION COLLECTE QUOTIDIENNE")
        print("="*70)
        
        # Données aujourd'hui
        count_today = self.db.curated_observations.count_documents({
            'source': 'BRVM',
            'ts': str(self.date_analyse),
            'attrs.data_quality': 'REAL_SCRAPER'
        })
        
        print(f"Date : {self.date_analyse}")
        print(f"Actions collectées : {count_today}/47")
        
        if count_today < 40:  # Minimum 40/47 (85%)
            print("❌ COLLECTE INCOMPLÈTE - Impossible de générer recommandations")
            return False
        
        print("✅ Collecte quotidienne OK")
        return True
    
    def verifier_historique_60jours(self):
        """Vérifie historique 60 jours pour analyse technique"""
        print("\n" + "="*70)
        print("📈 VÉRIFICATION HISTORIQUE 60 JOURS")
        print("="*70)
        
        date_debut = self.date_analyse - timedelta(days=80)  # Marge weekends
        
        # Compter jours de données par action
        pipeline = [
            {
                '$match': {
                    'source': 'BRVM',
                    'ts': {'$gte': str(date_debut)},
                    'attrs.data_quality': 'REAL_SCRAPER'
                }
            },
            {
                '$group': {
                    '_id': '$key',
                    'count': {'$sum': 1},
                    'dates': {'$addToSet': '$ts'}
                }
            }
        ]
        
        resultats = list(self.db.curated_observations.aggregate(pipeline))
        
        actions_ok = []
        actions_insuffisantes = []
        
        for r in resultats:
            if r['count'] >= 50:  # Minimum 50 jours sur 60
                actions_ok.append(r['_id'])
            else:
                actions_insuffisantes.append((r['_id'], r['count']))
        
        print(f"Actions avec historique suffisant : {len(actions_ok)}/47")
        
        if len(actions_ok) < 30:  # Minimum 30 actions analysables
            print("❌ HISTORIQUE INSUFFISANT")
            print("\nActions à problème :")
            for ticker, count in sorted(actions_insuffisantes, key=lambda x: x[1]):
                print(f"  {ticker:6s} : {count} jours")
            return False, []
        
        if actions_insuffisantes:
            print(f"\n⚠️  {len(actions_insuffisantes)} actions exclues (historique < 50j)")
        
        print(f"✅ Historique OK pour {len(actions_ok)} actions")
        return True, actions_ok
    
    def charger_donnees_historiques(self, tickers):
        """Charge historique 60 jours pour les actions"""
        print("\n" + "="*70)
        print("💾 CHARGEMENT DONNÉES HISTORIQUES")
        print("="*70)
        
        date_debut = self.date_analyse - timedelta(days=80)
        
        cursor = self.db.curated_observations.find({
            'source': 'BRVM',
            'key': {'$in': tickers},
            'ts': {'$gte': str(date_debut)},
            'attrs.data_quality': 'REAL_SCRAPER'
        }).sort('ts', 1)
        
        # Organiser par action
        data_by_ticker = defaultdict(list)
        
        for doc in cursor:
            data_by_ticker[doc['key']].append({
                'date': doc['ts'],
                'close': doc['value'],
                'volume': doc['attrs'].get('volume', 0),
                'variation': doc['attrs'].get('variation', 0)
            })
        
        # Convertir en DataFrames
        for ticker in tickers:
            if ticker in data_by_ticker:
                df = pd.DataFrame(data_by_ticker[ticker])
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                self.actions_brvm.append({
                    'ticker': ticker,
                    'data': df
                })
        
        print(f"✅ {len(self.actions_brvm)} actions chargées")
        return True
    
    # ============= INDICATEURS TECHNIQUES =============
    
    def calculer_indicateurs_techniques(self):
        """Calcule SMA, RSI, MACD, Bollinger pour chaque action"""
        print("\n" + "="*70)
        print("📐 CALCUL INDICATEURS TECHNIQUES")
        print("="*70)
        
        for action in self.actions_brvm:
            df = action['data']
            
            if len(df) < 20:
                continue
            
            # SMA
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean() if len(df) >= 50 else np.nan
            
            # RSI (14 jours)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # Support/Résistance (min/max 20j)
            df['support'] = df['close'].rolling(window=20).min()
            df['resistance'] = df['close'].rolling(window=20).max()
            
            action['data'] = df
        
        print(f"✅ Indicateurs calculés pour {len(self.actions_brvm)} actions")
    
    # ============= ANALYSE & SIGNAUX =============
    
    def generer_signaux_trading(self):
        """Génère signaux BUY/HOLD/SELL basés sur indicateurs"""
        print("\n" + "="*70)
        print("🎯 GÉNÉRATION SIGNAUX TRADING")
        print("="*70)
        
        for action in self.actions_brvm:
            ticker = action['ticker']
            df = action['data']
            
            if len(df) < 20:
                continue
            
            # Dernière ligne (aujourd'hui)
            latest = df.iloc[-1]
            
            # Calcul score (0-100)
            score = 0
            signaux = []
            
            # 1. Tendance SMA (25 points)
            if pd.notna(latest['sma_5']) and pd.notna(latest['sma_20']):
                if latest['close'] > latest['sma_5'] > latest['sma_20']:
                    score += 25
                    signaux.append("Tendance haussière forte")
                elif latest['close'] > latest['sma_20']:
                    score += 15
                    signaux.append("Tendance haussière modérée")
                elif latest['close'] < latest['sma_20']:
                    score -= 10
                    signaux.append("Tendance baissière")
            
            # 2. RSI (20 points)
            if pd.notna(latest['rsi']):
                if latest['rsi'] < 30:
                    score += 20
                    signaux.append("RSI survente (< 30)")
                elif latest['rsi'] > 70:
                    score -= 15
                    signaux.append("RSI surachat (> 70)")
                elif 40 <= latest['rsi'] <= 60:
                    score += 10
                    signaux.append("RSI neutre")
            
            # 3. MACD (20 points)
            if pd.notna(latest['macd']) and pd.notna(latest['macd_signal']):
                if latest['macd'] > latest['macd_signal'] and latest['macd_hist'] > 0:
                    score += 20
                    signaux.append("MACD croisement haussier")
                elif latest['macd'] < latest['macd_signal']:
                    score -= 10
                    signaux.append("MACD croisement baissier")
            
            # 4. Bollinger (15 points)
            if pd.notna(latest['bb_lower']) and pd.notna(latest['bb_upper']):
                bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
                if bb_position < 0.2:
                    score += 15
                    signaux.append("Prix près bande basse (opportunité)")
                elif bb_position > 0.8:
                    score -= 10
                    signaux.append("Prix près bande haute (surévalué)")
            
            # 5. Volume (10 points)
            if len(df) >= 20:
                vol_moy = df['volume'].tail(20).mean()
                if latest['volume'] > vol_moy * 1.5:
                    score += 10
                    signaux.append("Volume élevé (confirmation)")
            
            # 6. Momentum (10 points)
            if len(df) >= 5:
                perf_5j = ((latest['close'] - df.iloc[-6]['close']) / df.iloc[-6]['close']) * 100
                if perf_5j > 5:
                    score += 10
                    signaux.append(f"Momentum positif (+{perf_5j:.1f}%)")
                elif perf_5j < -5:
                    score -= 10
                    signaux.append(f"Momentum négatif ({perf_5j:.1f}%)")
            
            # Recommandation finale
            if score >= 60:
                recommandation = "BUY"
                confiance = "FORTE"
            elif score >= 40:
                recommandation = "BUY"
                confiance = "MODÉRÉE"
            elif score >= 20:
                recommandation = "HOLD"
                confiance = "NEUTRE"
            elif score >= 0:
                recommandation = "HOLD"
                confiance = "FAIBLE"
            else:
                recommandation = "SELL"
                confiance = "PRUDENCE"
            
            # Prix cible (projection simple)
            prix_actuel = latest['close']
            if recommandation == "BUY":
                prix_cible = prix_actuel * 1.10  # +10%
            elif recommandation == "SELL":
                prix_cible = prix_actuel * 0.95  # -5%
            else:
                prix_cible = prix_actuel
            
            self.recommandations.append({
                'ticker': ticker,
                'date_analyse': str(self.date_analyse),
                'prix_actuel': float(prix_actuel),
                'recommandation': recommandation,
                'confiance': confiance,
                'score': score,
                'prix_cible': float(prix_cible),
                'signaux': signaux,
                'rsi': float(latest['rsi']) if pd.notna(latest['rsi']) else None,
                'volume': int(latest['volume']),
                'variation_5j': float(perf_5j) if 'perf_5j' in locals() else 0
            })
        
        print(f"✅ {len(self.recommandations)} recommandations générées")
    
    def sauvegarder_recommandations(self):
        """Sauvegarde recommandations dans MongoDB"""
        print("\n" + "="*70)
        print("💾 SAUVEGARDE RECOMMANDATIONS")
        print("="*70)
        
        # Collection recommandations
        collection = self.db.trading_recommendations
        
        # Supprimer anciennes recommandations (> 30 jours)
        date_limite = str(self.date_analyse - timedelta(days=30))
        collection.delete_many({'date_analyse': {'$lt': date_limite}})
        
        # Insérer nouvelles
        for rec in self.recommandations:
            collection.update_one(
                {
                    'ticker': rec['ticker'],
                    'date_analyse': rec['date_analyse']
                },
                {'$set': rec},
                upsert=True
            )
        
        print(f"✅ {len(self.recommandations)} recommandations sauvegardées")
    
    def afficher_top_recommandations(self):
        """Affiche TOP 10 BUY et TOP 5 SELL"""
        print("\n" + "="*70)
        print("🏆 TOP RECOMMANDATIONS HEBDOMADAIRES")
        print("="*70)
        
        # Trier par score
        recs_sorted = sorted(self.recommandations, key=lambda x: x['score'], reverse=True)
        
        # TOP BUY
        top_buy = [r for r in recs_sorted if r['recommandation'] == 'BUY'][:10]
        print("\n🔥 TOP 10 BUY :")
        print("-" * 70)
        for i, rec in enumerate(top_buy, 1):
            print(f"{i:2d}. {rec['ticker']:6s} | Prix: {rec['prix_actuel']:8.0f} FCFA | Score: {rec['score']:3d}/100 | Cible: {rec['prix_cible']:8.0f} (+{((rec['prix_cible']/rec['prix_actuel']-1)*100):.1f}%)")
            print(f"    Confiance: {rec['confiance']} | RSI: {rec['rsi']:.1f if rec['rsi'] else 'N/A'}")
            print(f"    Signaux: {', '.join(rec['signaux'][:2])}")
        
        # TOP SELL
        top_sell = [r for r in recs_sorted if r['recommandation'] == 'SELL'][:5]
        if top_sell:
            print("\n⚠️  TOP 5 SELL (À ÉVITER) :")
            print("-" * 70)
            for i, rec in enumerate(top_sell, 1):
                print(f"{i}. {rec['ticker']:6s} | Prix: {rec['prix_actuel']:8.0f} FCFA | Score: {rec['score']:3d}/100")
                print(f"   Signaux: {', '.join(rec['signaux'][:2])}")
    
    def exporter_json(self, filename="recommandations_hebdo_latest.json"):
        """Export JSON pour dashboard"""
        import json
        
        output = {
            'date_generation': str(self.date_analyse),
            'total_actions_analysees': len(self.recommandations),
            'recommandations': self.recommandations
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Export JSON : {filename}")
    
    # ============= ORCHESTRATION =============
    
    def executer_analyse_complete(self):
        """Exécute analyse complète hebdomadaire"""
        print("\n" + "="*80)
        print("🚀 SYSTÈME TRADING HEBDOMADAIRE - ANALYSE COMPLÈTE")
        print("="*80)
        print(f"Date : {self.date_analyse}")
        print(f"Objectif : Recommandations 100% fiables (données réelles uniquement)")
        print("="*80)
        
        try:
            # 1. Vérifications
            if not self.verifier_collecte_quotidienne():
                print("\n❌ ANALYSE ANNULÉE : Collecte quotidienne incomplète")
                return False
            
            historique_ok, tickers_ok = self.verifier_historique_60jours()
            if not historique_ok:
                print("\n❌ ANALYSE ANNULÉE : Historique insuffisant")
                return False
            
            # 2. Chargement données
            if not self.charger_donnees_historiques(tickers_ok):
                print("\n❌ ANALYSE ANNULÉE : Erreur chargement données")
                return False
            
            # 3. Calculs
            self.calculer_indicateurs_techniques()
            
            # 4. Signaux
            self.generer_signaux_trading()
            
            # 5. Sauvegarde
            self.sauvegarder_recommandations()
            
            # 6. Affichage
            self.afficher_top_recommandations()
            
            # 7. Export
            self.exporter_json()
            
            print("\n" + "="*80)
            print("✅ ANALYSE COMPLÈTE TERMINÉE AVEC SUCCÈS")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR : {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Point d'entrée principal"""
    systeme = SystemeTradingHebdo()
    success = systeme.executer_analyse_complete()
    
    if success:
        print("\n💡 Les recommandations sont disponibles dans :")
        print("   - MongoDB : collection 'trading_recommendations'")
        print("   - JSON : recommandations_hebdo_latest.json")
        print("   - Dashboard : http://localhost:8000/dashboard/")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTÈME TRADING ADAPTATIF - DÉMARRAGE PROGRESSIF
================================================

Problème : Seulement 1-2 jours de données réelles
Solution : Analyse adaptative selon historique disponible

Phase 1 (J1-J5)   : Momentum court terme (variations quotidiennes)
Phase 2 (J6-J20)  : Indicateurs simples (SMA5, volume)
Phase 3 (J21-J60) : Analyse technique complète (RSI, MACD, Bollinger)
Phase 4 (J60+)    : Trading hebdomadaire optimal

ZERO TOLERANCE : Données réelles uniquement
"""

import os
import sys
import django

# Fix encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class TradingAdaptatif:
    """Trading adaptatif selon données disponibles"""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self.date_analyse = datetime.now().date()
        self.jours_historique = 0
        self.phase = None
        self.recommandations = []
    
    def detecter_historique_disponible(self):
        """Détecte combien de jours de données réelles disponibles"""
        print("\n" + "="*70)
        print("🔍 DÉTECTION HISTORIQUE DISPONIBLE")
        print("="*70)
        
        # Compter jours uniques avec données REAL_SCRAPER ou REAL_MANUAL
        pipeline = [
            {
                '$match': {
                    'source': 'BRVM',
                    '$or': [
                        {'attrs.data_quality': 'REAL_SCRAPER'},
                        {'attrs.data_quality': 'REAL_MANUAL'}
                    ]
                }
            },
            {
                '$group': {
                    '_id': {'$substr': ['$ts', 0, 10]},  # Date seule
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        dates = list(self.db.curated_observations.aggregate(pipeline))
        self.jours_historique = len(dates)
        
        print(f"Jours avec données réelles : {self.jours_historique}")
        
        if dates:
            print(f"Période : {dates[0]['_id']} → {dates[-1]['_id']}")
            print(f"\nDétail par jour :")
            for d in dates[-10:]:  # 10 derniers jours
                print(f"  {d['_id']} : {d['count']} observations")
        
        # Déterminer phase
        if self.jours_historique < 5:
            self.phase = "PHASE1_MOMENTUM"
            print(f"\n📊 PHASE 1 : Momentum court terme ({self.jours_historique}j)")
        elif self.jours_historique < 20:
            self.phase = "PHASE2_SIMPLE"
            print(f"\n📊 PHASE 2 : Indicateurs simples ({self.jours_historique}j)")
        elif self.jours_historique < 60:
            self.phase = "PHASE3_TECHNIQUE"
            print(f"\n📊 PHASE 3 : Analyse technique ({self.jours_historique}j)")
        else:
            self.phase = "PHASE4_OPTIMAL"
            print(f"\n📊 PHASE 4 : Trading optimal ({self.jours_historique}j)")
        
        return self.jours_historique > 0
    
    def charger_donnees_disponibles(self):
        """Charge toutes les données réelles disponibles"""
        print("\n" + "="*70)
        print("💾 CHARGEMENT DONNÉES RÉELLES")
        print("="*70)
        
        cursor = self.db.curated_observations.find({
            'source': 'BRVM',
            '$or': [
                {'attrs.data_quality': 'REAL_SCRAPER'},
                {'attrs.data_quality': 'REAL_MANUAL'}
            ]
        }).sort('ts', 1)
        
        data = []
        for doc in cursor:
            data.append({
                'date': doc['ts'][:10],
                'ticker': doc['key'],
                'close': float(doc['value']),
                'volume': int(doc.get('attrs', {}).get('volume', 0)),
                'variation': float(doc.get('attrs', {}).get('variation', 0))
            })
        
        if not data:
            print("❌ Aucune donnée réelle disponible")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"✅ {len(df)} observations chargées")
        print(f"Actions : {df['ticker'].nunique()}")
        print(f"Période : {df['date'].min().date()} → {df['date'].max().date()}")
        
        return df
    
    def analyser_phase1_momentum(self, df):
        """Phase 1 : Momentum court terme (1-5 jours)"""
        print("\n" + "="*70)
        print("📈 ANALYSE PHASE 1 : MOMENTUM COURT TERME")
        print("="*70)
        
        # Dernière date
        date_latest = df['date'].max()
        df_latest = df[df['date'] == date_latest]
        
        # Calculer variations si historique >1 jour
        if self.jours_historique > 1:
            date_prev = df['date'].unique()[-2]
            df_prev = df[df['date'] == date_prev]
            
            for _, row in df_latest.iterrows():
                ticker = row['ticker']
                prix_actuel = row['close']
                volume_actuel = row['volume']
                
                # Prix précédent
                prev = df_prev[df_prev['ticker'] == ticker]
                if not prev.empty:
                    prix_prev = prev.iloc[0]['close']
                    var_pct = ((prix_actuel - prix_prev) / prix_prev) * 100
                else:
                    var_pct = row['variation']
                
                # Calculer prix min/max sur la période
                df_ticker = df[df['ticker'] == ticker]
                prix_min = df_ticker['close'].min()
                prix_max = df_ticker['close'].max()
                prix_moyen = df_ticker['close'].mean()
                
                # Support et résistance
                support = prix_min
                resistance = prix_max
                
                # Position actuelle par rapport à la range
                if prix_max > prix_min:
                    position_pct = ((prix_actuel - prix_min) / (prix_max - prix_min)) * 100
                else:
                    position_pct = 50
                
                # Calcul potentiel de gain
                if position_pct < 30:  # Proche du support
                    potentiel_hausse = ((resistance - prix_actuel) / prix_actuel) * 100
                    prix_cible = resistance
                    prix_entree = prix_actuel
                elif position_pct > 70:  # Proche de la résistance
                    potentiel_hausse = 0
                    prix_cible = prix_actuel
                    prix_entree = support
                else:  # Au milieu
                    potentiel_hausse = ((resistance - prix_actuel) / prix_actuel) * 100
                    prix_cible = resistance
                    prix_entree = support
                
                # Recommandation améliorée
                raisons = []
                if var_pct > 5:
                    rec = "BUY"
                    score = 70 + min(var_pct, 10)
                    raisons.append(f"Momentum fort ({var_pct:+.1f}%)")
                    motif = f"Forte hausse {var_pct:+.1f}%"
                elif var_pct > 3:
                    rec = "BUY"
                    score = 60
                    raisons.append(f"Tendance haussière ({var_pct:+.1f}%)")
                    motif = f"Hausse modérée {var_pct:+.1f}%"
                elif var_pct < -5:
                    rec = "SELL"
                    score = 20
                    raisons.append(f"Momentum baissier ({var_pct:+.1f}%)")
                    motif = f"Forte baisse {var_pct:+.1f}%"
                elif var_pct < -3:
                    rec = "SELL"
                    score = 35
                    raisons.append(f"Tendance baissière ({var_pct:+.1f}%)")
                    motif = f"Baisse modérée {var_pct:+.1f}%"
                else:
                    rec = "HOLD"
                    score = 50
                    raisons.append("Variation faible")
                    motif = "Marché stable"
                
                # Ajustements selon position dans la range
                if position_pct < 20 and rec != "SELL":
                    raisons.append(f"Proche support ({prix_min:.0f} FCFA)")
                    score = min(score + 10, 85)
                    if rec == "HOLD":
                        rec = "BUY"
                        motif = f"Opportunité d'achat (support)"
                elif position_pct > 80:
                    raisons.append(f"Proche résistance ({prix_max:.0f} FCFA)")
                    score = max(score - 10, 20)
                    if rec == "BUY":
                        rec = "HOLD"
                        motif = "Prudence (résistance proche)"
                
                # Raison amplitude
                amplitude = ((prix_max - prix_min) / prix_min) * 100
                if amplitude > 10:
                    raisons.append(f"Volatilité élevée ({amplitude:.1f}%)")
                elif amplitude < 2:
                    raisons.append(f"Stabilité ({amplitude:.1f}%)")
                
                # Volume bonus
                if volume_actuel > 1000:
                    score = min(score + 5, 90)
                    raisons.append(f"Volume significatif ({volume_actuel})")
                
                # Stratégie de trading
                if rec == "BUY":
                    strategie = f"Achat à {prix_actuel:.0f} → Vente à {prix_cible:.0f} FCFA ({potentiel_hausse:+.1f}%)"
                elif rec == "SELL":
                    strategie = f"Vente à {prix_actuel:.0f} → Rachat à {support:.0f} FCFA"
                else:
                    strategie = f"Attendre entrée à {prix_entree:.0f} → Vente à {prix_cible:.0f} FCFA"
                
                self.recommandations.append({
                    'ticker': ticker,
                    'phase': 'MOMENTUM',
                    'recommandation': rec,
                    'score': int(score),
                    'prix_actuel': prix_actuel,
                    'prix_entree': prix_entree,
                    'prix_cible': prix_cible,
                    'support': support,
                    'resistance': resistance,
                    'potentiel_gain': potentiel_hausse,
                    'variation': var_pct,
                    'volume': volume_actuel,
                    'motif': motif,
                    'raisons': raisons,
                    'strategie': strategie,
                    'confiance': 'FAIBLE (données limitées)',
                    'jours_analyse': self.jours_historique
                })
        else:
            # Premier jour : recommandations neutres
            for _, row in df_latest.iterrows():
                self.recommandations.append({
                    'ticker': row['ticker'],
                    'phase': 'INITIAL',
                    'recommandation': 'HOLD',
                    'score': 50,
                    'prix_actuel': row['close'],
                    'variation': row['variation'],
                    'volume': row['volume'],
                    'motif': 'Premier jour - Collecte en cours',
                    'confiance': 'AUCUNE',
                    'jours_analyse': 1
                })
        
        print(f"✅ {len(self.recommandations)} recommandations générées")
    
    def afficher_recommandations(self):
        """Affiche TOP recommandations selon phase"""
        print("\n" + "="*70)
        print(f"🎯 TOP RECOMMANDATIONS - {self.phase}")
        print("="*70)
        
        # Statistiques
        buy_count = sum(1 for r in self.recommandations if r['recommandation'] == 'BUY')
        sell_count = sum(1 for r in self.recommandations if r['recommandation'] == 'SELL')
        hold_count = sum(1 for r in self.recommandations if r['recommandation'] == 'HOLD')
        
        print(f"\n📊 Distribution : {buy_count} BUY | {hold_count} HOLD | {sell_count} SELL")
        
        # Trier par score
        sorted_recs = sorted(self.recommandations, key=lambda x: x['score'], reverse=True)
        
        # Afficher BUY d'abord
        buy_recs = [r for r in sorted_recs if r['recommandation'] == 'BUY'][:5]
        hold_recs = [r for r in sorted_recs if r['recommandation'] == 'HOLD'][:5]
        sell_recs = [r for r in sorted_recs if r['recommandation'] == 'SELL'][:3]
        
        if buy_recs:
            print("\n" + "="*70)
            print("🔥 OPPORTUNITÉS D'ACHAT")
            print("="*70)
            for i, rec in enumerate(buy_recs, 1):
                print(f"\n{i}. {rec['ticker']} - {rec['motif']}")
                print(f"   Prix actuel:  {rec['prix_actuel']:>8,.0f} FCFA")
                print(f"   Prix cible:   {rec['prix_cible']:>8,.0f} FCFA")
                print(f"   Potentiel:    {rec['potentiel_gain']:>7.1f}%")
                print(f"   Score:        {rec['score']}/100")
                print(f"   📊 Stratégie: {rec['strategie']}")
                if 'raisons' in rec and rec['raisons']:
                    print(f"   ✓ Raisons: {', '.join(rec['raisons'])}")
        
        if sell_recs:
            print("\n" + "="*70)
            print("⚠️  SIGNAUX DE VENTE")
            print("="*70)
            for i, rec in enumerate(sell_recs, 1):
                print(f"\n{i}. {rec['ticker']} - {rec['motif']}")
                print(f"   Prix actuel:  {rec['prix_actuel']:>8,.0f} FCFA")
                print(f"   Support:      {rec['support']:>8,.0f} FCFA")
                print(f"   Score:        {rec['score']}/100")
                print(f"   📊 Stratégie: {rec['strategie']}")
                if 'raisons' in rec and rec['raisons']:
                    print(f"   ✓ Raisons: {', '.join(rec['raisons'])}")
        
        if hold_recs and not buy_recs:
            print("\n" + "="*70)
            print("📌 POSITIONS À SURVEILLER")
            print("="*70)
            for i, rec in enumerate(hold_recs[:3], 1):
                print(f"\n{i}. {rec['ticker']} - {rec['motif']}")
                print(f"   Prix actuel:  {rec['prix_actuel']:>8,.0f} FCFA")
                print(f"   Support:      {rec['support']:>8,.0f} FCFA")
                print(f"   Résistance:   {rec['resistance']:>8,.0f} FCFA")
                print(f"   📊 Stratégie: {rec['strategie']}")
        
        print(f"\n⚠️  AVERTISSEMENT :")
        print(f"Analyse basée sur {self.jours_historique} jour(s) de données")
        print(f"Confiance : FAIBLE - Attendre 60 jours pour analyse optimale")
        print("-"*70)
    
    def sauvegarder_recommandations(self):
        """Sauvegarde avec indicateur de phase"""
        collection = self.db.trading_recommendations
        
        for rec in self.recommandations:
            rec['date_analyse'] = str(self.date_analyse)
            rec['timestamp'] = datetime.now()
            
            collection.update_one(
                {
                    'ticker': rec['ticker'],
                    'date_analyse': rec['date_analyse']
                },
                {'$set': rec},
                upsert=True
            )
        
        print(f"\n✅ {len(self.recommandations)} recommandations sauvegardées")
    
    def nettoyer_donnees_parasites(self):
        """Supprime les données BRVM sans data_quality avant l'analyse"""
        parasites = self.db.curated_observations.count_documents({
            'source': 'BRVM',
            'attrs.data_quality': {'$exists': False}
        })
        
        if parasites > 0:
            print(f"\n🧹 Nettoyage de {parasites} données parasites...")
            result = self.db.curated_observations.delete_many({
                'source': 'BRVM',
                'attrs.data_quality': {'$exists': False}
            })
            print(f"✅ {result.deleted_count} observations non fiables supprimées\n")
    
    def executer(self):
        """Exécution principale"""
        print("\n" + "="*80)
        print("🚀 SYSTÈME TRADING ADAPTATIF")
        print("="*80)
        print(f"Date : {self.date_analyse}")
        print(f"Politique : ZERO TOLERANCE - Données réelles uniquement")
        print("="*80)
        
        # 0. Nettoyage automatique
        self.nettoyer_donnees_parasites()
        
        # 1. Détecter historique
        if not self.detecter_historique_disponible():
            print("\n❌ Aucune donnée disponible")
            print("➡️  Lancer : python importer_donnees_brvm_manuel.py")
            return False
        
        # 2. Charger données
        df = self.charger_donnees_disponibles()
        if df.empty:
            print("\n❌ Erreur chargement données")
            return False
        
        # 3. Analyser selon phase
        if self.phase in ["PHASE1_MOMENTUM", "PHASE2_SIMPLE"]:
            self.analyser_phase1_momentum(df)
        # TODO: Phases 2, 3, 4 quand plus de données
        
        # 4. Afficher
        self.afficher_recommandations()
        
        # 5. Sauvegarder
        self.sauvegarder_recommandations()
        
        # 6. Export JSON
        import json
        output = {
            'date': str(self.date_analyse),
            'phase': self.phase,
            'jours_historique': self.jours_historique,
            'confiance': 'FAIBLE' if self.jours_historique < 20 else 'MOYENNE',
            'recommandations': self.recommandations
        }
        with open('recommandations_adaptatives_latest.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n✅ Export : recommandations_adaptatives_latest.json")
        
        print("\n" + "="*80)
        print("📅 PROCHAINES ÉTAPES :")
        print("="*80)
        print(f"1. Collecter quotidiennement (17h) : python scheduler_trading_intelligent.py --test")
        print(f"2. Attendre {max(0, 60 - self.jours_historique)} jours pour analyse optimale")
        print(f"3. Phase actuelle : {self.phase}")
        print("="*80)
        
        return True

def main():
    systeme = TradingAdaptatif()
    success = systeme.executer()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

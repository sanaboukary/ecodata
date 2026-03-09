#!/usr/bin/env python3
"""Afficher les recommandations IA avec sentiment"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

_, db = get_mongo_db()

print("\n" + "="*100)
print("🤖 RECOMMANDATIONS IA - AVEC ANALYSE DE SENTIMENT")
print("="*100 + "\n")

# Récupérer dernières recommandations
today = datetime.now().strftime('%Y-%m-%d')
recos = list(db.curated_observations.find({
    'source': 'AI_ANALYSIS',
    'dataset': 'RECOMMENDATIONS',
    'ts': today
}).sort('attrs.confiance', -1))

if not recos:
    print("❌ Aucune recommandation trouvée pour aujourd'hui")
    print("\n💡 Générer recommandations: python generer_recommandations_maintenant.py\n")
    sys.exit(0)

# Grouper par décision
buy = [r for r in recos if r.get('attrs', {}).get('decision') == 'BUY']
sell = [r for r in recos if r.get('attrs', {}).get('decision') == 'SELL']
hold = [r for r in recos if r.get('attrs', {}).get('decision') == 'HOLD']

print(f"📊 Total: {len(recos)} recommandations")
print(f"   🟢 BUY:  {len(buy):2d} ({len(buy)/len(recos)*100:.0f}%)")
print(f"   🔴 SELL: {len(sell):2d} ({len(sell)/len(recos)*100:.0f}%)")
print(f"   🟡 HOLD: {len(hold):2d} ({len(hold)/len(recos)*100:.0f}%)")
print()

# Afficher TOP 5 BUY avec sentiment
if buy:
    print("="*100)
    print("🟢 TOP 5 SIGNAUX D'ACHAT (avec sentiment publications)")
    print("="*100 + "\n")
    
    for i, r in enumerate(buy[:5], 1):
        attrs = r.get('attrs', {})
        symbol = r['key']
        confiance = attrs.get('confiance', 0)
        prix = attrs.get('prix_actuel', 0)
        cible = attrs.get('prix_cible', 0)
        sentiment = attrs.get('sentiment', {})
        
        print(f"{i}. {symbol:10s} - {confiance}% confiance")
        print(f"   💰 Prix: {prix:,.0f} → {cible:,.0f} FCFA (+{(cible-prix)/prix*100:.1f}%)")
        
        # 🆕 Afficher sentiment
        if sentiment and sentiment.get('publications_count', 0) > 0:
            sent_label = sentiment.get('sentiment', 'neutral')
            sent_score = sentiment.get('score', 0)
            pub_count = sentiment.get('publications_count', 0)
            
            icon = "📈" if sent_label == 'positive' else "📉" if sent_label == 'negative' else "📊"
            print(f"   {icon} Sentiment: {sent_label.upper()} (score: {sent_score:+d}, {pub_count} publications)")
            
            # Publications récentes
            recent_pubs = sentiment.get('recent_publications', [])
            if recent_pubs:
                print(f"   📰 Publications récentes:")
                for pub in recent_pubs[:2]:
                    print(f"      • {pub.get('date')}: {pub.get('titre', '')[:65]}...")
        else:
            print(f"   📊 Sentiment: Aucune publication récente")
        
        # Raisons
        raisons = attrs.get('raisons', [])
        if raisons:
            print(f"   📋 Raisons:")
            for raison in raisons[:4]:
                print(f"      - {raison}")
        
        print()

# Statistiques sentiment global
print("="*100)
print("📊 STATISTIQUES SENTIMENT")
print("="*100 + "\n")

with_sentiment = [r for r in recos if r.get('attrs', {}).get('sentiment', {}).get('publications_count', 0) > 0]
positive_sent = [r for r in with_sentiment if r.get('attrs', {}).get('sentiment', {}).get('sentiment') == 'positive']
negative_sent = [r for r in with_sentiment if r.get('attrs', {}).get('sentiment', {}).get('sentiment') == 'negative']

print(f"Actions avec publications récentes : {len(with_sentiment)}/{len(recos)}")
print(f"   📈 Sentiment positif  : {len(positive_sent):2d}")
print(f"   📉 Sentiment négatif  : {len(negative_sent):2d}")
print(f"   📊 Sentiment neutre   : {len(with_sentiment) - len(positive_sent) - len(negative_sent):2d}")

print("\n" + "="*100)
print("✅ Dashboard accessible: http://127.0.0.1:8000/brvm/recommendations/")
print("="*100 + "\n")

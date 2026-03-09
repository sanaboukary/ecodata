from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("VÉRIFICATION ENRICHISSEMENT")
print("="*80)

# 1. RICHBOURSE
rich = list(db.curated_observations.find({'source': 'RICHBOURSE'}))
avec_contenu = sum(1 for r in rich if len(r.get('attrs', {}).get('contenu', '')) > 100)

print(f"\n📰 RICHBOURSE:")
print(f"   Total articles: {len(rich)}")
print(f"   Avec contenu (>100 chars): {avec_contenu}")
print(f"   Taux enrichissement: {avec_contenu/len(rich)*100:.1f}%" if len(rich) > 0 else "0%")

# 2. SCORES SÉMANTIQUES
print(f"\n📊 SCORES SÉMANTIQUES:")
agg = list(db.agregation_semantique_action.find())
print(f"   Actions avec agrégation: {len(agg)}")

if len(agg) > 0:
    print("\n   Top 5 actions:")
    for i, a in enumerate(agg[:5], 1):
        action = a.get('action', '?')
        ct = a.get('score_ct', 0)
        mt = a.get('score_mt', 0)
        lt = a.get('score_lt', 0)
        print(f"   {i}. {action:6} - CT:{ct:6.1f} | MT:{mt:6.1f} | LT:{lt:6.1f}")
else:
    print("   ❌ Aucune agrégation!")

# 3. RECOMMANDATIONS
print(f"\n🎯 RECOMMANDATIONS:")
decisions = list(db.decisions_finales_brvm.find().sort('_id', -1).limit(5))
print(f"   Décisions récentes: {len(decisions)}")

if len(decisions) > 0:
    print("\n   Top 5 recommandations:")
    for i, d in enumerate(decisions, 1):
        action = d.get('symbole', '?')
        decision = d.get('decision', '?')
        score = d.get('score_wos', 0)
        gain = d.get('potentiel_gain_pct', 0)
        print(f"   {i}. {action:6} | {decision:4} | WOS:{score:5.1f} | Gain:{gain:5.1f}%")

print("\n" + "="*80)

# Comparaison AVANT/APRÈS
if len(agg) == 0:
    print("❌ PROBLÈME: Aucune agrégation sémantique!")
    print("   Solutions:")
    print("   1. Vérifier que analyse_semantique_brvm_v3.py a tourné")
    print("   2. Vérifier que agregateur_semantique_actions.py a tourné")
    print("   3. Relancer: python pipeline_complet_pro.py")
elif avec_contenu == 0:
    print("❌ PROBLÈME: Aucun contenu dans RICHBOURSE!")
    print("   Solution: python enrichir_quick.py")
else:
    print("✅ SYSTÈME OPÉRATIONNEL!")
    print(f"   - {avec_contenu} articles avec contenu")
    print(f"   - {len(agg)} actions avec scores sémantiques")
    print(f"   - {len(decisions)} recommandations générées")
    
    # Vérifier si les scores ont changé
    scores_non_zero = sum(1 for a in agg if abs(a.get('score_mt', 0)) > 0.1)
    if scores_non_zero > 0:
        print(f"\n🎉 SUCCÈS! {scores_non_zero} actions ont des scores non-zéro!")
        print("   Vos recommandations sont maintenant DYNAMIQUES!")
    else:
        print("\n⚠️  Les scores sont toujours à 0")
        print("   Il faut relancer l'analyse sémantique")

print("="*80)

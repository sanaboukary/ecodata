#!/usr/bin/env python3
"""
Vérification des duplications d'actions BRVM
Recherche de variations et doublons
"""
from plateforme_centralisation.mongo import get_mongo_db
from collections import defaultdict

def main():
    print("="*80)
    print("🔍 VÉRIFICATION DES DUPLICATIONS BRVM")
    print("="*80)
    
    _, db = get_mongo_db()
    
    # Récupérer toutes les actions uniques
    actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
    
    print(f"\n📊 Total actions uniques: {len(actions)}")
    print("\n📋 Liste complète des actions dans MongoDB:")
    
    # Grouper par base (sans suffixe)
    groupes = defaultdict(list)
    
    for action in sorted(actions):
        # Extraire la base (sans .BC, etc.)
        base = action.split('.')[0] if '.' in action else action
        groupes[base].append(action)
    
    # Afficher et identifier les duplications
    duplications = []
    
    for i, action in enumerate(sorted(actions), 1):
        count = db.curated_observations.count_documents({
            'source': 'BRVM',
            'key': action
        })
        
        # Vérifier si c'est une duplication potentielle
        base = action.split('.')[0] if '.' in action else action
        if len(groupes[base]) > 1:
            print(f"   {i:3d}. ⚠️  {action:<15} ({count:,} obs) - DUPLICATION POTENTIELLE")
            duplications.append((base, groupes[base]))
        else:
            print(f"   {i:3d}. ✓  {action:<15} ({count:,} obs)")
    
    # Résumé des duplications
    if duplications:
        print(f"\n" + "="*80)
        print(f"❌ DUPLICATIONS DÉTECTÉES")
        print("="*80)
        
        # Dédupliquer la liste
        seen = set()
        unique_duplications = []
        for base, variants in duplications:
            if base not in seen:
                seen.add(base)
                unique_duplications.append((base, variants))
        
        for base, variants in unique_duplications:
            print(f"\n🔴 Groupe '{base}' ({len(variants)} variantes):")
            total_obs = 0
            for variant in variants:
                count = db.curated_observations.count_documents({
                    'source': 'BRVM',
                    'key': variant
                })
                total_obs += count
                print(f"   • {variant:<15} : {count:,} observations")
            
            print(f"   TOTAL: {total_obs:,} observations")
            
            # Recommandation
            if variants:
                # Choisir la variante la plus courante
                variante_principale = max(variants, key=lambda v: db.curated_observations.count_documents({
                    'source': 'BRVM',
                    'key': v
                }))
                autres = [v for v in variants if v != variante_principale]
                
                if autres:
                    print(f"   ✅ RECOMMANDATION: Garder '{variante_principale}', supprimer {autres}")
        
        # Commande de nettoyage
        print(f"\n" + "="*80)
        print(f"🧹 NETTOYAGE SUGGÉRÉ")
        print("="*80)
        print("\nPour chaque groupe, exécutez:")
        print("python nettoyer_duplications_brvm.py")
        
    else:
        print(f"\n✅ Aucune duplication détectée!")
    
    # Vérifier aussi les variations de casse
    print(f"\n" + "="*80)
    print(f"🔤 VÉRIFICATION CASSE (majuscules/minuscules)")
    print("="*80)
    
    actions_upper = defaultdict(list)
    for action in actions:
        actions_upper[action.upper()].append(action)
    
    casse_problems = {k: v for k, v in actions_upper.items() if len(v) > 1}
    
    if casse_problems:
        print("\n⚠️  Variations de casse détectées:")
        for upper, variants in casse_problems.items():
            print(f"   • {upper}: {variants}")
    else:
        print("\n✓ Pas de problème de casse")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

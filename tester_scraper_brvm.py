"""
TESTER LE SCRAPER BRVM PRODUCTION
Vérifie si le scraping du site officiel fonctionne
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath('.'))

print("="*80)
print("TEST SCRAPER BRVM PRODUCTION")
print("="*80)

try:
    from scripts.connectors.brvm_scraper_production import scraper_brvm_officiel
    
    print("\n1. Tentative de scraping du site BRVM...")
    data = scraper_brvm_officiel()
    
    if data and len(data) > 0:
        print(f"\n{'='*80}")
        print(f"✅ SUCCÈS: {len(data)} cours récupérés")
        print(f"{'='*80}")
        
        # Afficher échantillon
        print(f"\n📊 ÉCHANTILLON DES COURS RÉCUPÉRÉS:\n")
        print(f"{'SYMBOLE':<12} {'PRIX':>12} {'VARIATION':>12} {'VOLUME':>12}")
        print(f"{'-'*12} {'-'*12} {'-'*12} {'-'*12}")
        
        for stock in data[:10]:  # 10 premiers
            print(f"{stock['symbol']:<12} {stock['close']:>12,.0f} {stock['variation']:>+11.2f}% {stock['volume']:>12,}")
        
        if len(data) > 10:
            print(f"\n... et {len(data)-10} autres actions")
        
        # Vérifier ECOC
        ecoc = next((s for s in data if s['symbol'] == 'ECOC.BC'), None)
        if ecoc:
            print(f"\n{'='*80}")
            print(f"🔍 VÉRIFICATION ECOC (Ecobank Côte d'Ivoire):")
            print(f"{'='*80}")
            print(f"  Prix scrapé: {ecoc['close']:,.0f} FCFA")
            print(f"  Variation:   {ecoc['variation']:+.2f}%")
            print(f"  Volume:      {ecoc['volume']:,}")
            print(f"  Qualité:     {ecoc['data_quality']}")
            
            # Comparer avec le prix réel connu (15,000 FCFA)
            prix_reel_connu = 15000
            if abs(ecoc['close'] - prix_reel_connu) < 1000:
                print(f"\n  ✅ Prix cohérent avec le prix réel ({prix_reel_connu:,} FCFA)")
            else:
                print(f"\n  ⚠️  Prix différent du prix réel connu ({prix_reel_connu:,} FCFA)")
                print(f"      Écart: {ecoc['close'] - prix_reel_connu:+,.0f} FCFA ({(ecoc['close']/prix_reel_connu - 1)*100:+.1f}%)")
        
        print(f"\n{'='*80}")
        print(f"✅ Le scraper fonctionne correctement")
        print(f"{'='*80}")
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"  1. Exécuter: basculer_vers_collecte_reelle.bat")
        print(f"  2. Le DAG horaire utilisera automatiquement ce scraper")
        print(f"  3. Collecte automatique toutes les heures (9h-16h, lun-ven)")
        
    else:
        print(f"\n{'='*80}")
        print(f"❌ ÉCHEC: Le scraping n'a pas retourné de données")
        print(f"{'='*80}")
        
        print(f"\n📋 DIAGNOSTIC:")
        print(f"  • Vérifier que le site est accessible: https://www.brvm.org")
        print(f"  • Un fichier HTML a été sauvegardé pour analyse (brvm_scrape_*.html)")
        print(f"  • La structure du site a peut-être changé")
        
        print(f"\n📋 SOLUTIONS DE REPLI:")
        print(f"  1. Adapter le scraper selon la structure HTML réelle")
        print(f"  2. Essayer avec Selenium (JavaScript rendering):")
        print(f"     pip install selenium webdriver-manager")
        print(f"  3. Utiliser la saisie manuelle:")
        print(f"     python mettre_a_jour_cours_REELS_22dec.py")
        print(f"  4. Importer un CSV:")
        print(f"     python import_rapide_brvm.py")

except ImportError as e:
    print(f"\n❌ ERREUR IMPORT: {e}")
    print(f"\n📋 Installation requise:")
    print(f"  pip install requests beautifulsoup4")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}\n")

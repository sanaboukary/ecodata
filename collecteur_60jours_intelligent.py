#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecteur intelligent pour obtenir 60 jours de données BRVM RÉELLES
Essaie plusieurs méthodes et guide l'utilisateur
"""

import os
import sys
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Fix encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Actions BRVM (47 au total)
ACTIONS_BRVM = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS', 'CABC',
    'CBIBF', 'CFAC', 'CIEC', 'ETIT', 'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONTBF', 'ORGT',
    'PALC', 'PRSC', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC',
    'SICC', 'SICG', 'SIVC', 'SITC', 'SLBC', 'SMBC', 'SNTS', 'SOAC', 'SOGC', 'SPHC',
    'STAC', 'SVOC', 'TPCI', 'TTLC', 'TTLS', 'TTRC', 'UNLC', 'UNLB', 'UNXC'
]

def collecter_depuis_scraper():
    """Méthode 1: Collecter quotidiennement pendant 60 jours"""
    print("\n" + "="*80)
    print("MÉTHODE 1 : COLLECTE QUOTIDIENNE AUTOMATIQUE")
    print("="*80)
    print("""
Cette méthode collecte automatiquement les données chaque jour à 17h.

AVANTAGES:
   ✓ Données 100% réelles et vérifiées
   ✓ Totalement automatique
   ✓ Continue indéfiniment après 60 jours

INCONVÉNIENT:
   ✗ Nécessite 57 jours d'attente

COMMENT:
   1. Lancer: python scheduler_trading_intelligent.py
   2. Le laisser tourner en arrière-plan
   3. Chaque jour à 17h: collecte automatique
   4. Après 60 jours: historique complet disponible

PENDANT L'ATTENTE:
   • Utiliser le système adaptatif:
     python trading_adaptatif_demo.py
   • Les recommandations s'améliorent progressivement
   • À partir de 21 jours: analyse technique disponible
""")
    
    reponse = input("\nActiver la collecte automatique maintenant ? (oui/non): ").strip().lower()
    
    if reponse in ['oui', 'o', 'yes', 'y']:
        print("\n🚀 Lancement du scheduler...")
        import subprocess
        subprocess.Popen([sys.executable, "scheduler_trading_intelligent.py"])
        print("✅ Scheduler démarré en arrière-plan")
        print("   Collecte quotidienne: 17h00 (Lun-Ven)")
        print("   Arrêter avec: Ctrl+C dans le terminal du scheduler")
        return True
    
    return False

def collecter_depuis_bulletins_pdf():
    """Méthode 2: Parser les bulletins PDF BRVM"""
    print("\n" + "="*80)
    print("MÉTHODE 2 : BULLETINS PDF BRVM")
    print("="*80)
    print("""
Cette méthode parse les bulletins officiels BRVM (format PDF).

AVANTAGES:
   ✓ Données 100% officielles BRVM
   ✓ Historique complet en quelques minutes
   ✓ Format standard et fiable

ÉTAPES:
   1. Aller sur: https://www.brvm.org/fr/investir/publications
   2. Chercher "Bulletins de la cote" ou "Bulletins quotidiens"
   3. Télécharger les 60 bulletins les plus récents (PDF)
   4. Les placer dans le dossier: bulletins_brvm/
   5. Lancer: python parser_bulletins_brvm.py
   6. Importer le CSV généré

DURÉE ESTIMÉE:
   • Téléchargement manuel: 15-30 minutes
   • Parsing automatique: 2-5 minutes
   • Import: 1 minute
   • TOTAL: ~30-40 minutes
""")
    
    # Vérifier si des PDFs existent déjà
    bulletins_dir = Path("bulletins_brvm")
    pdfs = list(bulletins_dir.glob("*.pdf")) if bulletins_dir.exists() else []
    
    if pdfs:
        print(f"\n✅ {len(pdfs)} bulletins PDF trouvés dans bulletins_brvm/")
        reponse = input("Parser ces bulletins maintenant ? (oui/non): ").strip().lower()
        
        if reponse in ['oui', 'o', 'yes', 'y']:
            print("\n🔍 Parsing en cours...")
            import subprocess
            result = subprocess.run([sys.executable, "parser_bulletins_brvm.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Parsing terminé")
                print(result.stdout)
                
                # Chercher le CSV généré
                csv_file = "historique_brvm_bulletins.csv"
                if Path(csv_file).exists():
                    print(f"\n📊 CSV généré: {csv_file}")
                    reponse2 = input("Importer maintenant ? (oui/non): ").strip().lower()
                    
                    if reponse2 in ['oui', 'o', 'yes', 'y']:
                        result2 = subprocess.run([sys.executable, "collecter_csv_automatique.py", 
                                                "--fichier", csv_file],
                                               capture_output=True, text=True)
                        print(result2.stdout)
                        return result2.returncode == 0
            else:
                print(f"❌ Erreur parsing: {result.stderr}")
    else:
        print("\n❌ Aucun bulletin PDF trouvé dans bulletins_brvm/")
        print("\n💡 Étapes suivantes:")
        print("   1. Créer le dossier: mkdir bulletins_brvm")
        print("   2. Télécharger 60 bulletins depuis www.brvm.org")
        print("   3. Relancer ce script")
    
    return False

def collecter_depuis_csv_externe():
    """Méthode 3: Import CSV fourni par courtier ou autre source"""
    print("\n" + "="*80)
    print("MÉTHODE 3 : IMPORT CSV EXTERNE")
    print("="*80)
    print("""
Cette méthode importe un fichier CSV que vous fournissez.

SOURCES POSSIBLES:
   1. Courtier BRVM (SGI, EDC, Hudson, BICI Bourse)
      → Demander: "Export historique cours 60 jours"
      
   2. Terminal Bloomberg/Reuters (si accès)
      → Export données BRVM
      
   3. Autre source fiable
      → Vérifier que prix sont réalistes

FORMAT REQUIS:
   DATE,SYMBOL,CLOSE,VOLUME,VARIATION
   2025-12-15,SNTS,25500,8500,2.3
   2025-12-15,SGBC,29490,1200,-1.2

VALIDATION AUTOMATIQUE:
   ✓ Vérification format
   ✓ Validation prix (SNTS devrait être ~25500)
   ✓ Détection données simulées
   ✓ Rapport détaillé avant import
""")
    
    # Lister fichiers CSV disponibles
    csv_files = list(Path(".").glob("*.csv"))
    csv_files = [f for f in csv_files if f.name not in [
        'modele_import_brvm.csv', 
        'donnees_reelles_brvm.csv',
        'template_import_brvm.csv',
        'observation_complement.csv'
    ]]
    
    if csv_files:
        print(f"\n📁 Fichiers CSV trouvés ({len(csv_files)}):")
        for i, f in enumerate(csv_files, 1):
            size = f.stat().st_size / 1024
            print(f"   {i}. {f.name} ({size:.1f} KB)")
        
        print("\n⚠️  ATTENTION: Certains fichiers peuvent contenir des données SIMULÉES")
        print("   Le script va d'abord VALIDER avant d'importer")
        
        choix = input(f"\nChoisir un fichier (1-{len(csv_files)}) ou 'n' pour nouveau: ").strip()
        
        if choix.lower() != 'n' and choix.isdigit():
            idx = int(choix) - 1
            if 0 <= idx < len(csv_files):
                csv_file = csv_files[idx]
                return valider_et_importer_csv(str(csv_file))
    
    # Nouveau fichier
    print("\n📝 Nouveau fichier CSV:")
    fichier = input("Nom du fichier (ex: mon_historique.csv): ").strip()
    
    if fichier and Path(fichier).exists():
        return valider_et_importer_csv(fichier)
    else:
        print(f"❌ Fichier '{fichier}' introuvable")
        return False

def valider_et_importer_csv(filepath):
    """Valide un CSV et l'importe si OK"""
    print(f"\n🔍 Validation de {filepath}...")
    
    try:
        import pandas as pd
        
        # Lire CSV
        df = pd.read_csv(filepath)
        
        print(f"\n📊 Statistiques:")
        print(f"   Lignes: {len(df)}")
        print(f"   Colonnes: {list(df.columns)}")
        
        # Vérifier colonnes requises
        required = ['DATE', 'SYMBOL', 'CLOSE']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            print(f"❌ Colonnes manquantes: {missing}")
            return False
        
        # Vérifier période
        if 'DATE' in df.columns:
            dates = pd.to_datetime(df['DATE'], errors='coerce')
            jours_uniques = dates.nunique()
            
            print(f"   Période: {dates.min().date()} à {dates.max().date()}")
            print(f"   Jours uniques: {jours_uniques}")
        
        # Vérifier prix SNTS (indicateur de données réelles)
        if 'SYMBOL' in df.columns and 'CLOSE' in df.columns:
            snts_data = df[df['SYMBOL'] == 'SNTS']['CLOSE']
            
            if len(snts_data) > 0:
                prix_moyen = snts_data.mean()
                prix_min = snts_data.min()
                prix_max = snts_data.max()
                
                print(f"\n🔍 Vérification SNTS (indicateur qualité):")
                print(f"   Prix moyen: {prix_moyen:.0f} FCFA")
                print(f"   Plage: {prix_min:.0f} - {prix_max:.0f} FCFA")
                
                # Prix réel SNTS devrait être ~25000-26000
                if prix_moyen < 20000 or prix_moyen > 30000:
                    print(f"\n⚠️  ALERTE: Prix SNTS suspect ({prix_moyen:.0f} FCFA)")
                    print(f"   Prix réel attendu: ~25500 FCFA")
                    print(f"   Ces données pourraient être SIMULÉES")
                    
                    reponse = input("\nContinuer quand même ? (oui/non): ").strip().lower()
                    if reponse not in ['oui', 'o', 'yes', 'y']:
                        print("❌ Import annulé")
                        return False
                else:
                    print(f"   ✅ Prix cohérent avec données réelles")
        
        # Proposer import
        print(f"\n" + "="*80)
        print(f"RÉSUMÉ VALIDATION:")
        print(f"   Fichier: {filepath}")
        print(f"   Lignes: {len(df)}")
        print(f"   Jours: {jours_uniques if 'jours_uniques' in locals() else 'N/A'}")
        print(f"   Statut: {'✅ PRÊT' if not missing else '❌ INCOMPLET'}")
        print("="*80)
        
        reponse = input("\nImporter ce fichier ? (oui/non): ").strip().lower()
        
        if reponse in ['oui', 'o', 'yes', 'y']:
            print(f"\n💾 Import en cours...")
            
            import subprocess
            result = subprocess.run([sys.executable, "collecter_csv_automatique.py", 
                                   "--fichier", filepath],
                                  capture_output=True, text=True)
            
            print(result.stdout)
            
            if result.returncode == 0:
                print("\n✅ Import réussi")
                return True
            else:
                print(f"\n❌ Erreur: {result.stderr}")
                return False
        
    except Exception as e:
        print(f"❌ Erreur validation: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("COLLECTEUR INTELLIGENT - 60 JOURS DONNÉES BRVM")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*80)
    
    # État actuel
    try:
        client, db = get_mongo_db()
        dates_real = db.curated_observations.distinct('ts', {
            'source': 'BRVM', 
            'attrs.data_quality': {'$in': ['REAL_SCRAPER', 'REAL_MANUAL']}
        })
        jours_actuels = len(dates_real)
        client.close()
        
        print(f"\n📊 ÉTAT ACTUEL:")
        print(f"   Jours avec données réelles: {jours_actuels}")
        print(f"   Objectif: 60 jours")
        print(f"   Manquant: {60 - jours_actuels} jours")
        
        if jours_actuels >= 60:
            print("\n✅ OBJECTIF DÉJÀ ATTEINT !")
            print("\nLancer l'analyse:")
            print("   python systeme_trading_hebdo_auto.py")
            return
        
    except Exception as e:
        print(f"⚠️  Impossible de vérifier l'état: {e}")
        jours_actuels = 0
    
    # Menu des méthodes
    print("\n" + "="*80)
    print("MÉTHODES DISPONIBLES:")
    print("="*80)
    print("""
1. 📅 Collecte quotidienne automatique (57 jours d'attente)
   → Données 100% réelles, totalement automatique
   → Démarre immédiatement, continue indéfiniment

2. 📄 Import bulletins PDF BRVM (30-40 minutes)
   → Téléchargement manuel + parsing automatique
   → Données officielles BRVM

3. 💾 Import CSV externe (5-10 minutes)
   → Fichier fourni par courtier ou autre source
   → Validation automatique avant import

0. ❌ Quitter
""")
    
    choix = input("Choisir une méthode (1-3): ").strip()
    
    if choix == '1':
        collecter_depuis_scraper()
    elif choix == '2':
        collecter_depuis_bulletins_pdf()
    elif choix == '3':
        collecter_depuis_csv_externe()
    elif choix == '0':
        print("\n👋 Au revoir !")
        return
    else:
        print("\n❌ Choix invalide")
        return
    
    # Vérifier résultat final
    print("\n" + "="*80)
    print("VÉRIFICATION FINALE")
    print("="*80)
    
    import subprocess
    subprocess.run([sys.executable, "verifier_historique_rapide.py"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processus interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

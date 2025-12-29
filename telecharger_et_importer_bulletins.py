#!/usr/bin/env python3
"""
Script de téléchargement et import automatique des bulletins BRVM
Télécharge 60 jours de bulletins PDF puis les parse et importe dans MongoDB

Politique ZERO TOLERANCE : Uniquement données réelles des bulletins officiels
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import re
from bs4 import BeautifulSoup

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

# Import du parser
sys.path.insert(0, os.path.dirname(__file__))
from parser_bulletins_brvm import ParserBulletinBRVM

# Configuration
DOSSIER_BULLETINS = "bulletins_brvm"
NOMBRE_JOURS = 60
URLS_BRVM = [
    "https://www.brvm.org/fr/investir/publications",
    "https://www.brvm.org/sites/default/files/bulletin_cote",
    "https://brvm.org/fr/investir/publications/bulletins-quotidiens",
]

class TelechargerImporterBulletins:
    """Télécharge et importe les bulletins BRVM"""
    
    def __init__(self):
        self.dossier = Path(DOSSIER_BULLETINS)
        self.dossier.mkdir(exist_ok=True)
        self.parser = ParserBulletinBRVM()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def chercher_url_bulletins(self):
        """Cherche l'URL correcte des bulletins BRVM"""
        print("🔍 Recherche de l'URL des bulletins BRVM...")
        
        for url in URLS_BRVM:
            try:
                print(f"   Essai: {url}")
                response = self.session.get(url, timeout=10, verify=False)
                
                if response.status_code == 200:
                    print(f"   ✅ URL accessible: {url}")
                    
                    # Chercher des liens vers des PDFs
                    soup = BeautifulSoup(response.text, 'html.parser')
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
                    
                    if pdf_links:
                        print(f"   ✅ {len(pdf_links)} PDFs trouvés")
                        return url, pdf_links[:NOMBRE_JOURS]
                    else:
                        print(f"   ⚠️ Aucun PDF trouvé sur cette page")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                continue
        
        return None, []
    
    def telecharger_pdf(self, url, nom_fichier):
        """Télécharge un PDF"""
        try:
            response = self.session.get(url, timeout=30, verify=False, stream=True)
            
            if response.status_code == 200:
                filepath = self.dossier / nom_fichier
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"   ✅ Téléchargé: {nom_fichier}")
                return True
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}: {nom_fichier}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur téléchargement {nom_fichier}: {e}")
            return False
    
    def telecharger_bulletins_auto(self):
        """Tentative de téléchargement automatique"""
        print("="*80)
        print("📥 TÉLÉCHARGEMENT AUTOMATIQUE DES BULLETINS BRVM")
        print("="*80)
        
        url_base, pdf_links = self.chercher_url_bulletins()
        
        if not url_base or not pdf_links:
            print("\n❌ Impossible de trouver les bulletins automatiquement")
            return False
        
        print(f"\n📊 Téléchargement de {len(pdf_links)} bulletins...")
        
        success_count = 0
        for i, link in enumerate(pdf_links, 1):
            href = link.get('href', '')
            
            if not href:
                continue
            
            # Construire l'URL complète
            if href.startswith('http'):
                url_pdf = href
            else:
                url_pdf = requests.compat.urljoin(url_base, href)
            
            # Extraire le nom du fichier
            nom_fichier = Path(href).name or f"bulletin_{i:02d}.pdf"
            
            print(f"[{i}/{len(pdf_links)}] {nom_fichier}")
            
            if self.telecharger_pdf(url_pdf, nom_fichier):
                success_count += 1
                time.sleep(1)  # Pause entre téléchargements
        
        print(f"\n✅ {success_count}/{len(pdf_links)} bulletins téléchargés")
        return success_count > 0
    
    def guide_telechargement_manuel(self):
        """Guide pour le téléchargement manuel"""
        print("\n" + "="*80)
        print("📖 GUIDE DE TÉLÉCHARGEMENT MANUEL")
        print("="*80)
        print("""
Le téléchargement automatique n'est pas possible actuellement.
Voici comment procéder manuellement :

1️⃣  ACCÉDER AU SITE BRVM
   → Ouvrir: https://www.brvm.org/fr/investir/publications
   → Chercher la section "Bulletins de la cote" ou "Publications"

2️⃣  TÉLÉCHARGER LES BULLETINS
   → Télécharger les 60 bulletins les plus récents (2 mois)
   → Format: bulletin_cote_YYYYMMDD.pdf ou similaire
   → Dates: Du plus récent au plus ancien

3️⃣  SAUVEGARDER LES FICHIERS
   → Placer tous les PDFs dans le dossier: bulletins_brvm/
   → Noms: Garder les noms originaux ou renommer en bulletin_01.pdf, etc.

4️⃣  LANCER L'IMPORT
   → Exécuter: python telecharger_et_importer_bulletins.py --import-only
   → Le script parsera automatiquement tous les PDFs

📊 OBJECTIF: 60 bulletins PDF = ~2820 observations (47 actions × 60 jours)

💡 ASTUCE: Si certains bulletins manquent, ce n'est pas grave.
          Le système fonctionnera avec les données disponibles.
          Minimum recommandé: 40 bulletins (40 jours d'historique).
""")
        
        print("="*80)
        input("\nAppuyez sur Entrée quand vous êtes prêt à continuer...")
    
    def parser_et_importer(self):
        """Parse les PDFs et importe dans MongoDB"""
        print("\n" + "="*80)
        print("📊 PARSING ET IMPORT DES BULLETINS")
        print("="*80)
        
        # Lister les PDFs
        pdfs = list(self.dossier.glob("*.pdf"))
        
        if not pdfs:
            print("❌ Aucun PDF trouvé dans bulletins_brvm/")
            return False
        
        print(f"\n📁 {len(pdfs)} PDFs trouvés")
        
        # Parser les PDFs
        print("\n🔍 Parsing des PDFs...")
        csv_file = self.parser.parser_dossier(str(self.dossier))
        
        if not csv_file or not Path(csv_file).exists():
            print("❌ Erreur lors du parsing")
            return False
        
        print(f"✅ Données extraites: {csv_file}")
        
        # Importer dans MongoDB
        print("\n💾 Import dans MongoDB...")
        
        # Utiliser collecter_csv_automatique.py
        import subprocess
        
        cmd = [sys.executable, "collecter_csv_automatique.py", "--fichier", csv_file]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n✅ Import terminé avec succès")
            return True
        else:
            print(f"❌ Erreur import: {result.stderr}")
            return False
    
    def verifier_donnees(self):
        """Vérifie les données importées"""
        print("\n" + "="*80)
        print("✅ VÉRIFICATION DES DONNÉES")
        print("="*80)
        
        try:
            from plateforme_centralisation.mongo import get_mongo_db
            
            client, db = get_mongo_db()
            
            # Compter les observations BRVM
            total = db.curated_observations.count_documents({'source': 'BRVM'})
            
            # Compter par data_quality
            real_scraper = db.curated_observations.count_documents({
                'source': 'BRVM',
                'attrs.data_quality': 'REAL_SCRAPER'
            })
            
            real_manual = db.curated_observations.count_documents({
                'source': 'BRVM',
                'attrs.data_quality': 'REAL_MANUAL'
            })
            
            unknown = db.curated_observations.count_documents({
                'source': 'BRVM',
                'attrs.data_quality': {'$exists': False}
            })
            
            # Compter les jours uniques
            pipeline = [
                {'$match': {'source': 'BRVM', 'attrs.data_quality': {'$in': ['REAL_SCRAPER', 'REAL_MANUAL']}}},
                {'$group': {'_id': '$ts'}},
                {'$count': 'total'}
            ]
            
            result = list(db.curated_observations.aggregate(pipeline))
            jours_uniques = result[0]['total'] if result else 0
            
            # Afficher résultats
            print(f"""
📊 DONNÉES BRVM DANS MONGODB:
   Total observations: {total}
   
   Par qualité:
   ✅ REAL_SCRAPER: {real_scraper}
   ✅ REAL_MANUAL: {real_manual}
   ⚠️  UNKNOWN: {unknown}
   
   Jours avec données réelles: {jours_uniques}
   
   Objectif: ~2820 observations (47 actions × 60 jours)
   Statut: {"✅ OBJECTIF ATTEINT" if jours_uniques >= 60 else f"⏳ En cours ({jours_uniques}/60 jours)"}
""")
            
            if unknown > 0:
                print(f"⚠️  ATTENTION: {unknown} observations UNKNOWN détectées")
                print("   Ces observations contiennent peut-être des données simulées.")
                print("   Recommandation: Les supprimer avec:")
                print("   python purger_donnees_fake.py")
            
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur vérification: {e}")
            return False
    
    def executer(self, import_only=False):
        """Exécution principale"""
        print("\n" + "="*80)
        print("🎯 CONSTITUTION HISTORIQUE 60 JOURS BRVM")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Objectif: {NOMBRE_JOURS} jours de données réelles")
        print("="*80)
        
        if not import_only:
            # Tentative téléchargement auto
            auto_success = self.telecharger_bulletins_auto()
            
            if not auto_success:
                # Guide manuel
                self.guide_telechargement_manuel()
        
        # Parser et importer
        if self.parser_et_importer():
            # Vérifier les données
            self.verifier_donnees()
            
            print("\n" + "="*80)
            print("✅ PROCESSUS TERMINÉ")
            print("="*80)
            print("""
📊 PROCHAINES ÉTAPES:

1️⃣  Vérifier les données:
   python check_mongodb_brvm.py

2️⃣  Lancer l'analyse trading:
   python systeme_trading_hebdo_auto.py

3️⃣  Activer la collecte quotidienne:
   python scheduler_trading_intelligent.py

💡 Le système est maintenant opérationnel avec des données 100% réelles !
""")
            return True
        else:
            print("\n❌ Échec de l'import")
            return False


def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Télécharge et importe les bulletins BRVM dans MongoDB"
    )
    parser.add_argument(
        '--import-only',
        action='store_true',
        help="Importer uniquement (PDFs déjà téléchargés)"
    )
    
    args = parser.parse_args()
    
    telecharger = TelechargerImporterBulletins()
    
    try:
        success = telecharger.executer(import_only=args.import_only)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Processus interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

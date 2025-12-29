"""
TÉLÉCHARGEUR AUTOMATIQUE BULLETINS BRVM
========================================

Télécharge bulletins de cotation BRVM depuis site officiel
URL : https://www.brvm.org/fr/publications/bulletins-cote
"""

import os
import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

def telecharger_bulletins_brvm(nb_jours=60, dossier='bulletins_brvm'):
    """Télécharge derniers bulletins BRVM"""
    
    print("="*70)
    print("TELECHARGEMENT BULLETINS BRVM")
    print("="*70)
    print(f"Objectif : {nb_jours} derniers jours")
    print(f"Dossier : {dossier}")
    print("="*70)
    
    # Créer dossier
    os.makedirs(dossier, exist_ok=True)
    
    # URL base BRVM bulletins
    url_bulletins = "https://www.brvm.org/fr/publications/bulletins-cote"
    
    print(f"\nConnexion : {url_bulletins}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url_bulletins, headers=headers, timeout=30, verify=False)
        
        if response.status_code == 200:
            print("✅ Page chargée")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher liens PDF
            liens_pdf = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'bulletin' in href.lower() and '.pdf' in href.lower():
                    liens_pdf.append(href)
            
            if liens_pdf:
                print(f"✅ {len(liens_pdf)} liens bulletins trouvés")
                
                # Télécharger
                for i, lien in enumerate(liens_pdf[:nb_jours], 1):
                    # URL complète
                    if not lien.startswith('http'):
                        lien = 'https://www.brvm.org' + lien
                    
                    # Nom fichier
                    nom_fichier = os.path.basename(lien)
                    chemin_local = os.path.join(dossier, nom_fichier)
                    
                    # Skip si déjà téléchargé
                    if os.path.exists(chemin_local):
                        print(f"[{i}/{min(nb_jours, len(liens_pdf))}] Deja telecharge : {nom_fichier}")
                        continue
                    
                    print(f"[{i}/{min(nb_jours, len(liens_pdf))}] Telechargement : {nom_fichier}")
                    
                    try:
                        pdf_response = requests.get(lien, headers=headers, timeout=60, verify=False)
                        
                        if pdf_response.status_code == 200:
                            with open(chemin_local, 'wb') as f:
                                f.write(pdf_response.content)
                            print(f"    ✅ Sauvegardé : {len(pdf_response.content)} bytes")
                        else:
                            print(f"    ❌ Erreur {pdf_response.status_code}")
                    
                    except Exception as e:
                        print(f"    ❌ Erreur : {e}")
                    
                    time.sleep(2)  # Délai entre requêtes
                
                print(f"\n✅ Téléchargement terminé")
                return True
            
            else:
                print("❌ Aucun lien bulletin trouvé")
                print("\n💡 SOLUTION MANUELLE :")
                print("   1. Aller sur : https://www.brvm.org/fr/publications/bulletins-cote")
                print(f"   2. Télécharger {nb_jours} derniers bulletins PDF")
                print(f"   3. Placer dans : {dossier}/")
                return False
        
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur connexion : {e}")
        print("\n💡 SOLUTION MANUELLE :")
        print("   1. Aller sur : https://www.brvm.org/fr/publications/bulletins-cote")
        print(f"   2. Télécharger {nb_jours} derniers bulletins PDF")
        print(f"   3. Placer dans : {dossier}/")
        return False


def main():
    """Point d'entrée"""
    import sys
    
    # Désactiver warnings SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    nb_jours = 60
    
    if len(sys.argv) > 1:
        try:
            nb_jours = int(sys.argv[1])
        except:
            pass
    
    success = telecharger_bulletins_brvm(nb_jours)
    
    if success:
        print("\n💡 PROCHAINES ÉTAPES :")
        print("   1. Parser bulletins : python parser_bulletins_brvm.py")
        print("   2. Importer données : python collecter_csv_automatique.py")
        print("   3. Lancer analyse : python trading_adaptatif_demo.py")
        return 0
    else:
        print("\n⚠️  Téléchargement automatique échoué")
        print("Procédure manuelle recommandée")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

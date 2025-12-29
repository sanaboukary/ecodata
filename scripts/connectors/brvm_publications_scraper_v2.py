#!/usr/bin/env python3
"""
📰 SCRAPER PUBLICATIONS BRVM V2 - Optimisé pour extraction de données
Collecte les 3 sources officielles : rapports sociétés, AG, bulletins
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
import time

# Mapping noms société → symboles BRVM
MAPPING_SOCIETES = {
    'air liquide': 'AIRLIQC',
    'bernabe': 'BNBC',
    'bici': 'BICC',
    'boa benin': 'BOAB',
    'boa burkina': 'BOABF',
    'boa cote': 'BOAC',
    'boa mali': 'BOAM',
    'boa niger': 'BOAN',
    'boa senegal': 'BOAS',
    'boa togo': 'BOAT',
    'bolore': 'SDSC',
    'cfao': 'CFAC',
    'cie': 'CIE',
    'ecobank cote': 'ECOC',
    'ecobank': 'ETIT',
    'filtisac': 'FTSC',
    'negoce': 'NEIC',
    'nestle': 'NTLC',
    'onatel': 'ONTBF',
    'orange cote': 'ORGT',
    'palm': 'PALC',
    'palmci': 'PALC',
    'saga': 'ABJC',
    'safca': 'SAFC',
    'sam': 'SIBC',
    'saph': 'SPHC',
    'sbic': 'SBIC',
    'setao': 'STAC',
    'sib': 'SIBC',
    'sicable': 'CABC',
    'sicor': 'SCRC',
    'sitab': 'STAC',
    'smi': 'SMBC',
    'snts': 'SNTS',
    'sogb': 'SOGC',
    'sonatel': 'SNTS',
    'sucrivoire': 'SUCV',
    'total': 'TTLS',
    'tractafric': 'TTLC',
    'uniwax': 'UNXC',
    'vivo': 'SVOC',
    'solibra': 'SLBC',
    'servair': 'SEMC',
    'crown': 'CRON',
    'bernabe': 'BNBC'
}

def extraire_symbole_action(texte: str) -> str:
    """Extrait symbole action depuis nom société"""
    
    if not texte:
        return None
    
    texte_lower = texte.lower()
    
    # Chercher correspondance exacte
    for key, symbole in MAPPING_SOCIETES.items():
        if key in texte_lower:
            return symbole + '.BC'
    
    # Fallback : chercher pattern 4 lettres majuscules
    match = re.search(r'\b([A-Z]{4})\b', texte)
    if match:
        return match.group(1) + '.BC'
    
    return None

def scraper_rapports_societes() -> List[Dict]:
    """Scrape liste sociétés cotées avec rapports"""
    
    url = 'https://www.brvm.org/fr/rapports-societes-cotees'
    
    print(f"🔍 Scraping rapports: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"   ✓ Réponse reçue: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sauvegarder HTML pour debug
        filename = f'brvm_rapports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"   💾 HTML sauvegardé: {filename}")
        
        societes = []
        
        # Chercher toutes les tables
        tables = soup.find_all('table')
        
        for table in tables:
            tbody = table.find('tbody')
            if not tbody:
                continue
            
            rows = tbody.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) >= 2:
                    # Colonne 2 = nom société (avec lien)
                    nom_cell = cols[1] if len(cols) > 1 else cols[0]
                    nom_societe = nom_cell.get_text(strip=True)
                    
                    # Lien vers page société
                    link = nom_cell.find('a', href=True)
                    url_societe = None
                    
                    if link:
                        url_societe = link['href']
                        if not url_societe.startswith('http'):
                            url_societe = 'https://www.brvm.org' + url_societe
                    
                    # Mapper nom → symbole
                    symbole = extraire_symbole_action(nom_societe)
                    
                    if nom_societe and len(nom_societe) > 2:
                        societes.append({
                            'type': 'rapports',
                            'titre': f"Rapports financiers - {nom_societe}",
                            'url_societe': url_societe,
                            'societe': symbole,
                            'nom_societe': nom_societe,
                            'date_publication': None,
                            'type_document': 'RAPPORT_ANNUEL',
                            'source_url': url,
                            'scraped_at': datetime.now().isoformat()
                        })
        
        print(f"   ✓ {len(societes)} société(s) trouvée(s)")
        
        return societes
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []

def scraper_convocations_ag() -> List[Dict]:
    """Scrape convocations assemblées générales"""
    
    url = 'https://www.brvm.org/fr/emetteurs/type-annonces/convocations-assemblees-generales'
    
    print(f"\n🔍 Scraping AG: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"   ✓ Réponse reçue: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sauvegarder HTML
        filename = f'brvm_ag_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"   💾 HTML sauvegardé: {filename}")
        
        convocations = []
        
        # Chercher articles de convocation
        articles = soup.find_all(['article', 'div'], class_=re.compile(r'(node|annonce)', re.I))
        
        for article in articles:
            titre_elem = article.find(['h2', 'h3', 'a'])
            titre = titre_elem.get_text(strip=True) if titre_elem else ''
            
            # Lien complet
            link = titre_elem.find('a', href=True) if titre_elem else None
            url_ag = link['href'] if link else None
            
            if url_ag and not url_ag.startswith('http'):
                url_ag = 'https://www.brvm.org' + url_ag
            
            # Date AG
            date_text = article.get_text()
            match_date = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', date_text)
            date_ag = None
            
            if match_date:
                jour, mois, annee = match_date.groups()
                date_ag = f"{annee}-{mois.zfill(2)}-{jour.zfill(2)}"
            
            # Société
            symbole = extraire_symbole_action(titre)
            
            if titre:
                convocations.append({
                    'type': 'assemblees',
                    'titre': titre,
                    'url_ag': url_ag,
                    'societe': symbole,
                    'date_ag': date_ag,
                    'date_publication': None,
                    'type_document': 'CONVOCATION_AG',
                    'source_url': url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        print(f"   ✓ {len(convocations)} convocation(s) trouvée(s)")
        
        return convocations
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []

def scraper_bulletins_officiels() -> List[Dict]:
    """Scrape bulletins officiels de la cote"""
    
    url = 'https://www.brvm.org/fr/bulletins-officiels-de-la-cote'
    
    print(f"\n🔍 Scraping bulletins: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"   ✓ Réponse reçue: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sauvegarder HTML
        filename = f'brvm_bulletins_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"   💾 HTML sauvegardé: {filename}")
        
        bulletins = []
        
        # Chercher liens PDF
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links:
            titre = link.get_text(strip=True)
            url_pdf = link['href']
            
            if not url_pdf.startswith('http'):
                url_pdf = 'https://www.brvm.org' + url_pdf
            
            # Date bulletin
            match_date = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', titre)
            date_bulletin = None
            
            if match_date:
                jour, mois, annee = match_date.groups()
                date_bulletin = f"{annee}-{mois.zfill(2)}-{jour.zfill(2)}"
            
            if titre:
                bulletins.append({
                    'type': 'bulletins',
                    'titre': titre,
                    'url_pdf': url_pdf,
                    'societe': None,  # Bulletins globaux
                    'date_bulletin': date_bulletin,
                    'date_publication': date_bulletin,
                    'type_document': 'BULLETIN_OFFICIEL',
                    'source_url': url,
                    'scraped_at': datetime.now().isoformat()
                })
        
        print(f"   ✓ {len(bulletins)} bulletin(s) trouvé(s)")
        
        return bulletins
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return []

def main():
    """Collecte toutes les publications BRVM"""
    
    print("\n" + "="*80)
    print("SCRAPER PUBLICATIONS BRVM V2 - OPTIMISÉ")
    print("="*80)
    
    # 1. Rapports sociétés
    rapports = scraper_rapports_societes()
    time.sleep(2)
    
    # 2. Assemblées générales
    assemblees = scraper_convocations_ag()
    time.sleep(2)
    
    # 3. Bulletins officiels
    bulletins = scraper_bulletins_officiels()
    
    # Total
    total = rapports + assemblees + bulletins
    
    print("\n" + "="*80)
    print("RÉSULTATS")
    print("="*80)
    print(f"\nTotal publications: {len(total)}")
    print(f"  rapports: {len(rapports)}")
    print(f"  assemblees: {len(assemblees)}")
    print(f"  bulletins: {len(bulletins)}")
    
    # Échantillon
    print("\n" + "="*80)
    print("ÉCHANTILLON (5 premiers rapports)")
    print("="*80)
    
    for i, pub in enumerate(rapports[:5], 1):
        print(f"\n{i}. {pub['nom_societe']}")
        print(f"   Symbole: {pub['societe']}")
        print(f"   URL: {pub['url_societe']}")
    
    # Sauvegarder JSON
    import json
    filename = f'brvm_publications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(total, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Résultats sauvegardés: {filename}")
    
    return total

if __name__ == '__main__':
    publications = main()

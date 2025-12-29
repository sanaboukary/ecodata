#!/usr/bin/env python3
"""
📄 SCRAPER PUBLICATIONS BRVM OFFICIELLES
Collecte : Rapports annuels, Convocations AG, Bulletins officiels
Source : www.brvm.org
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS = {
    'rapports': 'https://www.brvm.org/fr/rapports-societes-cotees',
    'assemblees': 'https://www.brvm.org/fr/emetteurs/type-annonces/convocations-assemblees-generales',
    'bulletins': 'https://www.brvm.org/fr/bulletins-officiels-de-la-cote'
}

def scraper_publications_brvm(save_html=True):
    """
    Scrape les 3 types de publications BRVM
    Retourne : Liste de publications avec métadonnées
    """
    
    publications = []
    
    for type_pub, url in URLS.items():
        print(f"\n🔍 Scraping {type_pub}: {url}")
        
        try:
            response = requests.get(url, timeout=15, verify=False)
            
            if response.status_code != 200:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                continue
            
            print(f"   ✓ Réponse reçue: {len(response.content)} bytes")
            
            # Sauvegarder HTML pour debug
            if save_html:
                filename = f'brvm_{type_pub}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"   💾 HTML sauvegardé: {filename}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parser selon type
            if type_pub == 'rapports':
                pubs = parser_rapports_societes(soup)
            elif type_pub == 'assemblees':
                pubs = parser_convocations_ag(soup)
            elif type_pub == 'bulletins':
                pubs = parser_bulletins_officiels(soup)
            
            print(f"   ✓ {len(pubs)} publication(s) trouvée(s)")
            
            # Enrichir avec type et URL source
            for pub in pubs:
                pub['type'] = type_pub
                pub['source_url'] = url
                pub['scraped_at'] = datetime.now().isoformat()
            
            publications.extend(pubs)
        
        except Exception as e:
            print(f"   ❌ Erreur scraping {type_pub}: {e}")
    
    return publications

def parser_rapports_societes(soup):
    """Parse rapports annuels des sociétés cotées"""
    
    rapports = []
    
    # Patterns de recherche
    # 1. Liens PDF
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
    
    for link in pdf_links:
        titre = link.get_text(strip=True)
        url_pdf = link.get('href')
        
        # Extraire société et année
        match_societe = re.search(r'(ECOC|BICC|SNTS|[A-Z]{4})', titre, re.I)
        match_annee = re.search(r'20\d{2}', titre)
        
        rapports.append({
            'titre': titre,
            'url_pdf': url_pdf,
            'societe': match_societe.group(1).upper() if match_societe else None,
            'annee': int(match_annee.group(0)) if match_annee else None,
            'date_publication': datetime.now().strftime('%Y-%m-%d')
        })
    
    # 2. Tableaux de publications
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all('td')
            
            if len(cells) >= 3:
                date = cells[0].get_text(strip=True)
                societe = cells[1].get_text(strip=True)
                document = cells[2].get_text(strip=True)
                
                # Chercher lien PDF
                pdf_link = cells[2].find('a', href=re.compile(r'\.pdf$', re.I))
                url_pdf = pdf_link.get('href') if pdf_link else None
                
                rapports.append({
                    'titre': document,
                    'url_pdf': url_pdf,
                    'societe': extraire_symbole_action(societe),
                    'date_publication': parser_date_fr(date),
                    'type_document': classifier_type_document(document)
                })
    
    return rapports

def parser_convocations_ag(soup):
    """Parse convocations assemblées générales"""
    
    convocations = []
    
    # Chercher articles/divs de convocation
    articles = soup.find_all(['article', 'div'], class_=re.compile(r'(node|annonce|convocation)', re.I))
    
    for article in articles:
        titre_elem = article.find(['h2', 'h3', 'a'])
        titre = titre_elem.get_text(strip=True) if titre_elem else ''
        
        # Extraire date AG
        match_date = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', article.get_text())
        
        # Extraire société
        match_societe = re.search(r'(ECOC|BICC|SNTS|[A-Z]{4})', titre, re.I)
        
        # Type AG (ordinaire/extraordinaire)
        type_ag = 'ordinaire' if 'ordinaire' in titre.lower() else 'extraordinaire'
        
        convocations.append({
            'titre': titre,
            'societe': match_societe.group(1).upper() if match_societe else None,
            'date_ag': match_date.group(0) if match_date else None,
            'type_ag': type_ag,
            'date_publication': datetime.now().strftime('%Y-%m-%d'),
            'ordre_du_jour': extraire_ordre_du_jour(article)
        })
    
    return convocations

def parser_bulletins_officiels(soup):
    """Parse bulletins officiels de la cote"""
    
    bulletins = []
    
    # Chercher liens bulletins quotidiens
    bulletin_links = soup.find_all('a', href=re.compile(r'(bulletin|cote)', re.I))
    
    for link in bulletin_links:
        titre = link.get_text(strip=True)
        url = link.get('href')
        
        # Extraire date
        match_date = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', titre)
        
        bulletins.append({
            'titre': titre,
            'url_pdf': url,
            'date_bulletin': parser_date_fr(match_date.group(0)) if match_date else None,
            'date_publication': datetime.now().strftime('%Y-%m-%d')
        })
    
    return bulletins

def extraire_symbole_action(texte):
    """Extrait symbole action (ex: ECOC.BC) depuis texte"""
    
    match = re.search(r'([A-Z]{4}(?:\.BC)?)', texte, re.I)
    
    if match:
        symbole = match.group(1).upper()
        if not symbole.endswith('.BC'):
            symbole += '.BC'
        return symbole
    
    return None

def classifier_type_document(titre):
    """Classifie type de document financier"""
    
    titre_lower = titre.lower()
    
    if 'rapport annuel' in titre_lower or 'annual report' in titre_lower:
        return 'RAPPORT_ANNUEL'
    elif 'résultats' in titre_lower or 'results' in titre_lower:
        return 'RESULTATS_FINANCIERS'
    elif 'dividende' in titre_lower or 'dividend' in titre_lower:
        return 'DIVIDENDE'
    elif 'communiqué' in titre_lower or 'press release' in titre_lower:
        return 'COMMUNIQUE'
    else:
        return 'AUTRE'

def extraire_ordre_du_jour(article_soup):
    """Extrait ordre du jour d'une AG"""
    
    texte = article_soup.get_text()
    
    # Chercher section "Ordre du jour"
    match = re.search(r'ordre du jour[:\s]+(.*?)(?:fin|---|$)', texte, re.I | re.DOTALL)
    
    if match:
        return match.group(1).strip()[:500]  # Limiter à 500 chars
    
    return None

def parser_date_fr(date_str):
    """Parse date française (JJ/MM/AAAA ou JJ-MM-AAAA)"""
    
    if not date_str:
        return None
    
    try:
        # Essayer JJ/MM/AAAA
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', date_str)
        
        if match:
            jour, mois, annee = match.groups()
            return f"{annee}-{mois.zfill(2)}-{jour.zfill(2)}"
    except:
        pass
    
    return None

def telecharger_pdf(url, filename=None):
    """Télécharge un PDF depuis URL"""
    
    try:
        if not url.startswith('http'):
            url = f"https://www.brvm.org{url}"
        
        response = requests.get(url, timeout=30, verify=False)
        
        if response.status_code == 200:
            if not filename:
                filename = url.split('/')[-1]
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✓ PDF téléchargé: {filename} ({len(response.content)} bytes)")
            return filename
        
    except Exception as e:
        print(f"   ❌ Erreur téléchargement PDF: {e}")
    
    return None

if __name__ == '__main__':
    print("=" * 80)
    print("SCRAPER PUBLICATIONS BRVM OFFICIELLES")
    print("=" * 80)
    
    publications = scraper_publications_brvm(save_html=True)
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS")
    print(f"{'='*80}")
    print(f"\nTotal publications: {len(publications)}")
    
    # Grouper par type
    from collections import Counter
    types = Counter(p['type'] for p in publications)
    
    for type_pub, count in types.items():
        print(f"  {type_pub}: {count}")
    
    # Afficher échantillon
    if publications:
        print(f"\n{'='*80}")
        print(f"ÉCHANTILLON (5 premiers)")
        print(f"{'='*80}\n")
        
        for i, pub in enumerate(publications[:5], 1):
            print(f"{i}. [{pub['type'].upper()}] {pub['titre']}")
            print(f"   Société: {pub.get('societe', 'N/A')}")
            print(f"   Date: {pub.get('date_publication', 'N/A')}")
            if pub.get('url_pdf'):
                print(f"   PDF: {pub['url_pdf']}")
            print()

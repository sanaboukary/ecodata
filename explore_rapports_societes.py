#!/usr/bin/env python3
"""Exploration de la structure des rapports sociétés BRVM"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/rapports-societes-cotees"

print("="*80)
print("EXPLORATION: Rapports Sociétés Cotées BRVM")
print("="*80)

try:
    response = requests.get(url, verify=False, timeout=30)
    print(f"\n✅ Statut: {response.status_code}")
    print(f"✅ Taille: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. Chercher les tableaux
    print("\n" + "="*80)
    print("TABLEAUX")
    print("="*80)
    tables = soup.find_all('table')
    print(f"Nombre de tableaux: {len(tables)}")
    
    if tables:
        main_table = tables[0]
        headers = [th.get_text(strip=True) for th in main_table.find_all('th')]
        print(f"Colonnes: {headers}")
        
        rows = main_table.find_all('tr')[1:]  # Skip header
        print(f"Nombre de lignes: {len(rows)}")
        
        print("\n📊 Exemples de rapports (5 premiers):")
        for i, row in enumerate(rows[:5], 1):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                code = cells[0].get_text(strip=True)
                emetteur = cells[1].get_text(strip=True)
                description = cells[2].get_text(strip=True)
                
                # Chercher le lien
                link = row.find('a', href=True)
                if link:
                    href = link.get('href')
                    print(f"\n{i}. Code: {code}")
                    print(f"   Emetteur: {emetteur}")
                    print(f"   Description: {description}")
                    print(f"   Lien: {href}")
    
    # 2. Chercher tous les liens vers des rapports
    print("\n" + "="*80)
    print("LIENS VERS RAPPORTS")
    print("="*80)
    
    # Pattern pour rapports (PDF généralement)
    all_links = soup.find_all('a', href=True)
    rapport_links = []
    
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Identifier les liens de rapports
        if any(keyword in href.lower() for keyword in ['rapport', 'report', 'pdf', 'document']):
            rapport_links.append((text, href))
    
    print(f"Liens vers rapports trouvés: {len(rapport_links)}")
    
    if rapport_links:
        print("\n📄 Exemples:")
        for i, (text, href) in enumerate(rapport_links[:10], 1):
            print(f"  {i}. {text[:60]} | {href[:80]}")
    
    # 3. Chercher les filtres/secteurs
    print("\n" + "="*80)
    print("FILTRES/SECTEURS")
    print("="*80)
    
    buttons = soup.find_all('button')
    links_filter = soup.find_all('a', class_=re.compile('filter|btn|sector', re.I))
    
    print(f"Boutons: {len(buttons)}")
    print(f"Liens de filtrage: {len(links_filter)}")
    
    # Chercher les catégories de secteurs
    secteurs = []
    for elem in soup.find_all(['button', 'a']):
        text = elem.get_text(strip=True)
        if any(keyword in text.upper() for keyword in ['CONSOMMATION', 'ENERGIE', 'INDUSTRIEL', 'FINANCIER', 'TELECOMMUNICATION', 'SERVICES']):
            secteurs.append(text)
    
    if secteurs:
        print("\n📂 Secteurs identifiés:")
        for i, secteur in enumerate(set(secteurs), 1):
            print(f"  {i}. {secteur}")
    
    # 4. Structure des données
    print("\n" + "="*80)
    print("STRUCTURE DES DONNÉES")
    print("="*80)
    
    # Chercher les divs/sections principales
    main_content = soup.find('div', class_=re.compile('content|main|rapports', re.I))
    if main_content:
        print("✅ Conteneur principal trouvé")
    
    # Chercher les classes spécifiques
    all_classes = set()
    for elem in soup.find_all(class_=True):
        if isinstance(elem.get('class'), list):
            all_classes.update(elem.get('class'))
    
    relevant_classes = [c for c in all_classes if any(k in c.lower() for k in ['rapport', 'table', 'row', 'company', 'society'])]
    
    if relevant_classes:
        print(f"\n🎯 Classes CSS pertinentes: {relevant_classes[:10]}")

except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

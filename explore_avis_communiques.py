#!/usr/bin/env python3
"""Exploration structure Avis et Communiqués BRVM"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/avis-et-communiques"

print("="*80)
print("EXPLORATION: Avis et Communiqués BRVM")
print("="*80)

try:
    response = requests.get(url, verify=False, timeout=30)
    print(f"\n✅ Statut: {response.status_code}")
    print(f"✅ Taille: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. Structure principale
    print("\n" + "="*80)
    print("STRUCTURE PRINCIPALE")
    print("="*80)
    
    # Chercher conteneur principal
    main_content = soup.find('div', class_=re.compile('view-content|main-content|region-content'))
    if main_content:
        print(f"✅ Conteneur principal trouvé: {main_content.get('class')}")
    
    # 2. Liste des avis
    print("\n" + "="*80)
    print("LISTE DES AVIS")
    print("="*80)
    
    # Chercher les items
    items = soup.find_all(['div', 'article', 'tr'], class_=re.compile('views-row|item|avis|node'))
    print(f"Items potentiels trouvés: {len(items)}")
    
    # Chercher dans un tableau
    table = soup.find('table')
    if table:
        print("\n✅ Tableau trouvé")
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        print(f"Colonnes: {headers}")
        
        rows = table.find_all('tr')[1:11]  # 10 premières lignes
        print(f"\n📋 {len(rows)} premières lignes:\n")
        
        for i, row in enumerate(rows, 1):
            cells = row.find_all(['td', 'th'])
            if cells:
                texts = [cell.get_text(strip=True) for cell in cells]
                link = row.find('a', href=True)
                print(f"{i}. {' | '.join(texts[:3])}")
                if link:
                    print(f"   🔗 {link.get('href')}")
    else:
        # Structure liste/cards
        print("\n❌ Pas de tableau, recherche structure liste...")
        
        articles = soup.find_all(['article', 'div'], class_=re.compile('node|item|avis'))
        print(f"Articles/divs trouvés: {len(articles)}")
        
        for i, article in enumerate(articles[:5], 1):
            title = article.find(['h2', 'h3', 'h4', 'a'])
            if title:
                print(f"\n{i}. {title.get_text(strip=True)}")
                
                date = article.find(['time', 'span'], class_=re.compile('date'))
                if date:
                    print(f"   📅 {date.get_text(strip=True)}")
                
                link = article.find('a', href=True)
                if link:
                    print(f"   🔗 {link.get('href')}")
    
    # 3. Chercher tous les liens vers PDF/documents
    print("\n" + "="*80)
    print("LIENS VERS DOCUMENTS")
    print("="*80)
    
    pdf_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
    print(f"Documents trouvés: {len(pdf_links)}")
    
    for i, link in enumerate(pdf_links[:10], 1):
        href = link.get('href')
        text = link.get_text(strip=True)
        print(f"{i}. {text[:60]} | {href}")
    
    # 4. Tous les liens (pour pattern)
    print("\n" + "="*80)
    print("PATTERN DES LIENS")
    print("="*80)
    
    all_links = soup.find_all('a', href=True)
    avis_links = [l for l in all_links if 'avis' in l.get('href', '').lower() or 'communique' in l.get('href', '').lower()]
    
    print(f"Liens contenant 'avis' ou 'communique': {len(avis_links)}")
    
    if avis_links:
        print("\n📄 Exemples:")
        for i, link in enumerate(avis_links[:10], 1):
            href = link.get('href')
            text = link.get_text(strip=True)[:60]
            print(f"{i}. {text} | {href}")
    
    # 5. Classes CSS pertinentes
    print("\n" + "="*80)
    print("CLASSES CSS PERTINENTES")
    print("="*80)
    
    all_classes = set()
    for elem in soup.find_all(class_=True):
        if isinstance(elem.get('class'), list):
            all_classes.update(elem.get('class'))
    
    relevant = [c for c in all_classes if any(k in c.lower() for k in ['avis', 'communique', 'view', 'item', 'row', 'node'])]
    print(f"Classes pertinentes: {sorted(relevant)[:15]}")

except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

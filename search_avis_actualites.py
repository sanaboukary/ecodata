#!/usr/bin/env python3
"""Recherche des avis dans les actualités"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/actualites"

print("="*80)
print("RECHERCHE AVIS DANS ACTUALITÉS")
print("="*80)

response = requests.get(url, verify=False, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

print(f"✅ Status: {response.status_code}")

# Chercher les articles
print("\n" + "="*80)
print("ARTICLES TROUVÉS")
print("="*80)

articles = soup.find_all(['article', 'div'], class_=re.compile('node|item|views-row'))
print(f"Total articles: {len(articles)}")

# Filtrer ceux qui mentionnent des avis
avis_articles = []
for article in articles[:30]:  # Analyser les 30 premiers
    text = article.get_text().lower()
    title_tag = article.find(['h2', 'h3', 'a'])
    
    if title_tag:
        title = title_tag.get_text(strip=True)
        
        # Chercher mots-clés d'avis
        keywords = ['avis', 'suspension', 'dividende', 'assemblée', 'convocation', 
                   'capital', 'communiqué', 'cotation', 'ag ', 'ago', 'age']
        
        if any(kw in text for kw in keywords):
            link = article.find('a', href=True)
            date = article.find(['time', 'span'], class_=re.compile('date'))
            
            avis_articles.append({
                'title': title,
                'link': link.get('href') if link else None,
                'date': date.get_text(strip=True) if date else 'N/A',
                'matched_keywords': [kw for kw in keywords if kw in text]
            })

print(f"\n📋 Articles avec mots-clés 'avis': {len(avis_articles)}")

if avis_articles:
    print("\nExemples:")
    for i, art in enumerate(avis_articles[:10], 1):
        print(f"\n{i}. {art['title']}")
        print(f"   📅 {art['date']}")
        print(f"   🔑 Mots-clés: {', '.join(art['matched_keywords'][:3])}")
        if art['link']:
            full_link = art['link'] if art['link'].startswith('http') else f"https://www.brvm.org{art['link']}"
            print(f"   🔗 {full_link}")

# Chercher aussi des PDFs dans les actualités
print("\n" + "="*80)
print("PDFs DANS ACTUALITÉS")
print("="*80)

pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
print(f"PDFs trouvés: {len(pdf_links)}")

for i, link in enumerate(pdf_links[:10], 1):
    href = link.get('href')
    text = link.get_text(strip=True) or 'PDF'
    
    if not href.startswith('http'):
        href = f"https://www.brvm.org{href}"
    
    print(f"{i}. {text[:60]} → {href}")

"""Explorer la structure HTML du site BRVM pour trouver les publications"""
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

url = "https://www.brvm.org/fr/bulletins-officiels-de-la-cote"

print("="*80)
print(f"EXPLORATION DU SITE: {url}")
print("="*80)

try:
    response = requests.get(url, timeout=30, verify=False, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print(f"\n✅ Statut: {response.status_code}")
    print(f"✅ Taille: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("\n" + "="*80)
    print("STRUCTURE HTML:")
    print("="*80)
    
    # Chercher les tableaux
    tables = soup.find_all('table')
    print(f"\n📊 Tableaux trouvés: {len(tables)}")
    for i, table in enumerate(tables[:3], 1):
        print(f"\n  Table {i}:")
        rows = table.find_all('tr')[:3]
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if cells:
                print(f"    - {' | '.join([c.get_text(strip=True)[:50] for c in cells[:3]])}")
    
    # Chercher les liens PDF
    pdf_links = soup.find_all('a', href=lambda x: x and ('.pdf' in x.lower() or 'download' in x.lower()))
    print(f"\n📄 Liens PDF/Download trouvés: {len(pdf_links)}")
    for link in pdf_links[:5]:
        print(f"    - {link.get('href', '')[:60]} | {link.get_text(strip=True)[:40]}")
    
    # Chercher les articles/divs
    articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x or 'post' in x or 'item' in x or 'card' in x))
    print(f"\n📰 Articles/Cards trouvés: {len(articles)}")
    for article in articles[:3]:
        title = article.find(['h1', 'h2', 'h3', 'h4'])
        if title:
            print(f"    - {title.get_text(strip=True)[:60]}")
    
    # Chercher toutes les classes CSS utilisées
    all_classes = set()
    for tag in soup.find_all(class_=True):
        if isinstance(tag['class'], list):
            all_classes.update(tag['class'])
        else:
            all_classes.add(tag['class'])
    
    print(f"\n🎨 Classes CSS trouvées: {len(all_classes)}")
    relevant_classes = [c for c in all_classes if any(word in c.lower() for word in ['table', 'row', 'item', 'post', 'article', 'bulletin', 'publication', 'document'])]
    if relevant_classes:
        print("  Classes pertinentes:")
        for cls in sorted(relevant_classes)[:10]:
            print(f"    - {cls}")
    
    # Chercher les divs avec des IDs pertinents
    relevant_ids = soup.find_all(id=lambda x: x and any(word in x.lower() for word in ['content', 'main', 'publication', 'bulletin', 'document']))
    print(f"\n🆔 IDs pertinents trouvés: {len(relevant_ids)}")
    for elem in relevant_ids[:5]:
        print(f"    - ID: {elem.get('id')} | Tag: {elem.name}")
    
    print("\n" + "="*80)
    print("SNIPPET HTML (premiers 2000 caractères du contenu principal):")
    print("="*80)
    
    # Chercher le contenu principal
    main_content = soup.find(['main', 'div'], {'id': lambda x: x and 'content' in x.lower()})
    if not main_content:
        main_content = soup.find('body')
    
    if main_content:
        text = str(main_content)[:2000]
        print(text)
    
except Exception as e:
    print(f"❌ Erreur: {e}")

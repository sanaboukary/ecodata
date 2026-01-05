#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parser Bulletins PDF BRVM - Source officielle GARANTIE
Les bulletins quotidiens contiennent TOUTES les 47 actions avec TOUTES les données
"""

import sys
import io
import re
import os
from datetime import datetime
import pandas as pd

# Fix encodage
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pymongo import MongoClient

def log(msg, level='INFO'):
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbols.get(level, 'ℹ️')} {msg}")

def parse_french_number(x):
    """Parse nombre français."""
    if not x or x == '-':
        return None
    s = str(x).strip().replace('\xa0', ' ').replace(' ', '').replace(',', '.')
    try:
        return float(re.match(r'-?\d*\.?\d+', s).group())
    except:
        return None

def telecharger_bulletin_brvm(date_str=None):
    """Télécharge le bulletin quotidien BRVM."""
    import requests
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # URLs possibles pour bulletins BRVM
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    urls_bulletins = [
        f"https://www.brvm.org/sites/default/files/bulletin/bulletin_{date_obj.strftime('%Y%m%d')}.pdf",
        f"https://www.brvm.org/sites/default/files/quotidien/quotidien_{date_obj.strftime('%Y%m%d')}.pdf",
        f"https://www.brvm.org/fr/content/bulletin-quotidien-{date_obj.strftime('%d-%m-%Y')}",
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    for url in urls_bulletins:
        try:
            log(f"Tentative téléchargement: {url}")
            r = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if r.status_code == 200 and len(r.content) > 1000:
                # Sauvegarder PDF
                os.makedirs('bulletins_brvm', exist_ok=True)
                pdf_path = f"bulletins_brvm/bulletin_{date_obj.strftime('%Y%m%d')}.pdf"
                
                with open(pdf_path, 'wb') as f:
                    f.write(r.content)
                
                log(f"✅ Bulletin téléchargé: {pdf_path}", 'SUCCESS')
                return pdf_path
                
        except Exception as e:
            log(f"Erreur: {str(e)[:50]}", 'WARNING')
    
    return None

def parser_bulletin_pdf(pdf_path):
    """Parse le bulletin PDF BRVM pour extraire les données."""
    
    try:
        import PyPDF2
        
        log(f"Parsing PDF: {pdf_path}")
        
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Extraire tout le texte
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
        
        log(f"Texte extrait: {len(full_text)} caractères")
        
        # Parser les données action par ligne
        actions_data = []
        
        # Pattern pour lignes d'actions: TICKER LIBELLE COURS VARIATION VOLUME ...
        pattern = r'([A-Z]{3,6})\s+([^\d]+?)\s+(\d+[\s,]\d+|\d+)\s+([-+]?\d+[,.]?\d*)\s+(\d+[\s,]?\d*)'
        
        matches = re.finditer(pattern, full_text)
        
        for match in matches:
            ticker = match.group(1).strip()
            libelle = match.group(2).strip()
            cours = parse_french_number(match.group(3))
            variation = parse_french_number(match.group(4))
            volume = parse_french_number(match.group(5))
            
            if cours and cours > 10:  # Vraisemblable
                actions_data.append({
                    'Ticker': ticker,
                    'Libelle': libelle,
                    'Cours': cours,
                    'Variation_%': variation,
                    'Volume': volume
                })
        
        if actions_data:
            log(f"✅ {len(actions_data)} actions extraites", 'SUCCESS')
            return pd.DataFrame(actions_data)
        
    except ImportError:
        log("❌ PyPDF2 non installé: pip install PyPDF2", 'ERROR')
    except Exception as e:
        log(f"Erreur parsing: {e}", 'ERROR')
    
    return pd.DataFrame()

def parser_bulletin_local():
    """Parse les bulletins PDF locaux déjà téléchargés."""
    import glob
    
    pdf_files = glob.glob('bulletins_brvm/*.pdf')
    
    if not pdf_files:
        log("❌ Aucun bulletin PDF trouvé dans bulletins_brvm/", 'ERROR')
        return pd.DataFrame()
    
    log(f"📂 {len(pdf_files)} bulletin(s) trouvé(s)")
    
    # Utiliser le plus récent
    latest_pdf = max(pdf_files, key=os.path.getctime)
    log(f"Utilisation: {latest_pdf}")
    
    return parser_bulletin_pdf(latest_pdf)

def main():
    print("=" * 100)
    print("📄 PARSER BULLETINS PDF BRVM - Source Officielle")
    print("=" * 100)
    print()
    print("Les bulletins quotidiens BRVM contiennent les 47 actions avec TOUTES les données")
    print("Source: https://www.brvm.org/fr/investir/publications/bulletins-quotidiens")
    print()
    print("=" * 100)
    print()
    
    # Option 1: Télécharger bulletin du jour
    log("Option 1: Téléchargement automatique...")
    pdf_path = telecharger_bulletin_brvm()
    
    if pdf_path:
        df = parser_bulletin_pdf(pdf_path)
    else:
        # Option 2: Parser bulletins locaux
        log("Option 2: Parser bulletins locaux...")
        df = parser_bulletin_local()
    
    if df.empty:
        print()
        print("=" * 100)
        log("❌ Échec automatique", 'ERROR')
        print("=" * 100)
        print()
        print("📋 SOLUTION MANUELLE:")
        print()
        print("1. Télécharger le bulletin quotidien BRVM:")
        print("   https://www.brvm.org/fr/investir/publications/bulletins-quotidiens")
        print()
        print("2. Sauvegarder dans: bulletins_brvm/bulletin_YYYYMMDD.pdf")
        print()
        print("3. Relancer ce script:")
        print("   python parser_bulletin_brvm.py")
        print()
        print("OU installer PyPDF2:")
        print("   pip install PyPDF2")
        print()
        return 1
    
    # MongoDB
    log("Connexion MongoDB...")
    client = MongoClient('mongodb://localhost:27017')
    db = client['centralisation_db']
    
    # Sauvegarder
    date_str = datetime.now().strftime('%Y-%m-%d')
    saved = 0
    
    for _, row in df.iterrows():
        ticker = row.get('Ticker')
        cours = row.get('Cours')
        
        if pd.notna(ticker) and pd.notna(cours):
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': str(ticker),
                'ts': date_str,
                'value': float(cours),
                'attrs': {
                    'data_quality': 'REAL_SCRAPER',
                    'source_type': 'Bulletin_PDF_Officiel',
                    'libelle': str(row.get('Libelle', '')),
                    'variation_pct': float(row['Variation_%']) if pd.notna(row.get('Variation_%')) else None,
                    'volume': float(row['Volume']) if pd.notna(row.get('Volume')) else None,
                }
            }
            
            db.curated_observations.update_one(
                {'source': 'BRVM', 'key': ticker, 'ts': date_str},
                {'$set': obs},
                upsert=True
            )
            saved += 1
    
    # Export CSV
    os.makedirs('out_brvm', exist_ok=True)
    csv_path = f"out_brvm/brvm_bulletin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 100)
    log(f"✅ SUCCÈS: {saved} actions collectées", 'SUCCESS')
    print("=" * 100)
    print()
    log(f"MongoDB: {saved} observations", 'SUCCESS')
    log(f"CSV: {csv_path}", 'SUCCESS')
    print()
    print("📊 DONNÉES:")
    print(df.to_string(index=False))
    print()
    print("=" * 100)
    
    client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())

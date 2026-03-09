#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTEUR DE TEXTE DES PDFs BRVM
Lit les bulletins officiels et extrait le texte pour l'analyse sémantique
"""

import os
import sys
import requests
from pymongo import MongoClient
from datetime import datetime
import tempfile
import hashlib

# Pour extraire le texte des PDFs
try:
    import PyPDF2
except ImportError:
    print("❌ PyPDF2 non installé. Installation:")
    print("   pip install PyPDF2")
    sys.exit(1)

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

def telecharger_pdf(url):
    """Télécharge un PDF et retourne le chemin temporaire"""
    try:
        response = requests.get(url, timeout=30, verify=False)
        if response.status_code == 200:
            # Créer un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file.close()
            return temp_file.name
    except Exception as e:
        print(f"   ❌ Erreur téléchargement: {e}")
    return None

def extraire_texte_pdf(pdf_path):
    """Extrait le texte d'un PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            texte = ""
            
            # Lire toutes les pages (max 50 pour éviter les trop gros PDFs)
            for page_num in range(min(len(reader.pages), 50)):
                page = reader.pages[page_num]
                texte += page.extract_text() + "\n"
            
            return texte.strip()
    except Exception as e:
        print(f"   ❌ Erreur extraction: {e}")
    return ""

def main():
    print("="*80)
    print("EXTRACTION TEXTE PDFs BRVM")
    print("="*80)
    
    # Récupérer les publications BRVM sans contenu
    query = {
        'source': 'BRVM_PUBLICATION',
        '$or': [
            {'attrs.contenu': {'$exists': False}},
            {'attrs.contenu': ''},
            {'attrs.contenu': None}
        ]
    }
    
    publications = list(db.curated_observations.find(query))
    print(f"\n{len(publications)} publications BRVM sans texte")
    
    if len(publications) == 0:
        print("✅ Toutes les publications ont déjà du texte!")
        return
    
    # Limiter à 20 pour le test
    publications = publications[:20]
    print(f"Traitement de {len(publications)} publications (test)...\n")
    
    success = 0
    errors = 0
    
    for i, pub in enumerate(publications, 1):
        attrs = pub.get('attrs', {})
        url = attrs.get('url', '')
        titre = attrs.get('title', attrs.get('titre', 'Sans titre'))
        
        print(f"{i}/{len(publications)} | {titre[:60]}...")
        
        if not url:
            print("   ⚠️  Pas d'URL")
            errors += 1
            continue
        
        # Télécharger le PDF
        pdf_path = telecharger_pdf(url)
        if not pdf_path:
            print("   ❌ Téléchargement échoué")
            errors += 1
            continue
        
        # Extraire le texte
        texte = extraire_texte_pdf(pdf_path)
        
        # Nettoyer le fichier temporaire
        try:
            os.unlink(pdf_path)
        except:
            pass
        
        if not texte or len(texte) < 50:
            print(f"   ⚠️  Texte vide ou trop court ({len(texte)} chars)")
            errors += 1
            continue
        
        # Mettre à jour MongoDB
        db.curated_observations.update_one(
            {'_id': pub['_id']},
            {'$set': {
                'attrs.contenu': texte[:50000],  # Limiter à 50k chars
                'attrs.text_extracted_at': datetime.now().isoformat(),
                'attrs.text_length': len(texte)
            }}
        )
        
        print(f"   ✅ {len(texte)} caractères extraits")
        success += 1
    
    print("\n" + "="*80)
    print(f"RÉSULTATS:")
    print(f"  ✅ Succès: {success}")
    print(f"  ❌ Erreurs: {errors}")
    print("="*80)
    
    if success > 0:
        print("\n🎯 PROCHAINE ÉTAPE:")
        print("   python analyse_semantique_brvm_v3.py")
        print("   Puis: python pipeline_brvm.py")

if __name__ == "__main__":
    main()

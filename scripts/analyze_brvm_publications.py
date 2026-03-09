import os
import fitz  # PyMuPDF
from plateforme_centralisation.mongo import get_mongo_db

PDF_DIR = os.path.join(os.path.dirname(__file__), '../../media/brvm_publications')

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        print(f"Erreur extraction PDF {pdf_path}: {e}")
        return ""

def enrich_publications_with_text():
    _, db = get_mongo_db()
    publications = list(db.brvm_publications.find({}))
    for pub in publications:
        local_path = pub.get('local_path')
        if not local_path or not os.path.exists(local_path):
            continue
        # Ne pas retraiter si déjà extrait
        if pub.get('text_extracted'):
            continue
        text = extract_text_from_pdf(local_path)
        db.brvm_publications.update_one({'_id': pub['_id']}, {'$set': {'text_content': text, 'text_extracted': True}})
        print(f"Texte extrait pour {pub.get('filename')}")

if __name__ == "__main__":
    enrich_publications_with_text()

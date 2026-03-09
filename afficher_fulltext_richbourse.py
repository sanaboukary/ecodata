#!/usr/bin/env python3
"""
Affiche le texte intégral extrait pour une publication RichBourse donnée (par URL)
"""
from plateforme_centralisation.mongo import get_mongo_db

def main():
    url = "https://www.richbourse.com/common/apprendre/article/resume_semaine_26_01_au_30_01_2026_1769787002"
    _, db = get_mongo_db()
    doc = db.curated_observations.find_one({"url": url})
    if not doc:
        print("Aucune publication trouvée pour cette URL.")
        return
    full_text = doc.get("attrs", {}).get("full_text")
    if not full_text:
        print("Aucun texte intégral extrait pour cette publication.")
        return
    print("\nTEXTE INTÉGRAL EXTRAIT :\n" + "="*60)
    print(full_text)

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

BASE_URL = "https://www.brvm.org/fr/titres/{}"

def _clean_number(text: str) -> Optional[float]:
    """
    Nettoie un nombre BRVM (espaces, FCFA, virgules)
    """
    if not text:
        return None
    text = text.replace("FCFA", "").replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None

def enrichir_action_brvm(symbole: str, session: requests.Session = None) -> Dict:
    """
    Enrichit une action BRVM via sa page détail
    https://www.brvm.org/fr/titres/<SYMBOL>
    """
    url = BASE_URL.format(symbole.upper())

    session = session or requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "fr-FR,fr;q=0.9"
    })

    result = {
        "capitalisation": None,
        "nombre_titres": None,
        "flottant_pct": None,
        "secteur_officiel": None,
        "historique_disponible": False
    }

    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ============================
        # TABLE DES INFORMATIONS CLÉS
        # ============================
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                if len(cells) != 2:
                    continue

                label, value = cells

                label_lower = label.lower()

                if "capitalisation" in label_lower:
                    result["capitalisation"] = _clean_number(value)

                elif "nombre de titres" in label_lower:
                    result["nombre_titres"] = _clean_number(value)

                elif "flottant" in label_lower:
                    result["flottant_pct"] = _clean_number(
                        re.sub(r"[^\d,\.]", "", value)
                    )

                elif "secteur" in label_lower:
                    result["secteur_officiel"] = value

        # ============================
        # DÉTECTION HISTORIQUE
        # ============================
        if soup.find("table", class_=re.compile("historique", re.I)):
            result["historique_disponible"] = True

        # Certaines pages ont un onglet "Historique"
        for link in soup.find_all("a"):
            if "historique" in link.get_text(strip=True).lower():
                result["historique_disponible"] = True

        return result

    except Exception as e:
        result["error"] = str(e)
        return result

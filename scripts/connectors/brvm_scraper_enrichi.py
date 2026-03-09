print("[TRACE] Script brvm_scraper_enrichi.py lancé.")
"""
SCRAPER BRVM ENRICHI - DONNÉES COMPLÈTES + INDICATEURS AVANCÉS
🎯 Collecte: Cours, Variations, Volatilité, Liquidité, Ratios Financiers, Indicateurs Techniques

MÉTRIQUES COLLECTÉES (70+ attributs):
1. Prix OHLCV (Open, High, Low, Close, Volume)
2. Variations (jour, semaine, mois, année, YTD)
3. Volatilité (écart-type, beta, ATR)
4. Liquidité (volume moyen, taux rotation, spread)
5. Valorisation (PE, PB, EPS, market cap)
6. Dividendes (yield, payout, ex-date)
7. Analyse technique (SMA, RSI, MACD, Bollinger)
8. Fondamentaux (ROE, ROA, debt/equity, ratios)
9. Recommandations (consensus, target price)
10. Scores qualité (liquidité, croissance, dividende)
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
import sys
import math
import statistics

# Ajouter le répertoire parent pour importer brvm_stocks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connectors.brvm_stocks import BRVM_STOCKS, get_all_symbols

def calculer_volatilite(prix_historiques):
    """Calcule la volatilité (écart-type) des prix"""
    if len(prix_historiques) < 2:
        return 0.0
    
    rendements = []
    for i in range(1, len(prix_historiques)):
        rendement = (prix_historiques[i] - prix_historiques[i-1]) / prix_historiques[i-1]
        rendements.append(rendement)
    
    return statistics.stdev(rendements) * math.sqrt(252) * 100  # Volatilité annualisée en %

def calculer_beta(prix_action, prix_marche):
    """Calcule le beta (volatilité relative au marché)"""
    if len(prix_action) < 2 or len(prix_marche) < 2:
        return 1.0
    
    def scraper_brvm_html_enrichi():
        print("[TRACE] scraper_brvm_html_enrichi lancé")
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        import math, statistics
        try:
            url = "https://www.brvm.org/fr/emetteurs/societes-cotees"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            }
            print("🔄 Envoi requête HTTP...")
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            print(f"✅ Réponse HTTP {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')
            if not table:
                print("❌ Aucune table trouvée sur la page. Structure HTML à adapter.")
                return []
            data_scrapees = []
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if not cells or len(cells) < 3:
                    continue
                try:
                    text_cells = [cell.get_text(strip=True) for cell in cells]
                    symbol = text_cells[0]
                    prix_str = text_cells[1].replace(' ', '').replace(',', '').replace('FCFA', '')
                    close = float(prix_str) if prix_str else 0.0
                    variation_str = text_cells[2].replace('%', '').replace('+', '').strip()
                    variation = float(variation_str) if variation_str and variation_str != '-' else 0.0
                    volume = 0
                    for cell in text_cells[3:]:
                        cell_clean = cell.replace(' ', '').replace(',', '')
                        if cell_clean.isdigit() and len(cell_clean) >= 3:
                            volume = int(cell_clean)
                            break
                    data_scrapees.append({
                        'symbol': symbol,
                        'close': close,
                        'variation': variation,
                        'volume': volume
                    })
                except Exception as e:
                    continue
            if not data_scrapees:
                print("❌ Aucune donnée scrapée - Vérifier la structure HTML")
                return []
            print(f"✅ {len(data_scrapees)} actions scrapées avec succès")
            # Exemple affichage
            print("\nEXEMPLE D'UNE ACTION :")
            import pprint
            pprint.pprint(data_scrapees[0], width=120, compact=False)
            return data_scrapees
        except Exception as e:
            print(f"[ERREUR] {e}")
            return []
                
    def main():
        print("[TRACE] main() lancé")

        def scraper_brvm_html_enrichi():
            print("[TRACE] scraper_brvm_html_enrichi lancé")
            import requests
            from bs4 import BeautifulSoup
            try:
                url = "https://www.brvm.org/fr/emetteurs/societes-cotees"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                }
                print("🔄 Envoi requête HTTP...")
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response.raise_for_status()
                print(f"✅ Réponse HTTP {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table')
                if not table:
                    print("❌ Aucune table trouvée sur la page. Structure HTML à adapter.")
                    return []
                data_scrapees = []
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if not cells or len(cells) < 3:
                        continue
                    try:
                        text_cells = [cell.get_text(strip=True) for cell in cells]
                        symbol = text_cells[0]
                        prix_str = text_cells[1].replace(' ', '').replace(',', '').replace('FCFA', '')
                        close = float(prix_str) if prix_str else 0.0
                        variation_str = text_cells[2].replace('%', '').replace('+', '').strip()
                        variation = float(variation_str) if variation_str and variation_str != '-' else 0.0
                        volume = 0
                        for cell in text_cells[3:]:
                            cell_clean = cell.replace(' ', '').replace(',', '')
                            if cell_clean.isdigit() and len(cell_clean) >= 3:
                                volume = int(cell_clean)
                                break
                        data_scrapees.append({
                            'symbol': symbol,
                            'close': close,
                            'variation': variation,
                            'volume': volume
                        })
                    except Exception as e:
                        continue
                if not data_scrapees:
                    print("❌ Aucune donnée scrapée - Vérifier la structure HTML")
                    return []
                print(f"✅ {len(data_scrapees)} actions scrapées avec succès")
                # Exemple affichage
                print("\nEXEMPLE D'UNE ACTION :")
                import pprint
                pprint.pprint(data_scrapees[0], width=120, compact=False)
                return data_scrapees
            except Exception as e:
                print(f"[ERREUR] {e}")
                return []

        def main():
            print("[TRACE] main() lancé")
            data = scraper_brvm_html_enrichi()
            print(f"{len(data)} lignes récupérées")

        if __name__ == "__main__":
            print("[TRACE] Script exécuté directement")
            main()
            page = 0
            while True:
                url = BASE_URL if page == 0 else f"{BASE_URL}?page={page}"
                print(f"\n[DEBUG] Scraping {url}")
                response = requests.get(url)
                print(f"[DEBUG] HTTP status: {response.status_code}")
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                content = soup.find("div", class_="view-content")
                if not content:
                    print("[DEBUG] Aucun contenu principal trouvé (div.view-content introuvable)")
                    break
                rows = content.find_all("div", class_="views-row")
                print(f"[DEBUG] Nombre de blocs société trouvés: {len(rows)}")
                if not rows:
                    print("[DEBUG] Aucune société trouvée sur cette page.")
                    break
                for idx, div in enumerate(rows):
                    print(f"[DEBUG] Extraction société #{idx+1} sur la page...")
                    info = extract_societe_info(div)
                    societes.append(info)
                # Pagination: détecter si un bouton "next" existe
                pagination = soup.find("ul", class_="pagination")
                if not pagination or not pagination.find("li", class_="next"):
                    print("[DEBUG] Fin de la pagination ou bouton 'next' absent.")
                    break
                page += 1
                time.sleep(1)  # Respecter le serveur
            print(f"[DEBUG] Extraction terminée. Total sociétés: {len(societes)}")
            return societes

        def main():
            societes = get_all_societes()
            if societes:
                import os
                import pandas as pd
                df = pd.DataFrame(societes)
                print("\nAPERÇU DU DATAFRAME (liens inclus):")
                print(df[['nom','url_action']].head(10))
                # Forcer l’export dans un dossier existant
                export_dir = os.path.join(os.path.dirname(__file__), '../../csv')
                export_dir = os.path.abspath(export_dir)
                os.makedirs(export_dir, exist_ok=True)
                export_path = os.path.join(export_dir, 'brvm_societes_cotees.csv')
                df.to_csv(export_path, index=False)
                print(f"\n{len(df)} sociétés extraites. Résultat sauvegardé dans {export_path}")

                # --- Scraping des pages individuelles pour toutes les sociétés cotées ---
                print("\n[INFO] Extraction structurée et maximale sur toutes les pages individuelles :")
                all_structured = []
                for i, soc in enumerate(societes):
                    url = soc.get('url_action')
                    if not url:
                        print(f"{soc['nom']}: Pas de lien individuel trouvé.")
                        continue
                    print(f"\n[PAGE] {i+1}/{len(societes)} {soc['nom']} -> {url}")
                    try:
                        resp = requests.get(url, timeout=20)
                        resp.raise_for_status()
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        data = {"nom": soc['nom'], "url": url}
                        # 1. Titre principal
                        titre = soup.find('h1')
                        data['titre'] = titre.get_text(strip=True) if titre else 'N/A'
                        # 2. Description
                        desc = soup.find('div', class_='field-item')
                        data['description'] = desc.get_text(strip=True) if desc else ''
                        # 3. Tables d'infos clés (ratios, capitalisation, etc.)
                        tables = soup.find_all('table')
                        for t in tables:
                            for row in t.find_all('tr'):
                                cells = row.find_all(['td','th'])
                                if len(cells) == 2:
                                    k = cells[0].get_text(strip=True)
                                    v = cells[1].get_text(strip=True)
                                    # Mapping structuré pour les champs connus
                                    k_map = k.lower().replace(':','').replace(' ','_')
                                    if 'capitalisation' in k_map:
                                        data['capitalisation'] = v
                                    elif 'p/e' in k_map or 'per' in k_map:
                                        data['per'] = v
                                    elif 'p/b' in k_map or 'pbr' in k_map:
                                        data['pbr'] = v
                                    elif 'dividende' in k_map:
                                        data['dividende'] = v
                                    elif 'volume' in k_map:
                                        data['volume'] = v
                                    elif 'variation' in k_map:
                                        data['variation'] = v
                                    elif 'date' in k_map:
                                        data['date'] = v
                                    else:
                                        # Extraction maximale : tout ce qui n'est pas mappé
                                        data[k_map] = v
                        # 4. Blocs d'infos supplémentaires (ex: <div class="field">)
                        for field in soup.find_all('div', class_='field'):
                            label = field.find('div', class_='field-label')
                            value = field.find('div', class_='field-item')
                            if label and value:
                                k = label.get_text(strip=True).lower().replace(':','').replace(' ','_')
                                v = value.get_text(strip=True)
                                data[k] = v
                        # 5. Historique, ratios, actionnaires, gouvernance, etc. (si présents)
                        # (Extraction générique, à spécialiser selon structure réelle)
                        all_structured.append(data)
                        print(f"  Attributs extraits : {list(data.keys())}")
                    except Exception as ex:
                        print(f"  [ERREUR] Impossible d'extraire la page: {ex}")
                # Export JSON maximal pour analyse IA ou post-traitement
                import json
                export_json = os.path.join(export_dir, 'brvm_societes_cotees_structured.json')
                with open(export_json, 'w', encoding='utf-8') as f:
                    json.dump(all_structured, f, ensure_ascii=False, indent=2)
                print(f"\n[INFO] Extraction structurée terminée. Résultat JSON : {export_json}")
                # Affichage d'un exemple à l'écran
                if all_structured:
                    print("\nEXEMPLE D'UNE SOCIÉTÉ EXTRAITE (STRUCTURÉE ET MAXIMALE) :\n")
                    import pprint
                    pprint.pprint(all_structured[0], width=120, compact=False)
                else:
                    print("\nAucune donnée structurée extraite pour affichage exemple.")
            else:
                print("Aucune société extraite.")

        if __name__ == "__main__":
            print("[TRACE] Bloc __main__ exécuté.")
            main()

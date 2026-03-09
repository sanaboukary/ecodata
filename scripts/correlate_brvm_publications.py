import re
from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db

# Liste des symboles d'actions BRVM (à adapter si besoin)
BRVM_SYMBOLS = [
    'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS', 'CABC', 'CFAC', 'CIEC', 'ETIT',
    'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONTBF', 'ORAC', 'PALC', 'PRSC', 'SAFCA', 'SAFC', 'SCRC', 'SDCC',
    'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SIVC', 'SLBC', 'SMBC', 'SNTS', 'SOGC', 'SPHC',
    'STAC', 'STBC', 'SVOC', 'TMLC', 'TTLC', 'TTLS', 'TTRC', 'TTRS', 'UNXC', 'VRAC'
]

# Expressions régulières pour détecter les mentions d'actions dans le texte
SYMBOL_PATTERNS = [re.compile(rf'\b{symbol}\b', re.IGNORECASE) for symbol in BRVM_SYMBOLS]


def find_symbols_in_text(text):
    found = set()
    for symbol, pattern in zip(BRVM_SYMBOLS, SYMBOL_PATTERNS):
        if pattern.search(text):
            found.add(symbol)
    return list(found)


def correlate_publications_and_stocks(window_days=2):
    _, db = get_mongo_db()
    pubs = list(db.brvm_publications.find({'text_content': {'$exists': True, '$ne': ''}}))
    for pub in pubs:
        pub_date = pub.get('ts')
        if not pub_date:
            continue
        pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
        # Chercher les symboles mentionnés
        text = pub.get('text_content', '')
        mentioned = find_symbols_in_text(text)
        correlations = []
        for symbol in mentioned:
            # Fenêtre de +/- window_days autour de la publication
            start = (pub_dt - timedelta(days=window_days)).isoformat()
            end = (pub_dt + timedelta(days=window_days)).isoformat()
            obs = list(db.curated_observations.find({
                'source': 'BRVM',
                'key': symbol,
                'ts': {'$gte': start, '$lte': end}
            }))
            # Calcul de la variation sur la période
            if obs:
                obs_sorted = sorted(obs, key=lambda o: o['ts'])
                var = obs_sorted[-1]['value'] - obs_sorted[0]['value']
                pct = 100 * var / obs_sorted[0]['value'] if obs_sorted[0]['value'] else 0
                correlations.append({
                    'symbol': symbol,
                    'variation_pct': pct,
                    'obs_count': len(obs),
                    'start': obs_sorted[0]['ts'],
                    'end': obs_sorted[-1]['ts'],
                })
        db.brvm_publications.update_one({'_id': pub['_id']}, {'$set': {'correlations': correlations, 'symbols_mentioned': mentioned}})
        print(f"Corrélation calculée pour {pub.get('filename')}: {correlations}")

if __name__ == "__main__":
    correlate_publications_and_stocks()

"""
Service de recherche intelligente avec fuzzy matching
"""
from typing import List, Dict, Any, Optional
from fuzzywuzzy import fuzz, process
import re

from plateforme_centralisation.mongo import get_mongo_db


# Constantes pour l'index de recherche
CEDEAO_COUNTRIES = {
    'BEN': '🇧🇯 Bénin',
    'BFA': '🇧🇫 Burkina Faso',
    'CIV': '🇨🇮 Côte d\'Ivoire',
    'CPV': '🇨🇻 Cap-Vert',
    'GMB': '🇬🇲 Gambie',
    'GHA': '🇬🇭 Ghana',
    'GIN': '🇬🇳 Guinée',
    'GNB': '🇬🇼 Guinée-Bissau',
    'LBR': '🇱🇷 Liberia',
    'MLI': '🇲🇱 Mali',
    'NER': '🇳🇪 Niger',
    'NGA': '🇳🇬 Nigeria',
    'SEN': '🇸🇳 Sénégal',
    'SLE': '🇸🇱 Sierra Leone',
    'TGO': '🇹🇬 Togo',
}

BRVM_STOCKS = [
    {'symbol': 'BICC', 'name': 'BICICI', 'sector': 'Finance'},
    {'symbol': 'BNBC', 'name': 'BERNABE', 'sector': 'Distribution'},
    {'symbol': 'BOAB', 'name': 'BOA BENIN', 'sector': 'Finance'},
    {'symbol': 'BOABF', 'name': 'BOA BURKINA FASO', 'sector': 'Finance'},
    {'symbol': 'BOAC', 'name': 'BOA CÔTE D\'IVOIRE', 'sector': 'Finance'},
    {'symbol': 'BOAM', 'name': 'BOA MALI', 'sector': 'Finance'},
    {'symbol': 'BOAN', 'name': 'BOA NIGER', 'sector': 'Finance'},
    {'symbol': 'BOAS', 'name': 'BOA SÉNÉGAL', 'sector': 'Finance'},
    {'symbol': 'CABC', 'name': 'SICABLE', 'sector': 'Industrie'},
    {'symbol': 'CFAC', 'name': 'CFAO MOTORS', 'sector': 'Distribution'},
    {'symbol': 'CIEC', 'name': 'CIE', 'sector': 'Services publics'},
    {'symbol': 'ETIT', 'name': 'ECOBANK TRANSNATIONAL', 'sector': 'Finance'},
    {'symbol': 'FTSC', 'name': 'FILTISAC', 'sector': 'Industrie'},
    {'symbol': 'NEIC', 'name': 'NEI-CEDA', 'sector': 'Industrie'},
    {'symbol': 'NSBC', 'name': 'NSIA BANQUE CI', 'sector': 'Finance'},
    {'symbol': 'NTLC', 'name': 'NESTLE CI', 'sector': 'Agroalimentaire'},
    {'symbol': 'ONTBF', 'name': 'ONATEL', 'sector': 'Télécommunications'},
    {'symbol': 'ORAC', 'name': 'ORANGE CI', 'sector': 'Télécommunications'},
    {'symbol': 'ORAG', 'name': 'ORAGROUP', 'sector': 'Finance'},
    {'symbol': 'PALC', 'name': 'PALM CI', 'sector': 'Agroalimentaire'},
    {'symbol': 'PRSC', 'name': 'TRACTAFRIC MOTORS', 'sector': 'Distribution'},
    {'symbol': 'SAFCA', 'name': 'SAFCA', 'sector': 'Finance'},
    {'symbol': 'SAFC', 'name': 'SAFCA CI', 'sector': 'Finance'},
    {'symbol': 'SCRC', 'name': 'SUCRIVOIRE', 'sector': 'Agroalimentaire'},
    {'symbol': 'SDCC', 'name': 'SODE-CI', 'sector': 'Industrie'},
    {'symbol': 'SDSC', 'name': 'SAPH', 'sector': 'Agroalimentaire'},
    {'symbol': 'SEMC', 'name': 'SMB CI', 'sector': 'Agroalimentaire'},
    {'symbol': 'SGBC', 'name': 'SGCI', 'sector': 'Finance'},
    {'symbol': 'SHEC', 'name': 'SHELL CI', 'sector': 'Énergie'},
    {'symbol': 'SIBC', 'name': 'SIB', 'sector': 'Finance'},
    {'symbol': 'SICC', 'name': 'SICOR', 'sector': 'Industrie'},
    {'symbol': 'SIVC', 'name': 'SIVOM', 'sector': 'Industrie'},
    {'symbol': 'SLBC', 'name': 'SOLIBRA', 'sector': 'Agroalimentaire'},
    {'symbol': 'SMBC', 'name': 'SMB', 'sector': 'Agroalimentaire'},
    {'symbol': 'SNTS', 'name': 'SONATEL', 'sector': 'Télécommunications'},
    {'symbol': 'SOGC', 'name': 'SOGB', 'sector': 'Finance'},
    {'symbol': 'SPHC', 'name': 'SAPH', 'sector': 'Agroalimentaire'},
    {'symbol': 'STAC', 'name': 'SETAO', 'sector': 'Industrie'},
    {'symbol': 'STBC', 'name': 'SOCIETE IVOIRIENNE DE BANQUE', 'sector': 'Finance'},
    {'symbol': 'SVOC', 'name': 'MOVIS', 'sector': 'Distribution'},
    {'symbol': 'TMLC', 'name': 'TOTAL CI', 'sector': 'Énergie'},
    {'symbol': 'TTLC', 'name': 'TOTAL CI', 'sector': 'Énergie'},
    {'symbol': 'TTLS', 'name': 'TOTAL SENEGAL', 'sector': 'Énergie'},
    {'symbol': 'TTRC', 'name': 'TRITURAF', 'sector': 'Agroalimentaire'},
    {'symbol': 'TTRS', 'name': 'TEYLIOM', 'sector': 'Finance'},
    {'symbol': 'UNXC', 'name': 'UNILEVER CI', 'sector': 'Agroalimentaire'},
    {'symbol': 'VRAC', 'name': 'VIVO ENERGY CI', 'sector': 'Énergie'},
]


class SearchService:
    """Service de recherche globale avec fuzzy matching"""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self._build_search_index()
    
    def _build_search_index(self):
        """Construire l'index de recherche en mémoire"""
        
        # Index indicateurs depuis MongoDB
        self.indicators = {}
        pipeline = [
            {"$group": {"_id": "$dataset"}},
            {"$limit": 200}
        ]
        
        for doc in self.db.curated_observations.aggregate(pipeline):
            indicator_code = doc['_id']
            if indicator_code and indicator_code != 'Unknown':
                # Mapping code -> nom lisible (à améliorer avec vraie base)
                self.indicators[indicator_code] = {
                    'code': indicator_code,
                    'name': self._indicator_code_to_name(indicator_code),
                    'type': 'indicator'
                }
        
        # Index pays CEDEAO
        self.countries = {}
        for code, name in CEDEAO_COUNTRIES.items():
            self.countries[code] = {
                'code': code,
                'name': name,
                'type': 'country'
            }
        
        # Index actions BRVM
        self.stocks = {}
        for stock in BRVM_STOCKS:
            symbol = stock['symbol']
            self.stocks[symbol] = {
                'symbol': symbol,
                'name': stock['name'],
                'sector': stock.get('sector', ''),
                'type': 'stock'
            }
        
        # Index sources
        self.sources = {
            'BRVM': {'name': 'BRVM - Bourse Régionale', 'type': 'source'},
            'WorldBank': {'name': 'Banque Mondiale', 'type': 'source'},
            'IMF': {'name': 'Fonds Monétaire International', 'type': 'source'},
            'UN_SDG': {'name': 'ONU - Objectifs Développement Durable', 'type': 'source'},
            'AfDB': {'name': 'Banque Africaine de Développement', 'type': 'source'},
        }
    
    def _indicator_code_to_name(self, code: str) -> str:
        """Convertir code indicateur en nom lisible"""
        # Mapping des indicateurs courants
        mapping = {
            'SP.POP.TOTL': 'Population totale',
            'NY.GDP.MKTP.CD': 'PIB ($ courants)',
            'NY.GDP.PCAP.CD': 'PIB par habitant',
            'NY.GDP.MKTP.KD.ZG': 'Croissance PIB (%)',
            'FP.CPI.TOTL.ZG': 'Inflation (IPC %)',
            'GC.DOD.TOTL.GD.ZS': 'Dette publique (% PIB)',
            'SE.PRM.NENR': 'Taux scolarisation primaire',
            'SH.DYN.MORT': 'Mortalité infantile',
            'EG.ELC.ACCS.ZS': 'Accès électricité (%)',
            'SL.UEM.TOTL.ZS': 'Taux chômage (%)',
            'QUOTES': 'Cours boursiers BRVM',
            'VOLUMES': 'Volumes transactions BRVM',
            'MARKETCAP': 'Capitalisation boursière',
            'PCPI': 'Indice prix consommation',
            'NGDP_R': 'PIB réel',
            'PCPIPCH': 'Inflation prix consommation',
        }
        
        return mapping.get(code, code)
    
    def fuzzy_search(self, query: str, limit: int = 20, threshold: int = 60) -> Dict[str, List[Dict]]:
        """
        Recherche fuzzy sur tous les types de données
        
        Args:
            query: Terme de recherche
            limit: Nombre max résultats par catégorie
            threshold: Score minimum de similarité (0-100)
        
        Returns:
            Dict avec catégories indicators, countries, stocks, sources
        """
        if not query or len(query) < 2:
            return {'indicators': [], 'countries': [], 'stocks': [], 'sources': []}
        
        query = query.strip().lower()
        results = {
            'indicators': [],
            'countries': [],
            'stocks': [],
            'sources': []
        }
        
        # Recherche indicateurs
        indicator_matches = []
        for code, data in self.indicators.items():
            # Match code ou nom
            code_score = fuzz.partial_ratio(query, code.lower())
            name_score = fuzz.partial_ratio(query, data['name'].lower())
            score = max(code_score, name_score)
            
            if score >= threshold:
                indicator_matches.append({
                    'code': code,
                    'name': data['name'],
                    'type': 'indicator',
                    'score': score,
                    'url': f'/dashboards/worldbank/?indicator={code}'
                })
        
        # Trier par score et limiter
        results['indicators'] = sorted(indicator_matches, key=lambda x: x['score'], reverse=True)[:limit]
        
        # Recherche pays
        country_matches = []
        for code, data in self.countries.items():
            code_score = fuzz.partial_ratio(query, code.lower())
            name_score = fuzz.partial_ratio(query, data['name'].lower())
            score = max(code_score, name_score)
            
            if score >= threshold:
                country_matches.append({
                    'code': code,
                    'name': data['name'],
                    'type': 'country',
                    'score': score,
                    'url': f'/compare/countries/?countries={code}'
                })
        
        results['countries'] = sorted(country_matches, key=lambda x: x['score'], reverse=True)[:limit]
        
        # Recherche actions BRVM
        stock_matches = []
        for symbol, data in self.stocks.items():
            symbol_score = fuzz.partial_ratio(query, symbol.lower())
            name_score = fuzz.partial_ratio(query, data['name'].lower())
            sector_score = fuzz.partial_ratio(query, data['sector'].lower()) if data['sector'] else 0
            score = max(symbol_score, name_score, sector_score)
            
            if score >= threshold:
                stock_matches.append({
                    'symbol': symbol,
                    'name': data['name'],
                    'sector': data['sector'],
                    'type': 'stock',
                    'score': score,
                    'url': f'/dashboards/brvm/?stock={symbol}'
                })
        
        results['stocks'] = sorted(stock_matches, key=lambda x: x['score'], reverse=True)[:limit]
        
        # Recherche sources
        source_matches = []
        for source_id, data in self.sources.items():
            name_score = fuzz.partial_ratio(query, data['name'].lower())
            id_score = fuzz.partial_ratio(query, source_id.lower())
            score = max(name_score, id_score)
            
            if score >= threshold:
                source_matches.append({
                    'id': source_id,
                    'name': data['name'],
                    'type': 'source',
                    'score': score,
                    'url': f'/dashboards/{source_id.lower()}/'
                })
        
        results['sources'] = sorted(source_matches, key=lambda x: x['score'], reverse=True)[:limit]
        
        return results
    
    def autocomplete(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Suggestions rapides pour autocomplete
        
        Args:
            query: Début du terme recherché
            limit: Nombre suggestions
        
        Returns:
            Liste suggestions avec score
        """
        if not query or len(query) < 2:
            return []
        
        query = query.strip().lower()
        suggestions = []
        
        # Recherche rapide sur tous types
        all_items = []
        
        # Indicateurs
        for code, data in list(self.indicators.items())[:50]:
            if query in code.lower() or query in data['name'].lower():
                all_items.append({
                    'label': f"{data['name']} ({code})",
                    'value': code,
                    'type': 'indicator',
                    'category': '📊 Indicateur'
                })
        
        # Pays
        for code, data in self.countries.items():
            if query in code.lower() or query in data['name'].lower():
                all_items.append({
                    'label': f"{data['name']} ({code})",
                    'value': code,
                    'type': 'country',
                    'category': '🌍 Pays'
                })
        
        # Actions
        for symbol, data in list(self.stocks.items())[:30]:
            if query in symbol.lower() or query in data['name'].lower():
                all_items.append({
                    'label': f"{data['name']} ({symbol})",
                    'value': symbol,
                    'type': 'stock',
                    'category': '📈 Action BRVM'
                })
        
        # Limiter et retourner
        return all_items[:limit]
    
    def search_mongodb(self, query: str, source: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Recherche directe dans MongoDB avec regex
        
        Args:
            query: Terme recherche
            source: Filtrer par source (optionnel)
            limit: Nombre résultats
        
        Returns:
            Liste observations MongoDB
        """
        if not query or len(query) < 2:
            return []
        
        # Construire requête regex (insensible casse)
        regex_pattern = re.escape(query)
        mongo_query = {
            "$or": [
                {"dataset": {"$regex": regex_pattern, "$options": "i"}},
                {"key": {"$regex": regex_pattern, "$options": "i"}},
            ]
        }
        
        if source:
            mongo_query["source"] = source
        
        # Requête MongoDB
        results = list(
            self.db.curated_observations
            .find(mongo_query)
            .sort("ts", -1)
            .limit(limit)
        )
        
        # Formater résultats
        formatted = []
        for obs in results:
            formatted.append({
                'source': obs.get('source', ''),
                'dataset': obs.get('dataset', ''),
                'key': obs.get('key', ''),
                'date': obs.get('ts', '')[:10],
                'value': obs.get('value', 0),
                'type': 'observation'
            })
        
        return formatted
    
    def get_recent_searches(self, user_id: Optional[int] = None, limit: int = 5) -> List[str]:
        """
        Récupérer recherches récentes utilisateur
        
        Args:
            user_id: ID utilisateur (ou session)
            limit: Nombre recherches
        
        Returns:
            Liste termes recherchés récemment
        """
        # TODO: Implémenter stockage recherches en session ou DB
        # Pour l'instant retourner recherches populaires
        return [
            'PIB',
            'population',
            'inflation',
            'SONATEL',
            'Côte d\'Ivoire'
        ]
    
    def highlight_match(self, text: str, query: str) -> str:
        """
        Highlighter les termes matchés dans le texte
        
        Args:
            text: Texte complet
            query: Terme recherché
        
        Returns:
            HTML avec <mark> tags
        """
        if not query or not text:
            return text
        
        # Regex insensible casse
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)
        
        return highlighted
    
    def __del__(self):
        """Fermer connexion MongoDB"""
        if hasattr(self, 'client'):
            self.client.close()


# Instance singleton
search_service = SearchService()

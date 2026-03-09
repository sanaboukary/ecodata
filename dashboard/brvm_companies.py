# -*- coding: utf-8 -*-
"""Mapping des symboles BRVM vers noms complets des sociétés"""

BRVM_COMPANY_NAMES = {
    # Banques
    'BOAB': 'Bank of Africa Benin',
    'BOABF': 'Bank of Africa Burkina Faso',
    'BOAC': 'Bank of Africa Côte d\'Ivoire',
    'BOAM': 'Bank of Africa Mali',
    'BOAN': 'Bank of Africa Niger',
    'BOAS': 'Bank of Africa Sénégal',
    'BICC': 'BICICI - Banque Internationale pour le Commerce',
    'CBIBF': 'Coris Bank International Burkina Faso',
    'ETIT': 'Ecobank Transnational Incorporated',
    'SIBC': 'Société Ivoirienne de Banque',
    'SGBC': 'Société Générale Burkina',
    'SGBCI': 'Société Générale de Banques CI',
    'STBC': 'Société Togolaise de Banque',
    'SAFC': 'SAFCA - Société Africaine de Crédit Automobile',
    
    # Assurances
    'NSIC': 'NSIA Assurances CI',
    'NSBC': 'NSIA Banque CI',
    
    # Agriculture & Agroalimentaire
    'PALC': 'Palmci - Palme et huileries',
    'SIVC': 'SIVOM - Société Ivoirienne',
    'SOGC': 'SOGB - Société des Grains',
    'PHCC': 'PHI - Produits Huiliers',
    'SUCV': 'Sucrivoire - Sucrerie',
    'UNXC': 'UNILEVER CI',
    
    # Télécoms & Technologies<br/>    'ABJC': 'Bollore Transport & Logistics CI',
    'SNTS': 'Sonatel - Société Nationale des Télécommunications du Sénégal',
    'TTLS': 'Tractafric Motors',
    'ONTBF': 'ONATEL Burkina',
    
    # Distribution
    'CFAC': 'CFAO Motors CI',
    'PRSC': 'Pres Froid - Distribution',
    'SDCC': 'SODEPALM - Palmeraie',
    'SMBC': 'SMB - Société Malienne',
    'STAC': 'SITAB - Tabac',
    
    # Industries
    'NEIC': 'NEI-CEDA',
    'SEMC': 'SIEM - Société Industrielle',
    'SICC': 'SICOR - Société Ivoirienne',
    'SLBC': 'SOLIBRA - Brasserie',
    'TTRC': 'TRITURAF - Trituration',
    'SDSC': 'SODE - Développement',
    'SICB': 'SIC - Société Ivoirienne de Construction',
    
    # Autres
    'BNBC': 'BNB - Banque Nationale du Burkina',
    'FTSC': 'Filtisac - Emballages',
    'SEMC': 'SEM - Société d\'Exploitation Minière',
}

def get_company_name(symbol):
    """Retourne le nom complet d'une société BRVM depuis son symbole"""
    return BRVM_COMPANY_NAMES.get(symbol, symbol)

def get_all_symbols():
    """Retourne tous les symboles BRVM connus"""
    return list(BRVM_COMPANY_NAMES.keys())

"""
Liste complète des actions cotées à la BRVM (Bourse Régionale des Valeurs Mobilières)
Source: BRVM - Marché des Actions
"""

# Actions cotées à la BRVM par secteur
BRVM_STOCKS = {
    # AGRICULTURE
    "PALC": {"name": "PALM CI", "sector": "Agriculture", "country": "CI"},
    "SDCC": {"name": "SUCRIVOIRE", "sector": "Agriculture", "country": "CI"},
    "SIVC": {"name": "SIVOM", "sector": "Agriculture", "country": "CI"},
    "TTLC": {"name": "TOTAL CI", "sector": "Agriculture", "country": "CI"},
    "SCRC": {"name": "SUCRE CI", "sector": "Agriculture", "country": "CI"},
    
    # BANQUES & FINANCE
    "BOAB": {"name": "BOA BENIN", "sector": "Banque", "country": "BJ"},
    "BOABF": {"name": "BOA BURKINA", "sector": "Banque", "country": "BF"},
    "BOAC": {"name": "BOA CI", "sector": "Banque", "country": "CI"},
    "BOAM": {"name": "BOA MALI", "sector": "Banque", "country": "ML"},
    "BOAN": {"name": "BOA NIGER", "sector": "Banque", "country": "NE"},
    "BOAS": {"name": "BOA SENEGAL", "sector": "Banque", "country": "SN"},
    "BOAG": {"name": "BOA TOGO", "sector": "Banque", "country": "TG"},
    
    "BICC": {"name": "BICICI", "sector": "Banque", "country": "CI"},
    "CBIBF": {"name": "CORIS BANK BURKINA", "sector": "Banque", "country": "BF"},
    "ECOC": {"name": "ECOBANK CI", "sector": "Banque", "country": "CI"},
    "ETIT": {"name": "ECOBANK TOGO", "sector": "Banque", "country": "TG"},
    "NTLC": {"name": "NSIA BANQUE CI", "sector": "Banque", "country": "CI"},
    "ORGT": {"name": "ORAGROUP TOGO", "sector": "Banque", "country": "TG"},
    "SAFC": {"name": "SAFCA CI", "sector": "Banque", "country": "CI"},
    "SGBC": {"name": "SGBCI", "sector": "Banque", "country": "CI"},
    "SGBSL": {"name": "SGBS", "sector": "Banque", "country": "SL"},
    "SIBC": {"name": "SIB CI", "sector": "Banque", "country": "CI"},
    "STBC": {"name": "STANBIC BANK", "sector": "Banque", "country": "CI"},
    "TTRC": {"name": "TRACTAFRIC MOTORS", "sector": "Banque", "country": "CI"},
    
    # ASSURANCE
    "NSIAC": {"name": "NSIA ASSURANCES CI", "sector": "Assurance", "country": "CI"},
    "NSIAS": {"name": "NSIA VIE", "sector": "Assurance", "country": "CI"},
    "SPHC": {"name": "SAHAM ASSURANCE CI", "sector": "Assurance", "country": "CI"},
    
    # INDUSTRIE
    "NEIC": {"name": "NEI-CEDA", "sector": "Industrie", "country": "CI"},
    "SEMC": {"name": "SIEM CI", "sector": "Industrie", "country": "CI"},
    "SICC": {"name": "SICABLE", "sector": "Industrie", "country": "CI"},
    "SMBC": {"name": "SMB CI", "sector": "Industrie", "country": "CI"},
    "SNTS": {"name": "SONATEL", "sector": "Industrie", "country": "SN"},
    "SPHB": {"name": "SAPH", "sector": "Industrie", "country": "CI"},
    "STAC": {"name": "SETAO", "sector": "Industrie", "country": "CI"},
    "TTLS": {"name": "TOTAL SENEGAL", "sector": "Industrie", "country": "SN"},
    "UNLC": {"name": "UNILEVER CI", "sector": "Industrie", "country": "CI"},
    
    # DISTRIBUTION
    "PRSC": {"name": "PROSUMA CI", "sector": "Distribution", "country": "CI"},
    "SHEC": {"name": "SHELL CI", "sector": "Distribution", "country": "CI"},
    "TTBC": {"name": "TOTAL BURKINA", "sector": "Distribution", "country": "BF"},
    
    # TRANSPORT
    "ABJC": {"name": "BOLLORE TRANSPORT CI", "sector": "Transport", "country": "CI"},
    "SDSC": {"name": "BOLLORE LOGISTICS CI", "sector": "Transport", "country": "CI"},
    
    # SERVICES PUBLICS
    "CIEC": {"name": "CIE CI", "sector": "Services Publics", "country": "CI"},
    "ONTBF": {"name": "ONATEL BURKINA", "sector": "Services Publics", "country": "BF"},
    "SCRC": {"name": "SOLIBRA", "sector": "Services Publics", "country": "CI"},
    "SNDC": {"name": "SNEDAI", "sector": "Services Publics", "country": "CI"},
    "SPHC": {"name": "SODECI", "sector": "Services Publics", "country": "CI"},
    
    # AUTRES
    "CIAC": {"name": "CFAO CI", "sector": "Autres", "country": "CI"},
    "FTSC": {"name": "FILTISAC", "sector": "Autres", "country": "CI"},
    "SOGC": {"name": "SOGB", "sector": "Autres", "country": "CI"},
}

def get_all_symbols():
    """Retourne la liste de tous les symboles BRVM"""
    return list(BRVM_STOCKS.keys())

def get_stock_info(symbol: str):
    """Retourne les informations d'une action"""
    return BRVM_STOCKS.get(symbol, {})

def get_stocks_by_sector(sector: str):
    """Retourne toutes les actions d'un secteur"""
    return {k: v for k, v in BRVM_STOCKS.items() if v.get("sector") == sector}

def get_stocks_by_country(country: str):
    """Retourne toutes les actions d'un pays"""
    return {k: v for k, v in BRVM_STOCKS.items() if v.get("country") == country}

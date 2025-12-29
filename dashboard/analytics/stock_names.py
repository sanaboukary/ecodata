"""
Mapping des symboles BRVM vers les noms complets des sociétés
"""

BRVM_STOCK_NAMES = {
    # Banques
    'BOAB': 'Bank Of Africa Bénin',
    'BOABF': 'Bank Of Africa Burkina Faso',
    'BOAC': 'Bank Of Africa Côte d\'Ivoire',
    'BOAM': 'Bank Of Africa Mali',
    'BOAN': 'Bank Of Africa Niger',
    'BOAS': 'Bank Of Africa Sénégal',
    'SGBC': 'Société Générale de Banques au Cameroun',
    'SGBCI': 'Société Générale de Banques en Côte d\'Ivoire',
    'SGBSL': 'Société Générale de Banques au Sierra Leone',
    'CIEC': 'Compagnie Ivoirienne d\'Electricité',
    'CBIBF': 'Coris Bank International Burkina Faso',
    'ETIT': 'Ecobank Transnational Incorporated',
    'BICI': 'Banque Internationale pour le Commerce et l\'Industrie',
    'BICC': 'Banque Internationale pour le Commerce et l\'Industrie du Cameroun',
    
    # Agriculture & Agro-industrie
    'PALC': 'Palm Côte d\'Ivoire',
    'SICC': 'Société Ivoirienne de Coco',
    'SCRC': 'Sucrivoire',
    'PHCI': 'Palmafrique Holding',
    'SPHC': 'SIFCA Holding',
    'SPHB': 'Société des Plantations d\'Hévéa',
    
    # Distribution
    'PRSC': 'Tractafric Motors Côte d\'Ivoire',
    'TTLS': 'Total Sénégal',
    'TTLC': 'Total Côte d\'Ivoire',
    
    # Télécommunications
    'SNTS': 'Sonatel',
    'ABJC': 'Atlantique Télécom Benin',
    'ORGT': 'Orange Côte d\'Ivoire',
    
    # Industrie & Services
    'SMBC': 'SMB Côte d\'Ivoire',
    'FTSC': 'Filtisac',
    'NSIAC': 'NSIA Assurances Côte d\'Ivoire',
    'NSIAS': 'NSIA Assurances Sénégal',
    'NEIC': 'NEI-CEDA Côte d\'Ivoire',
    'NTLC': 'Nestlé Côte d\'Ivoire',
    'SDCC': 'SODE Côte d\'Ivoire',
    'SDSC': 'Société de Distribution Sénégal',
    'SEMC': 'SETAO Côte d\'Ivoire',
    'SIVC': 'Air Liquide Côte d\'Ivoire',
    'UNLC': 'Unilever Côte d\'Ivoire',
    'ECOC': 'Ecobank Côte d\'Ivoire',
    'SAFC': 'SAFCA',
    'SNDC': 'Société Nouvelle Dinderesso',
    'ONTBF': 'ONATEL Burkina Faso',
    
    # Transport & Logistique
    'SDVC': 'Société de Distribution de Véhicules',
    'CABC': 'Compagnie Africaine de Bois',
    
    # Autres
    'BOAG': 'BOA Group',
    'SGBC': 'Société Générale Bénin',
    'SLBC': 'Société Libérienne de Banque',
    'SHEC': 'Société Hôtelière et d\'Equipements',
    'SOGC': 'Société de Gestion et de Commercialisation',
    'STBC': 'SITAB Côte d\'Ivoire',
    'STAC': 'Société de Transport Africain',
}


def get_stock_full_name(symbol: str) -> str:
    """
    Retourne le nom complet d'une action à partir de son symbole
    
    Args:
        symbol: Code symbole de l'action (ex: 'BOAM')
    
    Returns:
        Nom complet de l'action ou le symbole si non trouvé
    """
    return BRVM_STOCK_NAMES.get(symbol, symbol)


def get_stock_display_name(symbol: str) -> str:
    """
    Retourne le nom à afficher (symbole + nom complet)
    
    Args:
        symbol: Code symbole de l'action (ex: 'BOAM')
    
    Returns:
        Format: "BOAM - Bank Of Africa Mali"
    """
    full_name = BRVM_STOCK_NAMES.get(symbol)
    if full_name:
        return f"{symbol} - {full_name}"
    return symbol

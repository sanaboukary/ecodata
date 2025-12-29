"""
Configuration des KPIs (Indicateurs Clés de Performance)
pour chaque source de données
"""

# ========================================================================
# 1. BRVM - Bourse Régionale des Valeurs Mobilières
# ========================================================================

BRVM_KPI_CONFIG = {
    "cours_actions": {
        "description": "Cours moyens journaliers des actions",
        "objectif": "Suivre la dynamique des prix et la valorisation sectorielle",
        "donnees_necessaires": [
            "prix_ouverture",
            "prix_plus_haut",
            "prix_plus_bas", 
            "prix_cloture",
            "volume_journalier",
            "ticker",
            "secteur",
            "dividendes",
            "splits"
        ],
        "frequence": "Horaire",
        "symbols": [
            "BICC", "BOAB", "BOABF", "BNBC", "ETIT", "ONTBF",
            "PALM", "PRSC", "SDCC", "SDSC", "SHEC", "SIBC",
            "SITC", "SLBC", "SMBC", "SNTS", "SOGB", "STBC",
            "STAC", "TTLC", "TTLS", "UNXC"
        ]
    },
    "indices": {
        "description": "Indices BRVM Composite & BRVM10",
        "objectif": "Mesurer la performance agrégée du marché",
        "donnees_necessaires": [
            "niveau_quotidien",
            "methodologie",
            "paniers",
            "ponderations"
        ],
        "indices": ["BRVM_COMPOSITE", "BRVM_10"]
    },
    "volumes_transactions": {
        "description": "Volumes et valeurs des transactions",
        "objectif": "Évaluer la liquidité et l'activité de marché",
        "donnees_necessaires": [
            "volume_negocie",
            "valeur_negociee",
            "nombre_transactions",
            "carnet_ordres"
        ]
    },
    "capitalisation": {
        "description": "Capitalisation boursière",
        "objectif": "Suivre la taille du marché et contribution sectorielle",
        "secteurs": [
            "FINANCE", "AGRICULTURE", "DISTRIBUTION",
            "INDUSTRIE", "SERVICES_PUBLICS", "TRANSPORT"
        ]
    }
}

# ========================================================================
# 2. FMI - Fonds Monétaire International
# ========================================================================

IMF_KPI_CONFIG = {
    "pib": {
        "description": "PIB réel & PIB par habitant",
        "objectif": "Mesurer l'activité économique",
        "indicateurs": {
            "PIB_REEL": "NGDP_R",
            "PIB_PERCAPITA": "NGDPPC",
            "PIB_PPA": "PPPPC"
        },
        "pays": ["BEN", "BFA", "CIV", "GIN", "MLI", "NER", "SEN", "TGO"],
        "periodicite": "Annuel"
    },
    "inflation": {
        "description": "Taux d'inflation (IPC)",
        "objectif": "Suivre la stabilité des prix",
        "indicateurs": {
            "IPC": "PCPI_IX",
            "IPC_VARIATION": "PCPIPCH"
        },
        "periodicite": "Mensuel"
    },
    "balance_paiements": {
        "description": "Balance des paiements",
        "objectif": "Évaluer la soutenabilité externe",
        "indicateurs": {
            "COMPTE_COURANT": "BCA_BP6_USD",
            "BALANCE_COMMERCIALE": "BG_BP6_USD",
            "EXPORTS": "BX_BP6_USD",
            "IMPORTS": "BM_BP6_USD"
        }
    },
    "finances_publiques": {
        "description": "Finances publiques",
        "objectif": "Apprécier la position fiscale",
        "indicateurs": {
            "SOLDE_BUDGETAIRE": "GGR_G01_GDP_PT",
            "RECETTES": "GGR_GDP_PT",
            "DEPENSES": "GGX_GDP_PT",
            "DETTE_PUBLIQUE": "GGXWDG_GDP_PT"
        }
    },
    "taux_change": {
        "description": "Taux de change effectif",
        "objectif": "Évaluer la compétitivité-prix",
        "indicateurs": {
            "TCER": "EREER_IX",
            "TCEN": "ENEER_IX",
            "TAUX_NOMINAL": "ENDA_XDC_USD_RATE"
        }
    }
}

# ========================================================================
# 3. BAD - Banque Africaine de Développement
# ========================================================================

AFDB_KPI_CONFIG = {
    "dette_exterieure": {
        "description": "Dette extérieure totale",
        "objectif": "Apprécier la charge externe",
        "indicateurs": {
            "DETTE_TOTALE": "DEBT.EXTERNAL.TOTAL",
            "DETTE_PIB": "DEBT.EXTERNAL.GDP_RATIO",
            "SERVICE_DETTE": "DEBT.SERVICE.RATIO"
        }
    },
    "projets_finances": {
        "description": "Projets financés par la BAD",
        "objectif": "Suivre l'effort d'investissement",
        "donnees": [
            "montant_engage",
            "montant_decaisse",
            "nombre_projets",
            "secteur",
            "pays",
            "statut",
            "dates_cles"
        ],
        "secteurs": [
            "INFRASTRUCTURES", "ENERGIE", "SANTE",
            "EDUCATION", "AGRICULTURE", "EAU_ASSAINISSEMENT"
        ]
    },
    "repartition_sectorielle": {
        "description": "Répartition des financements",
        "objectif": "Identifier les priorités d'allocation",
        "dimensions": ["secteur", "pays", "region", "instrument"]
    },
    "macro_indicateurs": {
        "description": "Indicateurs macroéconomiques BAD",
        "indicateurs": {
            "PIB": "GDP.CURRENT.USD",
            "INFLATION": "INFLATION.CPI",
            "CROISSANCE": "GDP.GROWTH.RATE"
        }
    },
    "taux_absorption": {
        "description": "Taux d'absorption des projets",
        "objectif": "Mesurer l'exécution des projets",
        "metriques": [
            "taux_engagement",
            "taux_decaissement",
            "taux_execution",
            "retards"
        ]
    }
}

# ========================================================================
# 4. ONU - Objectifs de Développement Durable
# ========================================================================

UN_KPI_CONFIG = {
    "idh": {
        "description": "Indice de Développement Humain",
        "objectif": "Suivre le progrès humain multidimensionnel",
        "dimensions": {
            "IDH_GLOBAL": "HDI.INDEX",
            "IDH_SANTE": "HDI.HEALTH",
            "IDH_EDUCATION": "HDI.EDUCATION",
            "IDH_REVENU": "HDI.INCOME"
        },
        "periodicite": "Annuel"
    },
    "odd_prioritaires": {
        "description": "Indicateurs ODD prioritaires",
        "objectif": "Mesurer l'avancement vers les cibles ODD",
        "indicateurs": {
            "ODD1_PAUVRETE": "SI_POV_DAY1",
            "ODD3_SANTE": "SH_STA_MORT",
            "ODD4_EDUCATION": "SE_TOT_ENRP",
            "ODD5_EGALITE_GENRE": "SG_GEN_PARL",
            "ODD8_EMPLOI": "SL_TLF_UEM",
            "ODD10_INEGALITES": "SI_POV_GINI",
            "ODD13_CLIMAT": "EN_ATM_CO2E_PC"
        }
    },
    "demographie": {
        "description": "Croissance démographique & structure",
        "objectif": "Anticiper les besoins en services publics",
        "indicateurs": {
            "POPULATION": "SP_POP_TOTL",
            "CROISSANCE_POP": "SP_POP_GROW",
            "STRUCTURE_AGE": "SP_POP_0014_TO_ZS",
            "FECONDITE": "SP_DYN_TFRT_IN",
            "MORTALITE": "SP_DYN_IMRT_IN"
        }
    },
    "urbanisation": {
        "description": "Taux d'urbanisation & migration",
        "objectif": "Apprécier les pressions urbaines",
        "indicateurs": {
            "POP_URBAINE": "SP_URB_TOTL",
            "TAUX_URBANISATION": "SP_URB_TOTL_IN_ZS",
            "CROISSANCE_URBAINE": "SP_URB_GROW",
            "MIGRATION_NETTE": "SM_POP_NETM"
        }
    },
    "commerce": {
        "description": "Commerce international",
        "objectif": "Évaluer l'intégration commerciale",
        "indicateurs": {
            "EXPORTS": "TX_VAL_MRCH_XD_WD",
            "IMPORTS": "TM_VAL_MRCH_XD_WD",
            "BALANCE_COMMERCIALE": "NE_RSB_GNFS_CD"
        }
    },
    "inegalites": {
        "description": "Indice de Gini",
        "objectif": "Suivre les inégalités de revenus",
        "indicateur": "SI_POV_GINI"
    }
}

# ========================================================================
# 5. BANQUE MONDIALE - World Development Indicators
# ========================================================================

WB_KPI_CONFIG = {
    "croissance_economique": {
        "description": "Croissance et PIB",
        "objectif": "Mesurer la trajectoire de croissance",
        "indicateurs": {
            "CROISSANCE_PIB": "NY.GDP.MKTP.KD.ZG",
            "PIB_REEL": "NY.GDP.MKTP.KD",
            "PIB_PERCAPITA": "NY.GDP.PCAP.CD",
            "RNB_PERCAPITA": "NY.GNP.PCAP.CD",
            "PIB_PPA": "NY.GDP.PCAP.PP.CD"
        },
        "pays": ["BEN", "BFA", "CIV", "GIN", "MLI", "NER", "SEN", "TGO"],
        "periode": "2000:2024"
    },
    "pauvrete": {
        "description": "Taux de pauvreté",
        "objectif": "Suivre la pauvreté extrême",
        "indicateurs": {
            "PAUVRETE_190": "SI.POV.DDAY",
            "PAUVRETE_320": "SI.POV.LMIC",
            "PAUVRETE_NATIONALE": "SI.POV.NAHC",
            "GAP_PAUVRETE": "SI.POV.GAP2"
        }
    },
    "depenses_publiques": {
        "description": "Dépenses publiques sectorielles",
        "objectif": "Évaluer l'effort budgétaire sectoriel",
        "indicateurs": {
            "SANTE": "SH.XPD.CHEX.GD.ZS",
            "EDUCATION": "SE.XPD.TOTL.GD.ZS",
            "DEFENSE": "MS.MIL.XPND.GD.ZS"
        }
    },
    "doing_business": {
        "description": "Environnement des affaires",
        "objectif": "Apprécier le climat des affaires",
        "dimensions": [
            "CLASSEMENT_GLOBAL",
            "CREATION_ENTREPRISE",
            "OBTENTION_CREDIT",
            "PAIEMENT_TAXES",
            "COMMERCE_TRANSFRONTALIER",
            "EXECUTION_CONTRATS"
        ]
    },
    "gouvernance": {
        "description": "Indicateurs de gouvernance (WGI)",
        "objectif": "Évaluer la qualité institutionnelle",
        "indicateurs": {
            "VOIX_RESPONSABILITE": "VA.EST",
            "STABILITE_POLITIQUE": "PV.EST",
            "EFFICACITE_GOUVERNEMENT": "GE.EST",
            "QUALITE_REGULATION": "RQ.EST",
            "ETAT_DROIT": "RL.EST",
            "CONTROLE_CORRUPTION": "CC.EST"
        }
    },
    "demographie": {
        "description": "Indicateurs démographiques",
        "indicateurs": {
            "POPULATION": "SP.POP.TOTL",
            "CROISSANCE_POP": "SP.POP.GROW",
            "ESPERANCE_VIE": "SP.DYN.LE00.IN",
            "TAUX_NATALITE": "SP.DYN.CBRT.IN",
            "TAUX_MORTALITE": "SP.DYN.CDRT.IN"
        }
    }
}

# ========================================================================
# MAPPING DES CODES PAYS
# ========================================================================

COUNTRY_CODES = {
    "BEN": {"iso3": "BEN", "iso2": "BJ", "name": "Bénin", "region": "West Africa"},
    "BFA": {"iso3": "BFA", "iso2": "BF", "name": "Burkina Faso", "region": "West Africa"},
    "CIV": {"iso3": "CIV", "iso2": "CI", "name": "Côte d'Ivoire", "region": "West Africa"},
    "GIN": {"iso3": "GIN", "iso2": "GN", "name": "Guinée", "region": "West Africa"},
    "MLI": {"iso3": "MLI", "iso2": "ML", "name": "Mali", "region": "West Africa"},
    "NER": {"iso3": "NER", "iso2": "NE", "name": "Niger", "region": "West Africa"},
    "SEN": {"iso3": "SEN", "iso2": "SN", "name": "Sénégal", "region": "West Africa"},
    "TGO": {"iso3": "TGO", "iso2": "TG", "name": "Togo", "region": "West Africa"}
}

# ========================================================================
# CONFIGURATION DES DASHBOARDS PAR SOURCE
# ========================================================================

DASHBOARD_CONFIG = {
    "brvm": {
        "nom": "Tableau de Bord BRVM",
        "sections": [
            "Évolution des cours",
            "Indices de marché",
            "Volumes et liquidité",
            "Top gagnants/perdants",
            "Capitalisation sectorielle",
            "Analyse de volatilité"
        ]
    },
    "imf": {
        "nom": "Tableau de Bord FMI",
        "sections": [
            "Croissance économique",
            "Inflation et prix",
            "Balance des paiements",
            "Finances publiques",
            "Dette publique",
            "Taux de change"
        ]
    },
    "afdb": {
        "nom": "Tableau de Bord BAD",
        "sections": [
            "Dette extérieure",
            "Portefeuille de projets",
            "Répartition sectorielle",
            "Répartition géographique",
            "Taux d'exécution",
            "Impact macro"
        ]
    },
    "un": {
        "nom": "Tableau de Bord ONU",
        "sections": [
            "Indice de développement humain",
            "Progrès ODD",
            "Indicateurs démographiques",
            "Urbanisation",
            "Commerce international",
            "Inégalités"
        ]
    },
    "worldbank": {
        "nom": "Tableau de Bord Banque Mondiale",
        "sections": [
            "Croissance et PIB",
            "Pauvreté",
            "Dépenses publiques",
            "Environnement des affaires",
            "Gouvernance",
            "Indicateurs sociaux"
        ]
    }
}

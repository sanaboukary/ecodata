#!/usr/bin/env python3
"""
Liste TOUS les indicateurs/datasets disponibles sur le FMI
pour les pays UEMOA
"""
import requests
import json
from datetime import datetime

# Pays UEMOA (codes ISO)
PAYS_UEMOA = {
    'BJ': 'Bénin',
    'BF': 'Burkina Faso', 
    'CI': "Côte d'Ivoire",
    'GW': 'Guinée-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Sénégal',
    'TG': 'Togo'
}

# Principaux datasets FMI
DATASETS_IMF = {
    'IFS': {
        'nom': 'International Financial Statistics (IFS)',
        'description': 'Statistiques financières internationales - Monnaie, taux de change, balance des paiements',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/IFS',
        'categories': [
            'Taux de change',
            'Réserves internationales',
            'Masse monétaire (M1, M2, M3)',
            'Taux d\'intérêt',
            'Prix à la consommation (CPI)',
            'Production industrielle',
            'Commerce extérieur',
            'Balance des paiements'
        ]
    },
    'DOT': {
        'nom': 'Direction of Trade Statistics (DOT)',
        'description': 'Statistiques de commerce extérieur - Importations/Exportations',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/DOT',
        'categories': [
            'Exportations totales',
            'Importations totales',
            'Balance commerciale',
            'Commerce par partenaire'
        ]
    },
    'BOP': {
        'nom': 'Balance of Payments (BOP)',
        'description': 'Balance des paiements - Transactions courantes et capital',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/BOP',
        'categories': [
            'Compte courant',
            'Compte de capital',
            'Investissements directs étrangers (IDE)',
            'Transferts de fonds',
            'Revenus primaires et secondaires'
        ]
    },
    'GFS': {
        'nom': 'Government Finance Statistics (GFS)',
        'description': 'Statistiques finances publiques - Budget gouvernemental',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/GFS',
        'categories': [
            'Revenus gouvernementaux',
            'Dépenses gouvernementales',
            'Déficit/Surplus budgétaire',
            'Dette publique',
            'Impôts et taxes'
        ]
    },
    'FSI': {
        'nom': 'Financial Soundness Indicators (FSI)',
        'description': 'Indicateurs solidité financière - Stabilité système bancaire',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/FSI',
        'categories': [
            'Ratio capital/actifs',
            'Prêts non performants',
            'Rentabilité bancaire (ROA, ROE)',
            'Liquidité bancaire'
        ]
    },
    'WEO': {
        'nom': 'World Economic Outlook (WEO)',
        'description': 'Perspectives économiques mondiales - Prévisions macroéconomiques',
        'url': 'https://www.imf.org/external/pubs/ft/weo/data/WEOapi.aspx',
        'categories': [
            'PIB et croissance',
            'Inflation',
            'Chômage',
            'Dette publique (% PIB)',
            'Balance courante (% PIB)',
            'Investissement (% PIB)'
        ]
    },
    'COFER': {
        'nom': 'Currency Composition of Official Foreign Exchange Reserves (COFER)',
        'description': 'Composition devises des réserves de change',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/COFER',
        'categories': [
            'Réserves en USD',
            'Réserves en EUR',
            'Réserves en autres devises'
        ]
    },
    'CDIS': {
        'nom': 'Coordinated Direct Investment Survey (CDIS)',
        'description': 'Enquête coordonnée sur les investissements directs',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/CDIS',
        'categories': [
            'IDE entrants par pays source',
            'IDE sortants par destination',
            'Stocks d\'IDE'
        ]
    },
    'CPIS': {
        'nom': 'Coordinated Portfolio Investment Survey (CPIS)',
        'description': 'Enquête coordonnée sur les investissements de portefeuille',
        'url': 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/CPIS',
        'categories': [
            'Investissements actions',
            'Investissements obligations',
            'Portefeuille par pays'
        ]
    }
}

# Indicateurs WEO principaux
INDICATEURS_WEO = {
    'NGDP_R': 'PIB réel',
    'NGDP_RPCH': 'Croissance du PIB réel (%)',
    'NGDP': 'PIB nominal (devises locales)',
    'NGDPD': 'PIB nominal (USD)',
    'NGDP_D': 'Déflateur du PIB',
    'NGDPRPC': 'PIB réel par habitant',
    'NGDPPC': 'PIB par habitant (USD)',
    'PCPI': 'Inflation (prix à la consommation, %)',
    'PCPIPCH': 'Variation inflation (%)',
    'PCPIE': 'Inflation (fin de période, %)',
    'LUR': 'Taux de chômage (%)',
    'BCA': 'Balance courante (milliards USD)',
    'BCA_NGDPD': 'Balance courante (% PIB)',
    'GGXWDG_NGDP': 'Dette publique brute (% PIB)',
    'GGXCNL_NGDP': 'Solde budgétaire net (% PIB)',
    'GGR_NGDP': 'Revenus gouvernementaux (% PIB)',
    'GGX_NGDP': 'Dépenses gouvernementales (% PIB)',
    'NID_NGDP': 'Investissement (% PIB)',
    'NGSD_NGDP': 'Épargne nationale brute (% PIB)',
    'TM_RPCH': 'Croissance importations (%)',
    'TX_RPCH': 'Croissance exportations (%)',
    'PPPPC': 'PIB par habitant (PPA, USD international)',
    'PPPEX': 'Taux de change PPA (monnaie locale par USD)',
}

def afficher_tous_les_datasets():
    """Affiche tous les datasets IMF disponibles"""
    print("\n" + "="*100)
    print("📊 DATASETS FMI DISPONIBLES POUR LES PAYS UEMOA")
    print("="*100)
    
    print(f"\n🌍 Pays UEMOA ({len(PAYS_UEMOA)}) :")
    for code, nom in PAYS_UEMOA.items():
        print(f"   • {code} : {nom}")
    
    print(f"\n📈 Datasets FMI disponibles ({len(DATASETS_IMF)}) :\n")
    
    for i, (code, info) in enumerate(DATASETS_IMF.items(), 1):
        print(f"\n{i}. {code} - {info['nom']}")
        print(f"   Description : {info['description']}")
        print(f"   URL : {info['url']}")
        print(f"   Catégories ({len(info['categories'])}) :")
        for cat in info['categories']:
            print(f"      • {cat}")
    
    print("\n" + "="*100)
    print("📋 INDICATEURS WEO DÉTAILLÉS")
    print("="*100)
    print(f"\nTotal : {len(INDICATEURS_WEO)} indicateurs\n")
    
    categories_weo = {
        'PIB & Croissance': ['NGDP_R', 'NGDP_RPCH', 'NGDP', 'NGDPD', 'NGDP_D', 'NGDPRPC', 'NGDPPC'],
        'Inflation': ['PCPI', 'PCPIPCH', 'PCPIE'],
        'Emploi': ['LUR'],
        'Balance extérieure': ['BCA', 'BCA_NGDPD', 'TM_RPCH', 'TX_RPCH'],
        'Finances publiques': ['GGXWDG_NGDP', 'GGXCNL_NGDP', 'GGR_NGDP', 'GGX_NGDP'],
        'Investissement & Épargne': ['NID_NGDP', 'NGSD_NGDP'],
        'Parité de pouvoir d\'achat': ['PPPPC', 'PPPEX']
    }
    
    for categorie, codes in categories_weo.items():
        print(f"\n{categorie} ({len(codes)}) :")
        for code in codes:
            print(f"   • {code:15} : {INDICATEURS_WEO[code]}")
    
    print("\n" + "="*100)
    print("📊 STATISTIQUES GLOBALES")
    print("="*100)
    
    total_categories = sum(len(info['categories']) for info in DATASETS_IMF.values())
    print(f"\n✓ {len(DATASETS_IMF)} datasets principaux")
    print(f"✓ {total_categories} catégories d'indicateurs")
    print(f"✓ {len(INDICATEURS_WEO)} indicateurs WEO détaillés")
    print(f"✓ {len(PAYS_UEMOA)} pays UEMOA couverts")
    print(f"✓ Période : 1960 - {datetime.now().year}")
    
    # Estimation nombre d'observations
    nb_annees = datetime.now().year - 1960 + 1
    estimation_obs_weo = len(INDICATEURS_WEO) * len(PAYS_UEMOA) * nb_annees
    
    print(f"\n📈 Estimation observations WEO : {estimation_obs_weo:,}")
    print(f"   ({len(INDICATEURS_WEO)} indicateurs × {len(PAYS_UEMOA)} pays × {nb_annees} années)")
    
    print("\n" + "="*100)
    print("🚀 COLLECTE RECOMMANDÉE")
    print("="*100)
    print("\nPriorité 1 (Essentiels macroéconomiques) :")
    print("   • WEO : NGDP_RPCH, PCPI, BCA_NGDPD, GGXWDG_NGDP, LUR")
    print("   • IFS : Taux de change, Réserves, CPI, Masse monétaire")
    
    print("\nPriorité 2 (Commerce & Investissement) :")
    print("   • DOT : Exportations/Importations")
    print("   • BOP : Compte courant, IDE")
    print("   • CDIS : IDE par pays")
    
    print("\nPriorité 3 (Finances publiques & Bancaires) :")
    print("   • GFS : Budget, Dette publique")
    print("   • FSI : Indicateurs bancaires")
    
    print("\n" + "="*100 + "\n")

def generer_code_collecte():
    """Génère le code Python pour collecter tous ces datasets"""
    print("\n" + "="*100)
    print("💻 CODE PYTHON POUR COLLECTE COMPLÈTE")
    print("="*100)
    
    code = '''
# COLLECTE WEO (World Economic Outlook) - PRIORITAIRE
INDICATEURS_WEO = [
    'NGDP_RPCH',      # Croissance PIB
    'PCPI',           # Inflation
    'BCA_NGDPD',      # Balance courante (% PIB)
    'GGXWDG_NGDP',    # Dette publique (% PIB)
    'LUR',            # Chômage
    'NGDPD',          # PIB nominal (USD)
    'NGDPPC',         # PIB par habitant
    'GGXCNL_NGDP',    # Solde budgétaire
    'NID_NGDP',       # Investissement
    'TM_RPCH',        # Croissance importations
    'TX_RPCH'         # Croissance exportations
]

PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

# Collecte WEO
for pays in PAYS_UEMOA:
    for indicateur in INDICATEURS_WEO:
        url = f"https://www.imf.org/external/datamapper/api/v1/{indicateur}/{pays}"
        # Collecter données 1960-2026
        ...

# Collecte IFS (Statistiques financières)
for pays in PAYS_UEMOA:
    # Taux de change
    # Réserves internationales
    # Masse monétaire
    # Prix à la consommation
    ...

# Collecte DOT (Commerce extérieur)
for pays in PAYS_UEMOA:
    # Exportations/Importations
    ...
'''
    
    print(code)
    print("="*100 + "\n")

def main():
    afficher_tous_les_datasets()
    generer_code_collecte()
    
    # Sauvegarder dans un fichier JSON
    output = {
        'date_generation': datetime.now().isoformat(),
        'pays_uemoa': PAYS_UEMOA,
        'datasets_imf': DATASETS_IMF,
        'indicateurs_weo': INDICATEURS_WEO
    }
    
    with open('indicateurs_imf_complets.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("✅ Liste complète sauvegardée dans : indicateurs_imf_complets.json\n")

if __name__ == '__main__':
    main()

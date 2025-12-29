#!/usr/bin/env python3
"""
Génère un template CSV pour importer 60 jours d'historique BRVM
Structure : DATE,SYMBOL,CLOSE,VOLUME,VARIATION
"""

from datetime import datetime, timedelta

# 43 actions principales BRVM
ACTIONS = [
    'ABJC.BC', 'BICC.BC', 'BOAB.BC', 'BOABF.BC', 'BOAC.BC',
    'BOAM.BC', 'CABC.BC', 'CFAC.BC', 'CIAC.BC', 'CIE.BC',
    'ECOC.BC', 'ETIT.BC', 'NEIC.BC', 'NSBC.BC', 'NTLC.BC',
    'ORGT.BC', 'SABC.BC', 'SCRC.BC', 'SDCC.BC', 'SDSC.BC',
    'SEMC.BC', 'SGBC.BC', 'SHEC.BC', 'SIBC.BC', 'SICC.BC',
    'SICB.BC', 'SIVC.BC', 'SLBC.BC', 'SMBC.BC', 'SNTS.BC',
    'SOGC.BC', 'STAC.BC', 'STBC.BC', 'SVOC.BC', 'ONTBF.BC',
    'PALC.BC', 'PRSC.BC', 'TTLC.BC', 'TTLS.BC', 'UNXC.BC',
    'FTSC.BC', 'UNLC.BC', 'BNBC.BC'
]

def generer_template_60j():
    """Génère template CSV pour 60 jours ouvrables"""
    
    print("=" * 80)
    print("GENERATION TEMPLATE HISTORIQUE BRVM - 60 JOURS")
    print("=" * 80)
    print()
    
    # Calculer 60 jours ouvrables en arrière
    dates_ouvrables = []
    date_actuelle = datetime.now()
    
    jours_ajoutes = 0
    delta = 0
    
    while jours_ajoutes < 60:
        date_test = date_actuelle - timedelta(days=delta)
        
        # Exclure weekends (samedi=5, dimanche=6)
        if date_test.weekday() < 5:
            dates_ouvrables.append(date_test.strftime('%Y-%m-%d'))
            jours_ajoutes += 1
        
        delta += 1
    
    # Inverser pour avoir du plus ancien au plus récent
    dates_ouvrables.reverse()
    
    print(f"Période: {dates_ouvrables[0]} → {dates_ouvrables[-1]}")
    print(f"Actions: {len(ACTIONS)}")
    print(f"Jours ouvrables: {len(dates_ouvrables)}")
    print(f"Total lignes: {len(ACTIONS) * len(dates_ouvrables):,}")
    print()
    
    # Générer CSV
    filename = 'historique_brvm_60jours_TEMPLATE.csv'
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Header
        f.write('DATE,SYMBOL,CLOSE,VOLUME,VARIATION\n')
        
        # Données (placeholders)
        for date in dates_ouvrables:
            for action in ACTIONS:
                # Placeholder - à remplacer par vraies données
                f.write(f'{date},{action},0,0,0.00\n')
    
    print(f"✅ Template généré: {filename}")
    print()
    print("=" * 80)
    print("COMMENT REMPLIR CE TEMPLATE")
    print("=" * 80)
    print()
    print("OPTION 1 - Bulletins PDF BRVM (RECOMMANDÉ)")
    print("  1. Télécharger 60 bulletins quotidiens BRVM:")
    print("     https://www.brvm.org/fr/publications/bulletins-quotidiens")
    print("  2. Sauvegarder dans dossier: bulletins_brvm/")
    print("  3. Parser automatiquement:")
    print("     python parser_bulletins_brvm_pdf.py")
    print()
    print("OPTION 2 - API/Scraping (si disponible)")
    print("  1. Vérifier si API historique BRVM existe")
    print("  2. Adapter brvm_scraper_production.py pour historique")
    print()
    print("OPTION 3 - Saisie manuelle (long)")
    print("  1. Ouvrir Excel/LibreOffice")
    print("  2. Remplir progressivement depuis site BRVM")
    print("  3. Remplacer les '0' par vraies valeurs")
    print()
    print("OPTION 4 - Utiliser données existantes (si disponible)")
    print("  1. Vérifier MongoDB pour données REAL_SCRAPER")
    print("  2. Exporter et compléter manquants")
    print()
    print("IMPORT APRÈS REMPLISSAGE:")
    print("  python collecter_csv_automatique.py --dossier .")
    print()
    print("=" * 80)

if __name__ == '__main__':
    generer_template_60j()

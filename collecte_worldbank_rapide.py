#!/usr/bin/env python3
"""
Collecte rapide des données de la Banque Mondiale
Collecte les principaux indicateurs pour les pays de l'UEMOA
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from scripts.pipeline import run_ingestion

# Pays de l'UEMOA et quelques autres pays africains
PAYS = [
    "BJ",  # Bénin
    "BF",  # Burkina Faso
    "CI",  # Côte d'Ivoire
    "GW",  # Guinée-Bissau
    "ML",  # Mali
    "NE",  # Niger
    "SN",  # Sénégal
    "TG",  # Togo
]

# Indicateurs économiques clés
INDICATEURS = {
    "SP.POP.TOTL": "Population totale",
    "NY.GDP.MKTP.CD": "PIB (USD courant)",
    "NY.GDP.PCAP.CD": "PIB par habitant (USD)",
    "NY.GDP.MKTP.KD.ZG": "Croissance du PIB (%)",
    "FP.CPI.TOTL.ZG": "Inflation, prix à la consommation (%)",
    "SL.UEM.TOTL.ZS": "Taux de chômage (%)",
    "NE.EXP.GNFS.ZS": "Exportations (% du PIB)",
    "NE.IMP.GNFS.ZS": "Importations (% du PIB)",
    "GC.DOD.TOTL.GD.ZS": "Dette publique (% du PIB)",
    "NY.GDS.TOTL.ZS": "Épargne brute nationale (% du PIB)",
    "SE.PRM.ENRR": "Taux de scolarisation primaire (%)",
    "SE.SEC.ENRR": "Taux de scolarisation secondaire (%)",
    "SH.DYN.MORT": "Taux de mortalité infantile (pour 1000)",
    "SP.DYN.LE00.IN": "Espérance de vie à la naissance (années)",
    "EG.ELC.ACCS.ZS": "Accès à l'électricité (% de la population)",
    "SI.POV.GINI": "Indice de Gini",
    "IT.NET.USER.ZS": "Utilisateurs Internet (% de la pop.)",
    "EN.ATM.CO2E.PC": "Émissions de CO2 (tonnes par habitant)",
}

def collect_worldbank_data():
    """Collecte les données de la Banque Mondiale"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║              COLLECTE DES DONNÉES DE LA BANQUE MONDIALE                        ║
║                         Pays UEMOA + Afrique                                   ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 {len(INDICATEURS)} indicateurs à collecter")
    print(f"🌍 {len(PAYS)} pays ciblés")
    print(f"{'='*80}\n")
    
    total_observations = 0
    indicateurs_reussis = 0
    indicateurs_echoues = 0
    
    for idx, (code, nom) in enumerate(INDICATEURS.items(), 1):
        print(f"\n[{idx}/{len(INDICATEURS)}] 📊 {nom}")
        print(f"    Code: {code}")
        
        try:
            # Collecter pour tous les pays de la liste
            pays_str = ";".join(PAYS)
            count = run_ingestion(
                "worldbank",
                indicator=code,
                date="2010:2024",  # Dernières 14 années
                country=pays_str
            )
            
            total_observations += count
            indicateurs_reussis += 1
            print(f"    ✅ {count} observations collectées")
            
        except Exception as e:
            indicateurs_echoues += 1
            print(f"    ❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"\n📊 RÉSUMÉ DE LA COLLECTE:")
    print(f"   ✅ Indicateurs réussis  : {indicateurs_reussis}/{len(INDICATEURS)}")
    print(f"   ❌ Indicateurs échoués  : {indicateurs_echoues}/{len(INDICATEURS)}")
    print(f"   📈 Total observations   : {total_observations}")
    print(f"\n{'='*80}\n")
    
    return total_observations

if __name__ == "__main__":
    try:
        total = collect_worldbank_data()
        print(f"\n✅ Collecte terminée avec succès !")
        print(f"📊 {total} observations insérées dans MongoDB\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Collecte interrompue par l'utilisateur\n")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}\n")
        import traceback
        traceback.print_exc()

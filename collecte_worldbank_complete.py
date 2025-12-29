#!/usr/bin/env python3
"""
Collecte complète WorldBank - TOUS LES PAYS - TOUS LES INDICATEURS
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion

# Liste COMPLÈTE des indicateurs (80+)
indicators = [
    # DÉMOGRAPHIE
    "SP.POP.TOTL",          # Population totale
    "SP.POP.GROW",          # Croissance démographique
    "SP.URB.TOTL.IN.ZS",    # Population urbaine (%)
    "SP.RUR.TOTL.ZS",       # Population rurale (%)
    "SP.DYN.LE00.IN",       # Espérance de vie
    "SP.DYN.TFRT.IN",       # Taux de fécondité
    "SP.POP.0014.TO.ZS",    # Population 0-14 ans (%)
    "SP.POP.1564.TO.ZS",    # Population 15-64 ans (%)
    "SP.POP.65UP.TO.ZS",    # Population 65+ ans (%)
    
    # ÉCONOMIE - PIB
    "NY.GDP.MKTP.CD",       # PIB ($ courants)
    "NY.GDP.MKTP.KD",       # PIB ($ constants)
    "NY.GDP.MKTP.KD.ZG",    # Croissance du PIB (%)
    "NY.GDP.PCAP.CD",       # PIB par habitant ($ courants)
    "NY.GDP.PCAP.KD",       # PIB par habitant ($ constants)
    "NY.GDP.PCAP.KD.ZG",    # Croissance PIB par habitant
    "NY.GNP.MKTP.CD",       # RNB ($ courants)
    "NY.GNP.PCAP.CD",       # RNB par habitant ($ courants)
    "NY.GNP.PCAP.PP.CD",    # RNB par habitant (PPA)
    
    # PAUVRETÉ & INÉGALITÉS
    "SI.POV.DDAY",          # Pauvreté $1.90/jour (%)
    "SI.POV.LMIC",          # Pauvreté $3.20/jour (%)
    "SI.POV.UMIC",          # Pauvreté $5.50/jour (%)
    "SI.POV.GINI",          # Indice de Gini
    "SI.POV.NAHC",          # Seuil de pauvreté national
    
    # EMPLOI & CHÔMAGE
    "SL.UEM.TOTL.ZS",       # Chômage total (%)
    "SL.UEM.1524.ZS",       # Chômage jeunes 15-24 ans
    "SL.TLF.TOTL.IN",       # Population active
    "SL.TLF.CACT.ZS",       # Taux d'activité
    "SL.AGR.EMPL.ZS",       # Emploi agriculture (%)
    "SL.IND.EMPL.ZS",       # Emploi industrie (%)
    "SL.SRV.EMPL.ZS",       # Emploi services (%)
    
    # INFLATION & PRIX
    "FP.CPI.TOTL.ZG",       # Inflation (%)
    "FP.CPI.TOTL",          # Indice des prix consommation
    "NY.GDP.DEFL.KD.ZG",    # Déflateur du PIB
    
    # COMMERCE EXTÉRIEUR
    "NE.EXP.GNFS.ZS",       # Exportations (% PIB)
    "NE.IMP.GNFS.ZS",       # Importations (% PIB)
    "NE.TRD.GNFS.ZS",       # Commerce (% PIB)
    "BN.CAB.XOKA.GD.ZS",    # Balance courante (% PIB)
    "BX.KLT.DINV.WD.GD.ZS", # IDE entrants (% PIB)
    "DT.ODA.ODAT.GD.ZS",    # Aide reçue (% RNB)
    
    # DETTE & FINANCES PUBLIQUES
    "GC.DOD.TOTL.GD.ZS",    # Dette publique (% PIB)
    "GC.XPN.TOTL.GD.ZS",    # Dépenses publiques (% PIB)
    "GC.REV.XGRT.GD.ZS",    # Recettes publiques (% PIB)
    "GC.BAL.CASH.GD.ZS",    # Solde budgétaire (% PIB)
    
    # ÉDUCATION
    "SE.PRM.ENRR",          # Taux de scolarisation primaire
    "SE.SEC.ENRR",          # Taux de scolarisation secondaire
    "SE.TER.ENRR",          # Taux de scolarisation tertiaire
    "SE.ADT.LITR.ZS",       # Taux d'alphabétisation adultes
    "SE.XPD.TOTL.GD.ZS",    # Dépenses éducation (% PIB)
    "SE.PRM.CMPT.ZS",       # Taux achèvement primaire
    "SE.SEC.CMPT.LO.ZS",    # Taux achèvement secondaire
    
    # SANTÉ
    "SH.DYN.MORT",          # Mortalité infantile (pour 1000)
    "SH.DYN.NMRT",          # Mortalité néonatale
    "SH.STA.MMRT",          # Mortalité maternelle
    "SH.MED.BEDS.ZS",       # Lits d'hôpital (pour 1000)
    "SH.MED.PHYS.ZS",       # Médecins (pour 1000)
    "SH.XPD.CHEX.GD.ZS",    # Dépenses santé courantes (% PIB)
    "SH.XPD.GHED.GD.ZS",    # Dépenses santé publiques (% PIB)
    "SH.IMM.MEAS",          # Vaccination rougeole (%)
    "SH.H2O.BASW.ZS",       # Accès eau potable (%)
    "SH.STA.BASS.ZS",       # Accès assainissement (%)
    
    # ÉNERGIE & ENVIRONNEMENT
    "EG.ELC.ACCS.ZS",       # Accès à l'électricité (%)
    "EG.USE.ELEC.KH.PC",    # Consommation électricité par hab
    "EG.USE.PCAP.KG.OE",    # Consommation énergie par hab
    "EN.ATM.CO2E.PC",       # Émissions CO2 par habitant
    "EN.ATM.CO2E.KT",       # Émissions CO2 totales
    "AG.LND.FRST.ZS",       # Surface forestière (%)
    "ER.H2O.FWTL.K3",       # Prélèvements eau douce
    
    # AGRICULTURE
    "AG.LND.AGRI.ZS",       # Terres agricoles (%)
    "AG.YLD.CREL.KG",       # Rendement céréales (kg/ha)
    "AG.PRD.FOOD.XD",       # Indice production alimentaire
    "NV.AGR.TOTL.ZS",       # Agriculture (% PIB)
    
    # INDUSTRIE & SERVICES
    "NV.IND.TOTL.ZS",       # Industrie (% PIB)
    "NV.IND.MANF.ZS",       # Manufacture (% PIB)
    "NV.SRV.TOTL.ZS",       # Services (% PIB)
    
    # TECHNOLOGIE & INNOVATION
    "IT.NET.USER.ZS",       # Utilisateurs internet (%)
    "IT.CEL.SETS.P2",       # Abonnements mobile (pour 100)
    "GB.XPD.RSDV.GD.ZS",    # R&D (% PIB)
    "IP.PAT.RESD",          # Demandes de brevets
    
    # INFRASTRUCTURE
    "IS.ROD.PAVE.ZP",       # Routes pavées (%)
    "IS.AIR.DPRT",          # Départs aériens
    "IT.MLT.MAIN.P2",       # Lignes téléphoniques fixes
]

print(f"\n{'='*80}")
print(f"    ╔════════════════════════════════════════════════════════════════╗")
print(f"    ║                                                                ║")
print(f"    ║    COLLECTE BANQUE MONDIALE - TOUS LES PAYS DU MONDE          ║")
print(f"    ║                                                                ║")
print(f"    ╚════════════════════════════════════════════════════════════════╝")
print(f"{'='*80}")
print(f"\n📊 Configuration:")
print(f"   - Indicateurs: {len(indicators)}")
print(f"   - Pays: TOUS (world='all')")
print(f"   - Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n⏱️  Durée estimée: 15-30 minutes")
print(f"{'='*80}\n")

total = 0
success = 0
failed = 0
start_time = datetime.now()

for i, indicator in enumerate(indicators, 1):
    try:
        print(f"[{i:2d}/{len(indicators)}] {indicator:30s} ", end="", flush=True)
        count = run_ingestion("worldbank", indicator=indicator, country="all")
        print(f"✅ {count:,} obs")
        total += count
        success += 1
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        failed += 1

duration = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*80}")
print(f"📊 RÉSUMÉ DE LA COLLECTE")
print(f"{'='*80}")
print(f"✅ Succès:       {success:3d}/{len(indicators)} indicateurs")
print(f"❌ Échecs:       {failed:3d}/{len(indicators)} indicateurs")
print(f"📈 Total obs:    {total:,} observations")
print(f"⏱️  Durée:        {duration/60:.1f} minutes")
print(f"🌍 Pays:         TOUS LES PAYS DU MONDE")
print(f"📅 Complété:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

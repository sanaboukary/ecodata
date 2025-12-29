#!/usr/bin/env python3
"""
Script d'automatisation de la collecte de données
Utilise APScheduler pour orchestrer toutes les sources
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Ajouter le répertoire scripts au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

# Import des connecteurs
from scripts.pipeline import run_ingestion

def collect_brvm():
    """Collecte des données BRVM - 47 actions"""
    print(f"\n{'='*80}")
    print(f"🏦 BRVM - Collecte des 47 actions cotées")
    print(f"{'='*80}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        count = run_ingestion("brvm")
        print(f"✅ BRVM: {count} observations collectées")
        return count
    except Exception as e:
        print(f"❌ Erreur BRVM: {e}")
        return 0

def collect_worldbank():
    """Collecte des données WorldBank - TOUS LES PAYS - 80+ indicateurs"""
    print(f"\n{'='*80}")
    print(f"🌍 WORLDBANK - Collecte des indicateurs économiques (TOUS LES PAYS)")
    print(f"{'='*80}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Liste COMPLÈTE des indicateurs WorldBank - TOUS LES PAYS DU MONDE
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
    
    print(f"📊 Collecte de {len(indicators)} indicateurs pour TOUS LES PAYS du monde...")
    print(f"⏱️  Cela peut prendre plusieurs minutes...\n")
    
    total = 0
    success = 0
    failed = 0
    
    for i, indicator in enumerate(indicators, 1):
        try:
            print(f"[{i}/{len(indicators)}] {indicator}...", end=" ")
            count = run_ingestion("worldbank", indicator=indicator, country="all")
            print(f"✅ {count} observations")
            total += count
            success += 1
        except Exception as e:
            print(f"❌ Erreur: {e}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"📊 RÉSUMÉ WORLDBANK:")
    print(f"   ✅ Succès: {success}/{len(indicators)} indicateurs")
    print(f"   ❌ Échecs: {failed}/{len(indicators)} indicateurs")
    print(f"   📈 Total: {total:,} observations collectées")
    print(f"   🌍 Pays: TOUS LES PAYS DU MONDE")
    print(f"{'='*80}\n")
    
    return total

def collect_imf():
    """Collecte des données IMF - 20+ séries"""
    print(f"\n{'='*80}")
    print(f"💰 IMF - Collecte des séries économiques")
    print(f"{'='*80}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Séries IMF principales
    series = [
        "PCPI_IX",          # Inflation
        "NGDP_RPCH",        # Croissance PIB réel
        "NGDPD",            # PIB nominal
        "NGDPDPC",          # PIB par habitant
        "LUR",              # Taux de chômage
        "BCA_NGDPD",        # Balance des comptes courants
        "GGXWDG_NGDP",      # Dette publique
        "ENDA_NGDPD",       # Réserves de change
    ]
    
    total = 0
    for serie in series:
        try:
            count = run_ingestion("imf", series_code=serie)
            print(f"✅ {serie}: {count} observations")
            total += count
        except Exception as e:
            print(f"❌ Erreur {serie}: {e}")
    
    return total

def collect_afdb():
    """Collecte des données AfDB - 6 indicateurs × 8 pays"""
    print(f"\n{'='*80}")
    print(f"🌍 AFDB - Collecte des indicateurs de développement")
    print(f"{'='*80}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        count = run_ingestion("afdb")
        print(f"✅ AfDB: {count} observations collectées")
        return count
    except Exception as e:
        print(f"❌ Erreur AfDB: {e}")
        return 0

def collect_un_sdg():
    """Collecte des données UN SDG - 8 séries ODD"""
    print(f"\n{'='*80}")
    print(f"🎯 UN SDG - Collecte des Objectifs de Développement Durable")
    print(f"{'='*80}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        count = run_ingestion("un_sdg")
        print(f"✅ UN SDG: {count} observations collectées")
        return count
    except Exception as e:
        print(f"❌ Erreur UN SDG: {e}")
        return 0

def show_status():
    """Affiche le statut de la collecte"""
    print(f"\n{'='*80}")
    print(f"📊 STATUT DE LA COLLECTE AUTOMATIQUE")
    print(f"{'='*80}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nProchaines exécutions programmées:")
    print(f"  🏦 BRVM         : Toutes les heures (9h-16h, lun-ven)")
    print(f"  🌍 WorldBank   : Mi-mensuel (15 de chaque mois)")
    print(f"  💰 IMF         : Mensuel (1er de chaque mois)")
    print(f"  🌍 AfDB        : Trimestriel (Jan/Avr/Jul/Oct)")
    print(f"  🎯 UN SDG      : Trimestriel (Jan/Avr/Jul/Oct)")
    print(f"{'='*80}\n")

def main():
    """Lance le scheduler avec toutes les tâches"""
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║        SYSTÈME DE COLLECTE AUTOMATIQUE DE DONNÉES                             ║
║                 Plateforme de Centralisation                                  ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    scheduler = BlockingScheduler()
    
    # BRVM - Toutes les heures pendant les heures de marché (9h-16h, lun-ven)
    scheduler.add_job(
        collect_brvm,
        trigger=CronTrigger(
            day_of_week='mon-fri',
            hour='9-16',
            minute='0'
        ),
        id='brvm_hourly',
        name='BRVM - 47 actions (horaire)',
        max_instances=1
    )
    
    # WorldBank - Mi-mensuel (15 de chaque mois à 2h)
    scheduler.add_job(
        collect_worldbank,
        trigger=CronTrigger(
            day='15',
            hour='2',
            minute='0'
        ),
        id='worldbank_monthly',
        name='WorldBank - 35+ indicateurs (mensuel)',
        max_instances=1
    )
    
    # IMF - Mensuel (1er de chaque mois à 2h30)
    scheduler.add_job(
        collect_imf,
        trigger=CronTrigger(
            day='1',
            hour='2',
            minute='30'
        ),
        id='imf_monthly',
        name='IMF - 20+ séries (mensuel)',
        max_instances=1
    )
    
    # AfDB - Trimestriel (Jan/Avr/Jul/Oct à 3h)
    scheduler.add_job(
        collect_afdb,
        trigger=CronTrigger(
            month='1,4,7,10',
            day='1',
            hour='3',
            minute='0'
        ),
        id='afdb_quarterly',
        name='AfDB - 48 séries (trimestriel)',
        max_instances=1
    )
    
    # UN SDG - Trimestriel (Jan/Avr/Jul/Oct à 3h15)
    scheduler.add_job(
        collect_un_sdg,
        trigger=CronTrigger(
            month='1,4,7,10',
            day='1',
            hour='3',
            minute='15'
        ),
        id='un_sdg_quarterly',
        name='UN SDG - 8 séries (trimestriel)',
        max_instances=1
    )
    
    # Affichage du statut toutes les heures
    scheduler.add_job(
        show_status,
        trigger=IntervalTrigger(hours=1),
        id='status_display',
        name='Affichage du statut',
        max_instances=1
    )
    
    # Collecte immédiate au démarrage pour tester
    print("🚀 Lancement d'une collecte de test...")
    collect_brvm()
    
    show_status()
    
    print("✅ Scheduler démarré et en attente des tâches programmées...")
    print("💡 Appuyez sur Ctrl+C pour arrêter\n")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n\n🛑 Arrêt du scheduler...")
        scheduler.shutdown()
        print("✅ Scheduler arrêté proprement")

if __name__ == "__main__":
    main()

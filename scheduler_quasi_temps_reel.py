#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Quasi Temps Réel BRVM
Scanne automatiquement le dossier CSV toutes les 15 minutes et importe les nouvelles données
Les utilisateurs voient les mises à jour avec un délai maximum de 15-30 minutes

UTILISATION:
- Développement: python scheduler_quasi_temps_reel.py
- Production: start_scheduler_quasi_temps_reel.bat (background)
"""

import os
import sys
import time
import schedule
from datetime import datetime, time as dt_time
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from collecter_csv_automatique import CollecteurCSV

class SchedulerQuasiTempsReel:
    """Scheduler pour collecte quasi temps réel"""
    
    def __init__(self):
        self.collecteur = CollecteurCSV()
        self.log_file = 'scheduler_temps_reel.log'
        self.heures_marche = (9, 17)  # 9h à 17h
    
    def log(self, message):
        """Logger avec timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def est_heure_marche(self):
        """Vérifie si on est pendant les heures de marché"""
        now = datetime.now()
        
        # Lundi à Vendredi uniquement
        if now.weekday() >= 5:  # Samedi=5, Dimanche=6
            return False
        
        # Entre 9h et 17h
        heure_actuelle = now.hour
        return self.heures_marche[0] <= heure_actuelle < self.heures_marche[1]
    
    def verifier_et_importer(self):
        """Vérifie si nouvelles données CSV et les importe"""
        self.log("🔍 Vérification nouvelles données BRVM...")
        
        # Vérifier si pendant heures de marché
        if not self.est_heure_marche():
            self.log("⏸️  Hors heures de marché - Attente")
            return
        
        try:
            # Chercher fichiers CSV récents (modifiés dans les 20 dernières minutes)
            import glob
            from datetime import timedelta
            
            dossiers = ['./csv', './data', './historique', '.']
            fichiers_recents = []
            seuil_temps = datetime.now() - timedelta(minutes=20)
            
            for dossier in dossiers:
                if os.path.exists(dossier):
                    csvs = glob.glob(os.path.join(dossier, '*.csv'))
                    for csv_file in csvs:
                        mtime = datetime.fromtimestamp(os.path.getmtime(csv_file))
                        if mtime > seuil_temps:
                            fichiers_recents.append(csv_file)
            
            if not fichiers_recents:
                self.log("  ℹ️  Aucun nouveau fichier CSV détecté")
                return
            
            self.log(f"  📂 {len(fichiers_recents)} fichier(s) CSV récent(s) détecté(s)")
            
            # Importer les fichiers
            total_imported = 0
            for csv_file in fichiers_recents:
                self.log(f"  📥 Import: {os.path.basename(csv_file)}")
                
                try:
                    # Traiter le fichier
                    rows_data = self.collecteur.lire_csv(csv_file)
                    if rows_data:
                        type_csv = self.collecteur.detecter_type_csv(csv_file)
                        observations = self.collecteur.preparer_observations(rows_data, type_csv)
                        
                        if observations:
                            count = self.collecteur.inserer_mongodb(observations)
                            total_imported += count
                            self.log(f"    ✅ {count} observations importées")
                        
                        # Archiver le fichier (renommer avec timestamp)
                        archive_name = f"{csv_file}.imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        os.rename(csv_file, archive_name)
                        self.log(f"    📦 Archivé: {os.path.basename(archive_name)}")
                        
                except Exception as e:
                    self.log(f"    ❌ Erreur import {csv_file}: {str(e)}")
            
            if total_imported > 0:
                self.log(f"✅ Total importé: {total_imported} observations")
                self.mettre_a_jour_timestamp()
            
        except Exception as e:
            self.log(f"❌ Erreur vérification: {str(e)}")
    
    def mettre_a_jour_timestamp(self):
        """Mettre à jour le timestamp de dernière mise à jour"""
        try:
            client, db = get_mongo_db()
            meta_collection = db.system_metadata
            
            meta_collection.update_one(
                {'type': 'last_update'},
                {
                    '$set': {
                        'type': 'last_update',
                        'source': 'BRVM',
                        'timestamp': datetime.utcnow(),
                        'timestamp_local': datetime.now().isoformat()
                    }
                },
                upsert=True
            )
            
            self.log("  🕐 Timestamp mis à jour")
            
        except Exception as e:
            self.log(f"  ⚠️  Erreur màj timestamp: {str(e)}")
    
    def demarrer(self):
        """Démarrer le scheduler"""
        self.log("\n" + "="*70)
        self.log("🚀 DÉMARRAGE SCHEDULER QUASI TEMPS RÉEL")
        self.log("="*70)
        self.log(f"⏰ Fréquence: Toutes les 15 minutes")
        self.log(f"🕐 Heures marché: {self.heures_marche[0]}h-{self.heures_marche[1]}h (Lun-Ven)")
        self.log(f"📂 Dossiers surveillés: ./csv, ./data, ./historique")
        self.log("="*70 + "\n")
        
        # Planifier la tâche toutes les 15 minutes
        schedule.every(15).minutes.do(self.verifier_et_importer)
        
        # Vérification immédiate au démarrage
        self.verifier_et_importer()
        
        # Boucle infinie
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier chaque minute
                
        except KeyboardInterrupt:
            self.log("\n" + "="*70)
            self.log("⏹️  ARRÊT DU SCHEDULER")
            self.log("="*70 + "\n")


def main():
    """Point d'entrée principal"""
    scheduler = SchedulerQuasiTempsReel()
    scheduler.demarrer()


if __name__ == "__main__":
    main()

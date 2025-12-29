#!/usr/bin/env python3
"""
Script pour insérer des données d'exemple WorldBank pour les secteurs Éducation, Santé et Infrastructure.
"""
import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Définition des indicateurs par secteur
indicators = {
    # Éducation
    "SE.PRM.ENRR": ("Taux de scolarisation primaire", 75, 95),
    "SE.SEC.ENRR": ("Taux de scolarisation secondaire", 45, 75),
    "SE.ADT.LITR.ZS": ("Taux d'alphabétisation des adultes", 60, 95),
    "SE.XPD.TOTL.GD.ZS": ("Dépenses publiques en éducation (% PIB)", 3, 7),
    
    # Santé
    "SP.DYN.LE00.IN": ("Espérance de vie à la naissance", 55, 75),
    "SH.XPD.CHEX.GD.ZS": ("Dépenses de santé (% PIB)", 4, 10),
    "SH.MED.PHYS.ZS": ("Médecins pour 1000 habitants", 0.1, 2.5),
    "SH.STA.MMRT": ("Taux de mortalité maternelle (pour 100k)", 150, 600),
    
    # Infrastructure
    "EG.ELC.ACCS.ZS": ("Accès à l'électricité (% population)", 40, 95),
    "IT.NET.USER.ZS": ("Utilisateurs Internet (% population)", 15, 70),
    "IT.CEL.SETS.P2": ("Abonnements téléphonie mobile (pour 100 habitants)", 70, 140),
    "SH.H2O.SMDW.ZS": ("Accès à l'eau potable (% population)", 50, 90),
}

# Pays d'Afrique de l'Ouest (zone BRVM étendue)
countries = [
    "Côte d'Ivoire",
    "Sénégal",
    "Burkina Faso",
    "Mali",
    "Bénin",
    "Togo",
    "Niger",
    "Guinée-Bissau",
    "Ghana",
    "Nigeria"
]

print(f"🌍 Insertion de données WorldBank pour {len(indicators)} indicateurs et {len(countries)} pays...")

# Générer des observations pour les 3 dernières années
inserted_count = 0
now = datetime.now()

for indicator_code, (indicator_name, min_val, max_val) in indicators.items():
    for country in countries:
        # Valeur de base aléatoire pour ce pays
        base_value = random.uniform(min_val, max_val)
        
        # Générer des observations mensuelles pour les 36 derniers mois
        for months_ago in range(36, 0, -1):
            # Légère variation autour de la valeur de base (tendance croissante légère)
            trend = months_ago * 0.002  # Tendance d'amélioration au fil du temps
            variation = random.uniform(-0.05, 0.05)  # Variation aléatoire ±5%
            
            # Pour la mortalité maternelle, la tendance doit être décroissante
            if indicator_code == "SH.STA.MMRT":
                value = base_value * (1 + trend + variation)
            else:
                value = base_value * (1 - trend + variation)
            
            # S'assurer que la valeur reste dans les bornes
            value = max(min_val * 0.8, min(max_val * 1.2, value))
            
            ts = (now - timedelta(days=months_ago * 30)).strftime("%Y-%m-%d")
            
            observation = {
                "source": "WorldBank",
                "dataset": indicator_code,
                "key": country,
                "indicator": indicator_code,
                "ts": ts,
                "value": round(value, 2),
                "metadata": {
                    "country": country,
                    "indicator_name": indicator_name,
                    "unit": "percent" if indicator_code.endswith("ZS") else "value"
                },
                "created_at": datetime.now()
            }
            
            db.curated_observations.insert_one(observation)
            inserted_count += 1

print(f"✅ {inserted_count} observations insérées avec succès!")

# Vérification
total_wb = db.curated_observations.count_documents({"source": "WorldBank"})
print(f"📊 Total d'observations WorldBank dans la base: {total_wb}")

# Afficher un échantillon par secteur
print("\n📚 Échantillon ÉDUCATION:")
edu_sample = db.curated_observations.find_one({"indicator": "SE.PRM.ENRR"})
if edu_sample:
    print(f"  {edu_sample['indicator']}: {edu_sample['value']} ({edu_sample['metadata']['country']}, {edu_sample['ts']})")

print("\n🏥 Échantillon SANTÉ:")
health_sample = db.curated_observations.find_one({"indicator": "SP.DYN.LE00.IN"})
if health_sample:
    print(f"  {health_sample['indicator']}: {health_sample['value']} ({health_sample['metadata']['country']}, {health_sample['ts']})")

print("\n🏗️ Échantillon INFRASTRUCTURE:")
infra_sample = db.curated_observations.find_one({"indicator": "EG.ELC.ACCS.ZS"})
if infra_sample:
    print(f"  {infra_sample['indicator']}: {infra_sample['value']} ({infra_sample['metadata']['country']}, {infra_sample['ts']})")

print("\n🎉 Données WorldBank prêtes pour le dashboard!")

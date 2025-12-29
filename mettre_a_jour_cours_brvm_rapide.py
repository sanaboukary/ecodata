"""
📋 MISE À JOUR RAPIDE DES COURS BRVM RÉELS
=========================================

INSTRUCTIONS:
1. Allez sur https://www.brvm.org/fr/investir/cours-et-cotations
2. Notez les cours de clôture du jour
3. Remplissez le dictionnaire ci-dessous avec les VRAIS prix
4. Exécutez: python mettre_a_jour_cours_brvm_rapide.py

⚠️ IMPORTANT: Remplacez TOUS les prix ci-dessous par les vrais cours BRVM !
"""
import sys
import os
import django
from datetime import datetime, timezone

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# ============================================================================
# 📝 REMPLISSEZ ICI LES VRAIS COURS BRVM DU JOUR
# ============================================================================
# Date de mise à jour: ___________
# Source: https://www.brvm.org ou bulletin officiel

COURS_BRVM_AUJOURDHUI = {
    # ⚠️ REMPLACEZ CES VALEURS PAR LES VRAIS COURS !
    
    # BANQUES (format: 'SYMBOL': prix_de_cloture)
    'BICC': 0,      # BICICI - Prix réel: _______ FCFA
    'BOAB': 0,      # BOA Bénin - Prix réel: _______ FCFA
    'BOABF': 0,     # BOA Burkina Faso - Prix réel: _______ FCFA
    'BOAC': 0,      # BOA Côte d'Ivoire - Prix réel: _______ FCFA
    'BOAG': 0,      # BOA Mali - Prix réel: _______ FCFA
    'BOAM': 0,      # BOA Niger - Prix réel: _______ FCFA
    'BOAN': 0,      # BOA Sénégal - Prix réel: _______ FCFA
    'BOAS': 0,      # BOA Togo - Prix réel: _______ FCFA
    'CABC': 0,      # Coris Bank International - Prix réel: _______ FCFA
    'CBIBF': 0,     # Coris Bank BF - Prix réel: _______ FCFA
    'ECOC': 0,      # Ecobank CI - Prix réel: _______ FCFA
    'ETIT': 0,      # Ecobank Transnational - Prix réel: _______ FCFA
    'SGBC': 0,      # Société Générale Bénin - Prix réel: _______ FCFA
    'SIBC': 0,      # SIB CI - Prix réel: _______ FCFA
    'NSIAC': 0,     # NSIA Banque CI - Prix réel: _______ FCFA
    
    # ASSURANCES
    'NSIAS': 0,     # NSIA Assurances - Prix réel: _______ FCFA
    'CFAC': 0,      # CFA Assurances - Prix réel: _______ FCFA
    
    # TÉLÉCOMMUNICATIONS
    'SNTS': 0,      # Sonatel - Prix réel: _______ FCFA
    'ORGT': 0,      # Orange CI - Prix réel: _______ FCFA
    'ONTBF': 0,     # ONATEL BF - Prix réel: _______ FCFA
    
    # DISTRIBUTION
    'NTLC': 0,      # NEI-CEDA - Prix réel: _______ FCFA
    'NEIC': 0,      # NEI-CEDA CI - Prix réel: _______ FCFA
    'UNLC': 0,      # Unilever CI - Prix réel: _______ FCFA
    'UNLB': 0,      # Unilever Bénin - Prix réel: _______ FCFA
    'TTLS': 0,      # Total Sénégal - Prix réel: _______ FCFA
    'TTLC': 0,      # Total CI - Prix réel: _______ FCFA
    'VRAC': 0,      # Vivo Energy CI - Prix réel: _______ FCFA
    'PRSC': 0,      # Tractafric Motors - Prix réel: _______ FCFA
    'SVOC': 0,      # Servair Abidjan - Prix réel: _______ FCFA
    
    # AGRICULTURE
    'PALC': 0,      # Palm CI - Prix réel: _______ FCFA
    'SCRC': 0,      # Sucrivoire - Prix réel: _______ FCFA
    'SDCC': 0,      # SODE CI - Prix réel: _______ FCFA
    'SPHC': 0,      # SAPH CI - Prix réel: _______ FCFA
    'FTSC': 0,      # Filtisac - Prix réel: _______ FCFA
    'TTRC': 0,      # Trituraf CI - Prix réel: _______ FCFA
    'SLBC': 0,      # Sté Libérienne Bois - Prix réel: _______ FCFA
    'SMBC': 0,      # SMB CI - Prix réel: _______ FCFA
    
    # INDUSTRIE/ÉNERGIE
    'SIVC': 0,      # Air Liquide CI - Prix réel: _______ FCFA
    'SNHC': 0,      # Sté Nationale Hydrocarbures - Prix réel: _______ FCFA
    'STBC': 0,      # Sitab CI - Prix réel: _______ FCFA
    'SEMC': 0,      # Crown SIEM CI - Prix réel: _______ FCFA
    'SICC': 0,      # SICOR CI - Prix réel: _______ FCFA
    'SOGC': 0,      # SOGB CI - Prix réel: _______ FCFA
    'STAC': 0,      # SETAO CI - Prix réel: _______ FCFA
    
    # SERVICES FINANCIERS
    'SAFC': 0,      # SAFCA - Prix réel: _______ FCFA
    'ABJC': 0,      # Bernabé CI - Prix réel: _______ FCFA
}

def mettre_a_jour_avec_vrais_prix():
    """Met à jour la base avec les vrais cours BRVM"""
    print("\n" + "="*80)
    print("📊 MISE À JOUR COURS BRVM RÉELS")
    print("="*80 + "\n")
    
    # Vérifier si des prix ont été renseignés
    prix_renseignes = [symbol for symbol, prix in COURS_BRVM_AUJOURDHUI.items() if prix > 0]
    
    if not prix_renseignes:
        print("❌ ERREUR: Aucun prix n'a été renseigné !")
        print("\n📝 INSTRUCTIONS:")
        print("   1. Ouvrir ce fichier: mettre_a_jour_cours_brvm_rapide.py")
        print("   2. Remplacer les 0 par les vrais cours BRVM")
        print("   3. Relancer: python mettre_a_jour_cours_brvm_rapide.py\n")
        return
    
    print(f"✅ {len(prix_renseignes)} cours à mettre à jour\n")
    
    _, db = get_mongo_db()
    now = datetime.now(timezone.utc)
    
    observations = []
    
    for symbol, prix_actuel in COURS_BRVM_AUJOURDHUI.items():
        if prix_actuel <= 0:
            continue  # Skip les prix non renseignés
        
        # Récupérer le prix précédent pour calculer la variation
        prix_precedent = db.curated_observations.find_one(
            {'source': 'BRVM', 'key': symbol},
            sort=[('ts', -1)]
        )
        
        if prix_precedent:
            prix_hier = prix_precedent['value']
            variation = round((prix_actuel - prix_hier) / prix_hier * 100, 2)
        else:
            prix_hier = prix_actuel
            variation = 0.0
        
        # OHLC (si pas de données intraday, utiliser le prix de clôture)
        observation = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': symbol,
            'ts': now,
            'value': prix_actuel,
            'attrs': {
                'open': prix_hier,
                'high': max(prix_actuel, prix_hier),
                'low': min(prix_actuel, prix_hier),
                'close': prix_actuel,
                'volume': 1000,  # Volume par défaut (à mettre à jour si disponible)
                'day_change': round(prix_actuel - prix_hier, 2),
                'day_change_pct': variation,
                'data_quality': 'REAL_MANUAL',
                'update_source': 'MANUEL_BRVM_ORG',
                'update_date': now.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }
        observations.append(observation)
    
    # Insérer dans MongoDB
    if observations:
        db.curated_observations.insert_many(observations)
        print(f"✅ {len(observations)} cours mis à jour dans la base\n")
        
        # Afficher échantillon
        print("📋 ÉCHANTILLON DES COURS MIS À JOUR:\n")
        for obs in sorted(observations[:10], key=lambda x: x['key']):
            symbol = obs['key']
            prix = obs['value']
            variation = obs['attrs']['day_change_pct']
            emoji = "📈" if variation > 0 else "📉" if variation < 0 else "➡️"
            print(f"   {emoji} {symbol:8s} | {prix:8.0f} FCFA | {variation:+6.2f}%")
        
        if len(observations) > 10:
            print(f"   ... et {len(observations) - 10} autres actions")
    
    print("\n" + "="*80)
    print("✅ MISE À JOUR TERMINÉE")
    print("="*80 + "\n")
    
    print("📊 PROCHAINES ÉTAPES:\n")
    print("   1. Relancer l'analyse IA: python lancer_analyse_ia_complete.py")
    print("   2. Consulter dashboard: http://localhost:8000/dashboard/brvm/")
    print("   3. Vérifier les signaux: python diagnostic_analyse_ia.py\n")

if __name__ == "__main__":
    try:
        mettre_a_jour_avec_vrais_prix()
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()

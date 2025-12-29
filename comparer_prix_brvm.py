"""
Comparer les prix dans la base avec les vrais cours BRVM
Permet de voir l'écart entre nos données et le marché réel
"""
import sys
import os
import django

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# VRAIS COURS BRVM à mettre à jour manuellement depuis www.brvm.org
VRAIS_COURS_REFERENCE = {
    # À COMPLÉTER avec les vrais cours du marché
    # Format: 'SYMBOL': prix_réel_FCFA
    'SNTS': 15500,  # Sonatel - Vérifier sur BRVM.org
    'BICC': 7200,   # BICICI
    'ECOC': 6800,   # Ecobank CI
    'ORGT': 5400,   # Orange CI
    'BOAC': 6300,   # BOA CI
    'SGBC': 7500,   # Société Générale
    'SIBC': 7300,   # SIB
    # ... Ajouter les autres actions
}

def comparer_prix():
    """Compare nos prix avec les vrais cours BRVM"""
    print("\n" + "="*80)
    print("📊 COMPARAISON PRIX BASE vs MARCHÉ BRVM RÉEL")
    print("="*80 + "\n")
    
    if not VRAIS_COURS_REFERENCE:
        print("⚠️ VRAIS_COURS_REFERENCE est vide!")
        print("\n💡 INSTRUCTIONS:")
        print("1. Ouvrez: comparer_prix_brvm.py")
        print("2. Complétez VRAIS_COURS_REFERENCE avec les vrais cours")
        print("3. Source: https://www.brvm.org/fr/investir/cours-et-cotations\n")
        return
    
    _, db = get_mongo_db()
    
    # Récupérer les cours les plus récents dans notre base
    cours_base = {}
    for symbol in VRAIS_COURS_REFERENCE.keys():
        latest = db.curated_observations.find_one(
            {'source': 'BRVM', 'key': symbol},
            sort=[('ts', -1)]
        )
        if latest:
            cours_base[symbol] = latest['value']
    
    print("📋 COMPARAISON PAR ACTION:\n")
    print(f"{'Symbol':8s} | {'Notre Prix':12s} | {'Prix Réel':12s} | {'Écart':12s} | {'Qualité'}")
    print("-" * 80)
    
    ecarts = []
    for symbol, prix_reel in sorted(VRAIS_COURS_REFERENCE.items()):
        prix_base = cours_base.get(symbol, 0)
        
        if prix_base == 0:
            print(f"{symbol:8s} | {'N/A':>12s} | {prix_reel:>10.0f} F | {'N/A':>12s} | ❌ Absent")
            continue
        
        ecart = prix_base - prix_reel
        ecart_pct = (ecart / prix_reel) * 100
        ecarts.append(abs(ecart_pct))
        
        # Qualité selon l'écart
        if abs(ecart_pct) < 1:
            qualite = "✅ Excellent"
        elif abs(ecart_pct) < 5:
            qualite = "⚠️ Acceptable"
        elif abs(ecart_pct) < 10:
            qualite = "⚠️ Important"
        else:
            qualite = "❌ CRITIQUE"
        
        print(f"{symbol:8s} | {prix_base:>10.0f} F | {prix_reel:>10.0f} F | {ecart:+10.0f} F ({ecart_pct:+.1f}%) | {qualite}")
    
    # Statistiques globales
    if ecarts:
        print("\n" + "="*80)
        print("📊 STATISTIQUES GLOBALES")
        print("="*80 + "\n")
        
        ecart_moyen = sum(ecarts) / len(ecarts)
        ecart_max = max(ecarts)
        
        print(f"   Écart moyen: {ecart_moyen:.2f}%")
        print(f"   Écart maximum: {ecart_max:.2f}%")
        print(f"   Actions comparées: {len(ecarts)}/{len(VRAIS_COURS_REFERENCE)}")
        
        if ecart_moyen < 1:
            print("\n   ✅ Qualité EXCELLENTE - Données très proches du marché")
        elif ecart_moyen < 5:
            print("\n   ⚠️ Qualité ACCEPTABLE - Écarts mineurs")
        elif ecart_moyen < 10:
            print("\n   ⚠️ Qualité MOYENNE - Mise à jour recommandée")
        else:
            print("\n   ❌ Qualité FAIBLE - MISE À JOUR URGENTE REQUISE")
    
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80 + "\n")
    
    if ecart_moyen > 5:
        print("⚠️ ATTENTION: Écarts importants détectés!")
        print("\n📋 ACTIONS À PRENDRE:")
        print("1. Mettre à jour avec les vrais cours:")
        print("   python saisir_cours_brvm_reels.py")
        print("\n2. Vérifier l'insertion:")
        print("   python verifier_cours_brvm.py")
        print("\n3. Relancer l'analyse avec données réelles:")
        print("   python lancer_analyse_ia_complete.py\n")
    else:
        print("✅ Données proches du marché réel")
        print("📊 Analyse IA peut être utilisée pour le trading\n")

if __name__ == "__main__":
    try:
        comparer_prix()
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()

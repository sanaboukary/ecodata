"""
🚀 Démarrage Express du Data Marketplace
Lance le serveur et ouvre la page dans le navigateur
"""
import os
import sys
import time
import webbrowser
from pathlib import Path

# Couleurs pour terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Affiche un en-tête coloré"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Affiche un avertissement"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Affiche une information"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_dependencies():
    """Vérifie les dépendances nécessaires"""
    print_header("Vérification des dépendances")
    
    dependencies = {
        'django': 'Django',
        'pymongo': 'PyMongo',
        'openpyxl': 'openpyxl (Export Excel)',
        'requests': 'Requests (Tests)'
    }
    
    missing = []
    
    for package, name in dependencies.items():
        try:
            __import__(package)
            print_success(f"{name} installé")
        except ImportError:
            print_error(f"{name} manquant")
            missing.append(package)
    
    if missing:
        print_warning(f"\nInstallez les dépendances manquantes:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_mongodb():
    """Vérifie la connexion MongoDB"""
    print_header("Vérification MongoDB")
    
    try:
        from plateforme_centralisation.mongo import get_mongo_db
        client, db = get_mongo_db()
        
        # Test connexion
        client.server_info()
        
        # Compter observations
        count = db.curated_observations.count_documents({})
        
        print_success(f"MongoDB connecté")
        print_info(f"{count:,} observations en base")
        
        return True
        
    except Exception as e:
        print_error(f"Connexion MongoDB échouée: {e}")
        print_warning("Lancez MongoDB avec: python demarrer_mongodb.py")
        return False

def check_data_quality():
    """Vérifie la qualité des données BRVM"""
    print_header("Vérification Données BRVM")
    
    try:
        from plateforme_centralisation.mongo import get_mongo_db
        client, db = get_mongo_db()
        
        # BRVM observations
        brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
        
        if brvm_count == 0:
            print_warning("Aucune donnée BRVM trouvée")
            print_info("Collectez des données avec: python collecter_quotidien_intelligent.py")
            return False
        
        # Dernière date
        latest = db.curated_observations.find_one(
            {'source': 'BRVM'},
            sort=[('ts', -1)]
        )
        
        print_success(f"{brvm_count:,} observations BRVM")
        print_info(f"Dernière mise à jour: {latest['ts'][:10]}")
        
        # Actions uniques
        symbols = db.curated_observations.distinct('key', {'source': 'BRVM'})
        print_info(f"{len(symbols)} actions/indices cotés")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur vérification données: {e}")
        return False

def start_server():
    """Lance le serveur Django"""
    print_header("Démarrage Serveur Django")
    
    print_info("Lancement sur http://localhost:8000")
    print_info("Appuyez sur Ctrl+C pour arrêter")
    print()
    
    # Lancer serveur (bloquant)
    os.system("python manage.py runserver")

def open_browser():
    """Ouvre le marketplace dans le navigateur"""
    print_info("Ouverture du marketplace dans 3 secondes...")
    time.sleep(3)
    
    url = "http://localhost:8000/dashboard/marketplace/"
    webbrowser.open(url)
    print_success(f"Navigateur ouvert: {url}")

def show_menu():
    """Affiche le menu de démarrage"""
    print_header("🚀 MARKETPLACE DATA - Démarrage Express")
    
    print(f"{Colors.BOLD}Que voulez-vous faire ?{Colors.END}\n")
    print("1️⃣  Démarrer le marketplace (serveur + navigateur)")
    print("2️⃣  Vérifier l'installation complète")
    print("3️⃣  Collecter des données BRVM")
    print("4️⃣  Lancer les tests du marketplace")
    print("5️⃣  Voir la documentation")
    print("0️⃣  Quitter")
    print()
    
    choice = input(f"{Colors.BOLD}Votre choix (0-5) : {Colors.END}")
    return choice

def run_tests():
    """Lance les tests du marketplace"""
    print_header("Exécution des Tests")
    
    print_info("Lancement des tests automatiques...")
    os.system("python test_marketplace.py")

def collect_brvm_data():
    """Lance la collecte de données BRVM"""
    print_header("Collecte Données BRVM")
    
    print_info("Lancement du collecteur intelligent...")
    os.system("python collecter_quotidien_intelligent.py")

def show_documentation():
    """Affiche le chemin vers la documentation"""
    print_header("Documentation")
    
    doc_path = Path("MARKETPLACE_DOCUMENTATION.md")
    
    if doc_path.exists():
        print_success(f"Documentation disponible: {doc_path.absolute()}")
        print_info("Ouvrez ce fichier avec n'importe quel éditeur Markdown")
        
        # Afficher aperçu
        print(f"\n{Colors.BOLD}Aperçu:{Colors.END}\n")
        with open(doc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:20]
            for line in lines:
                print(f"   {line.rstrip()}")
        
        print(f"\n{Colors.YELLOW}... (voir fichier complet pour plus){Colors.END}")
    else:
        print_error("Documentation non trouvée")

def main():
    """Fonction principale"""
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Démarrage complet
            if not check_dependencies():
                input("\nAppuyez sur Entrée pour continuer...")
                continue
            
            if not check_mongodb():
                input("\nAppuyez sur Entrée pour continuer...")
                continue
            
            check_data_quality()
            
            print_header("🎉 Tout est prêt!")
            print_success("Le marketplace va démarrer...")
            print_warning("Le serveur va se lancer (bloquant)")
            print_info("Ouvrez manuellement: http://localhost:8000/dashboard/marketplace/")
            print()
            
            input("Appuyez sur Entrée pour démarrer...")
            
            # Lancer serveur (bloquant)
            start_server()
            break
            
        elif choice == '2':
            # Vérification complète
            check_dependencies()
            check_mongodb()
            check_data_quality()
            
            print_header("✨ Vérification Terminée")
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == '3':
            # Collecte BRVM
            collect_brvm_data()
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == '4':
            # Tests
            run_tests()
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == '5':
            # Documentation
            show_documentation()
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == '0':
            # Quitter
            print_header("👋 À bientôt!")
            break
            
        else:
            print_error("Choix invalide. Réessayez.")
            time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Arrêt demandé par l'utilisateur{Colors.END}")
        print(f"{Colors.GREEN}✅ Marketplace arrêté{Colors.END}\n")
        sys.exit(0)

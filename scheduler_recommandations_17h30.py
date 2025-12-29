"""
Script de collecte quotidienne automatique à 17h30
Alternative à Airflow pour Windows
"""
import schedule
import time
import subprocess
from datetime import datetime
import logging

# Configuration logging
logging.basicConfig(
    filename='recommandations_17h30.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def executer_analyse_complete():
    """Exécute l'analyse complète et log les résultats"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f'Début analyse complète: {timestamp}')
        print(f'\n{"="*80}')
        print(f'🚀 ANALYSE BRVM - {timestamp}')
        print(f'{"="*80}\n')
        
        # Lancer l'analyse
        result = subprocess.run(
            ['python', 'lancer_analyse_ia_complete.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logging.info('✅ Analyse terminée avec succès')
            print('✅ Analyse terminée avec succès')
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        else:
            logging.error(f'❌ Erreur: {result.stderr}')
            print(f'❌ Erreur: {result.stderr}')
            
    except Exception as e:
        logging.error(f'❌ Exception: {str(e)}')
        print(f'❌ Exception: {str(e)}')

def main():
    print('='*80)
    print('SCHEDULER RECOMMANDATIONS BRVM - 17h30')
    print('='*80)
    print('')
    print('📅 Schedule: 17h30 du lundi au vendredi')
    print('📝 Logs: recommandations_17h30.log')
    print('')
    print('🔄 Démarrage du scheduler...')
    print('')
    
    # Programmer l'exécution à 17h30 du lundi au vendredi
    schedule.every().monday.at("17:30").do(executer_analyse_complete)
    schedule.every().tuesday.at("17:30").do(executer_analyse_complete)
    schedule.every().wednesday.at("17:30").do(executer_analyse_complete)
    schedule.every().thursday.at("17:30").do(executer_analyse_complete)
    schedule.every().friday.at("17:30").do(executer_analyse_complete)
    
    logging.info('Scheduler démarré')
    
    print('✅ Scheduler actif!')
    print('')
    print('⏰ Prochaines exécutions programmées:')
    for job in schedule.get_jobs():
        print(f'   - {job}')
    print('')
    print('💡 Pour tester maintenant: python lancer_analyse_ia_complete.py')
    print('🛑 Pour arrêter: Ctrl+C')
    print('')
    
    # Boucle principale
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes
    except KeyboardInterrupt:
        print('\n\n🛑 Arrêt du scheduler')
        logging.info('Scheduler arrêté par utilisateur')

if __name__ == '__main__':
    main()

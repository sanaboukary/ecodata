#!/usr/bin/env python3
"""
📢 SYSTÈME DE NOTIFICATIONS - OPPORTUNITÉS FORTES

Notifie lorsqu'une opportunité FORTE (score ≥ 70) est détectée

Modes disponibles :
- Console (affichage coloré)
- Fichier log
- Email (si configuré)
- Webhook Discord/Slack (si configuré)
"""
import os, sys
from pathlib import Path
from datetime import datetime
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION
# ============================================================================

NOTIFICATIONS_DIR = BASE_DIR / "logs" / "notifications"
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = {
    'console': True,              # Affichage console
    'file': True,                 # Log fichier
    'email': False,               # Email (nécessite configuration SMTP)
    'webhook': False,             # Webhook Discord/Slack
    
    'min_score': 70,              # Score minimum pour notification FORTE
    'threshold_alert': 75,        # Score > 75 = ALERTE PRIORITAIRE
    
    'email_config': {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_email': '',         # À configurer
        'to_emails': [],          # À configurer
        'password': ''            # À configurer
    },
    
    'webhook_config': {
        'url': '',                # Webhook Discord ou Slack
        'type': 'discord'         # 'discord' ou 'slack'
    }
}

# ============================================================================
# NOTIFICATIONS CONSOLE
# ============================================================================

def notify_console(opportunities):
    """Afficher opportunités en console (coloré)"""
    if not opportunities:
        return
    
    print("\n" + "="*100)
    print("🔥 ALERTE OPPORTUNITÉS FORTES DÉTECTÉES 🔥")
    print("="*100 + "\n")
    
    for opp in opportunities:
        score = opp['opportunity_score']
        level = opp['level']
        symbol = opp['symbol']
        price = opp['current_price']
        
        # Déterminer urgence
        if score >= CONFIG['threshold_alert']:
            urgence = "🚨 PRIORITAIRE"
        else:
            urgence = "🔥 FORTE"
        
        print(f"{urgence} | {symbol:<8} | Score: {score:>5.1f} | Prix: {price:>8.0f} FCFA")
        
        # Détecteurs actifs
        det = opp['detectors']
        actifs = []
        if det['news_silent']['detected']:
            actifs.append(f"📰 News: {det['news_silent']['reason']}")
        if det['volume_accumulation']['detected']:
            actifs.append(f"📊 Volume: {det['volume_accumulation']['reason']}")
        if det['volatility_awakening']['detected']:
            actifs.append(f"⚡ Volatilité: {det['volatility_awakening']['reason']}")
        if det['sector_lag']['detected']:
            actifs.append(f"🏢 Secteur: {det['sector_lag']['reason']}")
        
        if actifs:
            for sig in actifs:
                print(f"     └─ {sig}")
        
        # Composantes du score
        comp = opp['components']
        print(f"     Composantes: Vol={comp['volume_acceleration']:.0f} | News={comp['semantic_impact']:.0f} | Volat={comp['volatility_expansion']:.0f} | Sect={comp['sector_momentum']:.0f}")
        
        print()
    
    print("="*100)
    print(f"💡 ACTION RECOMMANDÉE : Entrer 25% position sur opportunités PRIORITAIRES (score ≥75)")
    print(f"   Observer et confirmer J+1 pour opportunités FORTES (score 70-75)")
    print("="*100 + "\n")

# ============================================================================
# NOTIFICATIONS FICHIER
# ============================================================================

def notify_file(opportunities, date):
    """Enregistrer dans fichier log"""
    if not opportunities:
        return
    
    log_file = NOTIFICATIONS_DIR / f"opportunities_{date}.log"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "="*100 + "\n")
        f.write(f"OPPORTUNITÉS FORTES - {date} - {datetime.now()}\n")
        f.write("="*100 + "\n\n")
        
        for opp in opportunities:
            f.write(f"SYMBOLE     : {opp['symbol']}\n")
            f.write(f"SCORE       : {opp['opportunity_score']:.1f} ({opp['level']})\n")
            f.write(f"PRIX        : {opp['current_price']:.0f} FCFA\n")
            f.write(f"DATE        : {opp['date']}\n")
            
            f.write("\nDÉTECTEURS ACTIFS :\n")
            for key, det in opp['detectors'].items():
                if det['detected']:
                    f.write(f"  ✓ {key}: {det['reason']}\n")
            
            f.write("\nCOMPOSANTES :\n")
            for key, val in opp['components'].items():
                f.write(f"  • {key}: {val:.1f}\n")
            
            f.write("\n" + "-"*100 + "\n\n")
    
    print(f"📄 Log sauvegardé : {log_file}")

# ============================================================================
# NOTIFICATIONS EMAIL
# ============================================================================

def notify_email(opportunities, date):
    """Envoyer notification email"""
    if not CONFIG['email'] or not CONFIG['email_config']['from_email']:
        return
    
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    if not opportunities:
        return
    
    # Construire email
    subject = f"🔥 {len(opportunities)} OPPORTUNITÉ(S) FORTE(S) BRVM - {date}"
    
    body = f"""
OPPORTUNITÉS FORTES DÉTECTÉES - {date}
{'='*80}

{len(opportunities)} opportunité(s) détectée(s) avec score ≥ 70

"""
    
    for i, opp in enumerate(opportunities, 1):
        body += f"""
{i}. {opp['symbol']} - SCORE {opp['opportunity_score']:.1f}
   Prix actuel : {opp['current_price']:.0f} FCFA
   
   Détecteurs :
"""
        for key, det in opp['detectors'].items():
            if det['detected']:
                body += f"      ✓ {key}: {det['reason']}\n"
        
        body += "\n"
    
    body += """
ACTION RECOMMANDÉE :
- Score ≥ 75 : Entrer 25% position immédiatement
- Score 70-75 : Observer et confirmer J+1

Voir dashboard pour détails : python brvm_pipeline/dashboard_opportunities.py
"""
    
    # Envoi
    try:
        msg = MIMEMultipart()
        msg['From'] = CONFIG['email_config']['from_email']
        msg['To'] = ', '.join(CONFIG['email_config']['to_emails'])
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(CONFIG['email_config']['smtp_host'], CONFIG['email_config']['smtp_port'])
        server.starttls()
        server.login(CONFIG['email_config']['from_email'], CONFIG['email_config']['password'])
        
        server.send_message(msg)
        server.quit()
        
        print(f"📧 Email envoyé à {len(CONFIG['email_config']['to_emails'])} destinataire(s)")
        
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ============================================================================
# NOTIFICATIONS WEBHOOK (Discord/Slack)
# ============================================================================

def notify_webhook(opportunities, date):
    """Envoyer notification via webhook"""
    if not CONFIG['webhook'] or not CONFIG['webhook_config']['url']:
        return
    
    import requests
    
    if not opportunities:
        return
    
    url = CONFIG['webhook_config']['url']
    webhook_type = CONFIG['webhook_config']['type']
    
    # Construire message
    if webhook_type == 'discord':
        # Format Discord
        embeds = []
        
        for opp in opportunities:
            color = 0xFF0000 if opp['opportunity_score'] >= 75 else 0xFFA500  # Rouge ou orange
            
            # Détecteurs actifs
            fields = []
            for key, det in opp['detectors'].items():
                if det['detected']:
                    fields.append({
                        'name': key.replace('_', ' ').title(),
                        'value': det['reason'],
                        'inline': False
                    })
            
            embed = {
                'title': f"🔥 {opp['symbol']} - OPPORTUNITÉ FORTE",
                'description': f"Score: **{opp['opportunity_score']:.1f}** | Prix: **{opp['current_price']:.0f} FCFA**",
                'color': color,
                'fields': fields,
                'footer': {'text': f"Date: {date}"}
            }
            
            embeds.append(embed)
        
        payload = {
            'content': f"**{len(opportunities)} OPPORTUNITÉ(S) FORTE(S) DÉTECTÉE(S)**",
            'embeds': embeds[:10]  # Max 10 embeds Discord
        }
        
    else:  # Slack
        # Format Slack
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f'🔥 {len(opportunities)} OPPORTUNITÉ(S) FORTE(S) - {date}'
                }
            }
        ]
        
        for opp in opportunities:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*{opp['symbol']}* - Score: *{opp['opportunity_score']:.1f}* | Prix: {opp['current_price']:.0f} FCFA"
                }
            })
        
        payload = {'blocks': blocks}
    
    # Envoi
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 204 or response.status_code == 200:
            print(f"📱 Webhook {webhook_type.title()} envoyé")
        else:
            print(f"❌ Erreur webhook : {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur envoi webhook : {e}")

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def check_and_notify(date=None):
    """
    Vérifier opportunités FORTES et notifier
    
    Args:
        date: Date à vérifier (défaut: hier)
    """
    from datetime import datetime, timedelta
    
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n🔍 Vérification opportunités FORTES - {date}")
    
    # Chercher opportunités FORTES
    opportunities = list(db['opportunities_brvm'].find({
        'date': date,
        'level': 'FORTE'
    }).sort('opportunity_score', -1))
    
    if not opportunities:
        print("✅ Aucune opportunité FORTE détectée")
        return
    
    print(f"🔥 {len(opportunities)} opportunité(s) FORTE(S) trouvée(s)\n")
    
    # Notifications
    if CONFIG['console']:
        notify_console(opportunities)
    
    if CONFIG['file']:
        notify_file(opportunities, date)
    
    if CONFIG['email']:
        notify_email(opportunities, date)
    
    if CONFIG['webhook']:
        notify_webhook(opportunities, date)

# ============================================================================
# CONFIGURATION INTERACTIVE
# ============================================================================

def configure_notifications():
    """Configuration interactive des notifications"""
    print("\n" + "="*80)
    print("⚙️  CONFIGURATION NOTIFICATIONS")
    print("="*80 + "\n")
    
    print("Modes actuels :")
    print(f"  Console  : {'✅' if CONFIG['console'] else '❌'}")
    print(f"  Fichier  : {'✅' if CONFIG['file'] else '❌'}")
    print(f"  Email    : {'✅' if CONFIG['email'] else '❌'} {' (configuré)' if CONFIG['email_config']['from_email'] else ' (non configuré)'}")
    print(f"  Webhook  : {'✅' if CONFIG['webhook'] else '❌'} {' (configuré)' if CONFIG['webhook_config']['url'] else ' (non configuré)'}")
    
    print("\nSeuils :")
    print(f"  Opportunité FORTE     : Score ≥ {CONFIG['min_score']}")
    print(f"  Alerte PRIORITAIRE    : Score ≥ {CONFIG['threshold_alert']}")
    
    print("\n💡 Pour configurer email/webhook, éditer : brvm_pipeline/notifications_opportunites.py")
    print()

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Notifications Opportunités FORTES')
    parser.add_argument('--date', help='Date à vérifier (YYYY-MM-DD)')
    parser.add_argument('--config', action='store_true', help='Afficher configuration')
    parser.add_argument('--test', action='store_true', help='Mode test (dernière date)')
    
    args = parser.parse_args()
    
    if args.config:
        configure_notifications()
    elif args.test:
        # Test sur dernière date avec données
        latest = db['opportunities_brvm'].find_one(sort=[('date', -1)])
        if latest:
            check_and_notify(latest['date'])
        else:
            print("❌ Aucune opportunité en base. Exécuter d'abord : python opportunity_engine.py")
    else:
        check_and_notify(args.date)

if __name__ == "__main__":
    main()

"""
Service d'envoi automatique d'e-mails aux utilisateurs premium pour les recommandations d'achat/vente.
"""
from django.core.mail import send_mail
from django.conf import settings
from plateforme_centralisation.mongo import get_mongo_db
from dashboard.correlation_engine import generate_trading_recommendations
from django.contrib.auth import get_user_model

def send_recommendations_to_premium_users():
    _, db = get_mongo_db()
    User = get_user_model()
    premium_users = User.objects.filter(is_premium=True, is_active=True)
    recos = generate_trading_recommendations(days=1)  # Recos du jour
    if not recos:
        return 0
    for user in premium_users:
        subject = "Recommandations BRVM - Achat/Vente du jour"
        message = "Bonjour,\n\nVoici vos recommandations du jour :\n\n"
        for reco in recos:
            message += f"Action : {reco['action']}\nRecommandation : {reco['recommandation']}\nVariation : {reco['variation']}\nPublication : {reco['publication']}\nLien : {reco['url']}\n---\n"
        message += "\nCeci est un envoi automatique.\n"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    return len(premium_users)

# Envoi groupé à tous les tokens enregistrés
from plateforme_centralisation.mongo import get_mongo_db
def send_push_to_all(title, body, data=None):
    _, db = get_mongo_db()
    tokens = [doc['token'] for doc in db.push_tokens.find({}) if 'token' in doc]
    results = []
    for token in tokens:
        status, resp = send_push_notification(token, title, body, data)
        results.append({"token": token, "status": status, "resp": resp})
    return results
"""
Service générique pour notifications push (web/app).
Prévu pour intégration avec Firebase Cloud Messaging, OneSignal, ou Web Push API.
"""
import requests

# Exemple d'intégration avec Firebase Cloud Messaging (FCM)
# Remplacer FCM_SERVER_KEY par ta clé serveur FCM
FCM_SERVER_KEY = "<A REMPLACER>"
FCM_URL = "https://fcm.googleapis.com/fcm/send"

def send_push_notification(token, title, body, data=None):
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body
        },
        "data": data or {}
    }
    resp = requests.post(FCM_URL, json=payload, headers=headers)
    return resp.status_code, resp.text

# Exemple d'appel :
# send_push_notification(token, "Alerte BRVM", "Signal d'achat détecté sur BOAB")

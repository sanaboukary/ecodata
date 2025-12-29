from django.conf import settings
from pymongo import MongoClient
import os


def get_mongo_client():
    # Utiliser les variables d'environnement au lieu de DATABASES["default"]
    uri = os.getenv('MONGODB_URI', settings.MONGODB_URI)
    return MongoClient(uri)


def get_mongo_db():
    client = get_mongo_client()
    # Utiliser les variables d'environnement pour le nom de la base
    db_name = os.getenv('MONGODB_NAME', settings.MONGODB_NAME)
    return client, client[db_name]





import os
from pymongo import MongoClient

def get_mongo_client():
    # Priorité : variable d'environnement, sinon valeur par défaut locale
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    timeout_ms = int(os.getenv('MONGODB_TIMEOUT_MS', '5000'))
    return MongoClient(
        uri,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
    )

def get_mongo_db():
    client = get_mongo_client()
    db_name = os.getenv('MONGODB_NAME', 'centralisation_db')
    try:
        client.admin.command('ping')
    except Exception as e:
        raise RuntimeError(
            f"MongoDB injoignable (uri={os.getenv('MONGODB_URI', 'mongodb://localhost:27017')}, timeout={os.getenv('MONGODB_TIMEOUT_MS', '5000')}ms). "
            "Démarre MongoDB puis relance."
        ) from e

    return client, client[db_name]



import os
from urllib.parse import quote
from pymongo import MongoClient


def get_mongo_client_from_env() -> MongoClient:
	uri = os.getenv("MONGODB_URI")
	if not uri:
		raise RuntimeError("MONGODB_URI manquant dans l'environnement")
	return MongoClient(uri)


def get_db_from_env():
	client = get_mongo_client_from_env()
	db_name = os.getenv("MONGODB_NAME", "centralisation_db")
	return client, client[db_name]

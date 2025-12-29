import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGODB_NAME", "centralisation_db")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

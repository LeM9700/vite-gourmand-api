from pymongo import MongoClient
from dotenv import load_dotenv
import os
from app.core.config import settings

load_dotenv()

# Configuration MongoDB
_client: MongoClient | None = None

def get_mongo_client() -> MongoClient:
    global _client
    if _client is not None:
        return _client

    url = os.getenv("MONGO_URL")
    if not url:
        raise RuntimeError("MONGO_URL manquant dans l'environnement (.env)")

    # timeouts plus courts = debug plus rapide
    _client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
    return _client

def get_mongo_db():
    client = get_mongo_client()
    db_name = settings.mongo_db
    return client[db_name]
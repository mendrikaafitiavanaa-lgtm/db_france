"""
database/connexion.py
----------------------
Connexion MongoDB centralisée. Toute la logique du projet qui a besoin
d'accéder à MongoDB passe par obtenir_db() plutôt que de créer sa propre
connexion — un seul point de configuration, une seule connexion réutilisée.
"""

from pymongo import MongoClient
import config

_client = None


def obtenir_client() -> MongoClient:
    """Retourne un client MongoDB unique, créé une seule fois (singleton simple)."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    return _client


def obtenir_db():
    """Retourne la base de données configurée dans .env (MONGO_DB_NAME)."""
    return obtenir_client()[config.MONGO_DB_NAME]


def fermer_connexion():
    global _client
    if _client is not None:
        _client.close()
        _client = None
"""
Configuration centralisée du projet db-Entreprise_france.

Toutes les valeurs sensibles ou variables (URI Mongo, noms de collection,
clés API futures, paramètres de performance) viennent du fichier .env.
Aucun script de src/ ne doit contenir de valeur en dur : tout passe par ici.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "")

# Noms de collections, utilisés par les fichiers database/*.py
# (un fichier = une collection, cf. database/entreprises.py)
COLLECTION_ENTREPRISES_SOURCE = os.getenv("MONGO_SOURCE_COLLECTION", "")
COLLECTION_ENTREPRISES_ENRICHIES = os.getenv("MONGO_TARGET_COLLECTION", "entreprises_enrichies")

# --- Clés API (réservées aux étapes suivantes) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --- Performance (mêmes noms de variables réutilisés à chaque étape) ---
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
PAUSE_SECONDES = float(os.getenv("PAUSE_SECONDES", "0"))

# --- Logging centralisé ---
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

#ecrire dans fichier log de résumé des exécutions
def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré identique pour tous les scripts du projet."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # évite les handlers dupliqués si appelé plusieurs fois

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOGS_DIR / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def verifier_config():
    """Vérifie que les variables essentielles sont bien renseignées avant de lancer un script."""
    manquants = []
    if not MONGO_DB_NAME:
        manquants.append("MONGO_DB_NAME")
    if not COLLECTION_ENTREPRISES_SOURCE:
        manquants.append("MONGO_SOURCE_COLLECTION")
    if manquants:
        raise EnvironmentError(
            f"Variables manquantes dans .env : {', '.join(manquants)}. "
            f"Complète ton fichier .env avant de continuer."
        )
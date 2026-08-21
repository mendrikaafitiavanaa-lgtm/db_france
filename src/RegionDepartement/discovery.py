"""
src/RegionDepartement/discovery.py
------------------------------------
Découverte des bases et collections MongoDB disponibles en local.

Objectif : identifier le nom exact de la base et de la collection source
(celle qui contient les 734 entreprises) pour renseigner MONGO_DB_NAME et
MONGO_SOURCE_COLLECTION dans le fichier .env avant l'étape de migration.

Cas particulier : contrairement aux autres étapes, ce script ne peut pas
utiliser src/database/connexion.py (qui a besoin de MONGO_DB_NAME déjà connu)
— c'est justement ce script qui sert à le découvrir. Il crée donc sa propre
connexion MongoDB, une seule fois.

Usage :
    python main.py discovery
"""

from pymongo import MongoClient
import config
from src.utils.timing import run_step

logger = config.get_logger("discovery")


def main():
    logger.info("Connexion à MongoDB : %s", config.MONGO_URI)
    client = MongoClient(config.MONGO_URI)

    try:
        db_names = client.list_database_names()
        logger.info("Nombre de bases trouvées : %d", len(db_names))

        for db_name in db_names:
            db = client[db_name]
            logger.info("Base : %s", db_name)
            for coll_name in db.list_collection_names():
                count = db[coll_name].count_documents({})
                logger.info("   -> Collection : %s (%d documents)", coll_name, count)
    finally:
        client.close()
        logger.info("Connexion fermée.")


if __name__ == "__main__":
    run_step("discovery", main)
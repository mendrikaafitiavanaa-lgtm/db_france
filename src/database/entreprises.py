"""
src/database/entreprises.py
------------------------
Tout ce qui concerne la collection des entreprises (source et enrichie).
Une entreprise est identifiée par son siren.
"""

import logging
from pymongo import UpdateOne

from src.database.connexion import obtenir_db
import config


def creer_index():
    """Index sur siren pour accélérer les recherches et éviter les doublons."""
    collection = obtenir_db()[config.COLLECTION_ENTREPRISES_ENRICHIES]
    collection.create_index("siren")
    logging.info("Index créé sur la collection entreprises enrichies (siren).")


def lire_entreprises_par_lots(taille_lot: int = 100):
    """
    Générateur : lit la collection source par lots (pagination), sans tout
    charger en mémoire. Utilisé par les étapes d'enrichissement.
    """
    collection = obtenir_db()[config.COLLECTION_ENTREPRISES_SOURCE]
    curseur = collection.find({}).sort("adresse", 1)

    lot = []
    for document in curseur:
        lot.append(document)
        if len(lot) >= taille_lot:
            yield lot
            lot = []
    if lot:
        yield lot


def sauvegarder_entreprises_bulk(entreprises: list[dict]) -> dict:
    """
    Met à jour (ou insère si absent) plusieurs entreprises en un seul appel.
    Upsert sur _id : si l'entreprise existe déjà dans la collection enrichie,
    on met à jour ses champs sans écraser ceux ajoutés par une autre étape.
    """
    if not entreprises:
        return {"traitees": 0, "upserted": 0, "modifiees": 0}

    collection = obtenir_db()[config.COLLECTION_ENTREPRISES_ENRICHIES]

    operations = [
        UpdateOne({"_id": entreprise["_id"]}, {"$set": entreprise}, upsert=True)
        for entreprise in entreprises
    ]
    resultat = collection.bulk_write(operations, ordered=False)

    resume = {
        "traitees": len(operations),
        "upserted": resultat.upserted_count,
        "modifiees": resultat.modified_count,
    }
    logging.info(
        "%d entreprise(s) traitée(s) (%d ajoutées, %d modifiées).",
        resume["traitees"], resume["upserted"], resume["modifiees"],
    )
    return resume


def compter_entreprises_source() -> int:
    collection = obtenir_db()[config.COLLECTION_ENTREPRISES_SOURCE]
    return collection.count_documents({})
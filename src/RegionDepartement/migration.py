"""Étape de migration : copie la collection source vers une collection cible
et ajoute les champs géographiques `departement` et `region` à partir de l'adresse.

Cette étape ne modifie pas la collection source.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from src.database.connexion import obtenir_db
from src.RegionDepartement.geo import extraire_code_postal, calculer_departement_region
from src.utils.timing import run_step


def enrichir_document(doc):
    """Retourne une copie du document enrichie avec departement/region."""
    adresse = doc.get("adresse") or ""
    code_postal = extraire_code_postal(adresse)
    geo = calculer_departement_region(code_postal, adresse=adresse)

    nouveau_doc = dict(doc)
    nouveau_doc["departement"] = geo["departement"]
    nouveau_doc["region"] = geo["region"]
    return nouveau_doc


def migrer_source_vers_cible(batch_size: int = 100):
    """Lit la collection source par lot, enrichit les documents et les écrit dans la cible."""
    db = obtenir_db()
    source = db[config.COLLECTION_ENTREPRISES_SOURCE]
    cible = db[config.COLLECTION_ENTREPRISES_ENRICHIES]

    # Réinitialise la cible pour éviter les doublons sur _id
    cible.delete_many({})

    stats = {
        "total": 0,
        "copies": 0,
        "sans_adresse": 0,
        "sans_code_postal": 0,
        "regions_inconnues": 0,
    }

    lot = []
    for doc in source.find({}):
        stats["total"] += 1
        if not doc.get("adresse"):
            stats["sans_adresse"] += 1

        doc_enrichi = enrichir_document(doc)
        code_postal = extraire_code_postal(doc.get("adresse") or "")
        if not code_postal:
            stats["sans_code_postal"] += 1
        if doc_enrichi.get("region") in (None, "INCONNU"):
            stats["regions_inconnues"] += 1

        lot.append(doc_enrichi)

        if len(lot) >= batch_size:
            cible.insert_many(lot)
            stats["copies"] += len(lot)
            lot.clear()

    if lot:
        cible.insert_many(lot)
        stats["copies"] += len(lot)

    return stats


def main():
    batch_size = max(1, int(getattr(config, "BATCH_SIZE", 100)))
    stats = migrer_source_vers_cible(batch_size=batch_size)
    print(
        f"Migration OK: source={stats['total']} -> cible={stats['copies']} | "
        f"sans_adresse={stats['sans_adresse']} | sans_cp={stats['sans_code_postal']} | "
        f"region_inconnue={stats['regions_inconnues']}"
    )


if __name__ == "__main__":
    run_step("migration", main)
"""
src/RegionDepartement/geo.py
------------------------------------
Détermine département et région à partir d'une adresse, en s'appuyant sur
le référentiel officiel data.gouv.fr des communes de France
(fichier : data/communes_france.csv).

Ce référentiel remplace toute table de communes codée en dur : il couvre
l'ensemble des communes de France (métropole, DOM, Corse comprise), donc
plus besoin de patcher le code à chaque nouvelle commune rencontrée.

Le CSV est chargé une seule fois en mémoire (mis en cache via lru_cache),
peu importe le nombre de documents traités ensuite.
"""

import csv
import re
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

from src.RegionDepartement.mapping import DEPARTEMENT_TO_REGION

# Chemin vers le référentiel officiel (à côté de ce fichier)
CSV_PATH = Path(__file__).parent / "data" / "communes_france.csv"
CSV_DIR = Path(__file__).parent / "data"


def extraire_code_postal(adresse: Optional[str]) -> str:
    """
    Extrait le code postal d'une adresse.

    On prend le DERNIER groupe de 5 chiffres trouvé dans l'adresse, car
    certaines adresses contiennent d'autres suites de 5 chiffres avant
    le vrai code postal (numéro de boîte postale "CS 48756", CEDEX, etc.).
    Le vrai code postal est presque toujours juste avant le nom de la ville,
    en fin d'adresse.
    """
    if not adresse or not isinstance(adresse, str):
        return ""
    matches = re.findall(r"\b(\d{5})\b", adresse)
    return matches[-1] if matches else ""


@lru_cache(maxsize=1)
def _charger_referentiel() -> Dict[str, str]:
    """
    Charge le CSV une seule fois et construit un dict { code_postal: code_departement }.

    Colonnes réelles du fichier data.gouv.fr :
    code_commune_INSEE, nom_commune_postal, code_postal, libelle_acheminement,
    ligne_5, latitude, longitude, code_commune, article, nom_commune,
    nom_commune_complet, code_departement, nom_departement, code_region, nom_region

    Le fichier source stocke certains codes SANS zéro de tête (ex: "6000"
    au lieu de "06000", "6" au lieu de "06" pour le département). On corrige
    ça ici avec .zfill() pour que les lookups matchent bien nos adresses.
    """
    referentiel: Dict[str, str] = {}

    # Si le chemin attendu n'existe pas, tente de trouver un fichier CSV
    # pertinent dans le dossier `data/` (ex: `20230823-communes-departement-region.csv`).
    candidate_files = []
    if CSV_PATH.exists():
        candidate_files.append(CSV_PATH)
    if CSV_DIR.exists():
        for p in sorted(CSV_DIR.glob("*.csv")):
            if p not in candidate_files:
                candidate_files.append(p)

    for path in candidate_files:
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Vérifie rapidement que le fichier contient les colonnes attendues
                if "code_postal" not in reader.fieldnames or "code_departement" not in reader.fieldnames:
                    continue
                for row in reader:
                    cp = (row.get("code_postal") or "").strip().zfill(5)
                    dept = (row.get("code_departement") or "").strip()
                    if dept.isdigit() and len(dept) == 1:
                        dept = dept.zfill(2)
                    if cp and dept:
                        referentiel.setdefault(cp, dept)
                # si on a rempli le référentiel, on arrête la recherche
                if referentiel:
                    break
        except Exception:
            # ignore file read errors and try next candidate
            continue
    return referentiel


def calculer_departement_region(code_postal: Optional[str], adresse: Optional[str] = None) -> dict:
    """
    Retourne {"departement": ..., "region": ...} à partir du code postal,
    en s'appuyant en priorité sur le référentiel officiel des communes.
    """
    if not code_postal:
        return {"departement": None, "region": None}

    code = str(code_postal).strip()
    referentiel = _charger_referentiel()

    # 1) Lookup direct et fiable via le référentiel officiel (résout aussi
    #    nativement les cas Corse 2A/2B et les DOM-TOM sur 3 chiffres).
    dept = referentiel.get(code)
    if dept:
        region = DEPARTEMENT_TO_REGION.get(dept, "INCONNU")
        return {"departement": dept, "region": region}

    # 2) Fallback DOM-TOM (3 chiffres) si le CP n'est pas dans le référentiel
    if len(code) >= 3:
        prefix3 = code[:3]
        if prefix3 in DEPARTEMENT_TO_REGION:
            return {"departement": prefix3, "region": DEPARTEMENT_TO_REGION[prefix3]}

    # 3) Fallback métropole (2 chiffres) - ne résout PAS 2A/2B correctement,
    #    donc si prefix2 == "20" et qu'on arrive ici, c'est que le référentiel
    #    ne connaissait pas ce CP -> on ne peut pas deviner fiablement.
    prefix2 = code[:2]
    if prefix2 == "20":
        return {"departement": "INCONNU", "region": "INCONNU"}

    departement = prefix2 if prefix2.isdigit() else code
    region = DEPARTEMENT_TO_REGION.get(departement)
    if region is None:
        return {"departement": "INCONNU", "region": "INCONNU"}
    return {"departement": departement, "region": region}
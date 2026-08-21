"""
Point d'entrée unique du projet db-Entreprise_france.

Usage :
    python main.py discovery       # étape 1 : découverte MongoDB
    python main.py migration       # étape 2 : region + departement (à venir)
    python main.py domaine         # étape 3 : domaine_activite via SIRENE (à venir)
    python main.py client_cible    # étape 4 : client_cible via LLM (à venir)
    python main.py fusion          # étape 5 : fusion finale (à venir)

Chaque étape logue sa durée et son statut (succès/échec) dans
logs/resume_executions.log, en plus de son propre fichier log détaillé.
"""

import sys

from src.utils.timing import run_step

ETAPES_DISPONIBLES = {
    "discovery": ("src.RegionDepartement.discovery", "discovery"),
    "migration": ("src.RegionDepartement.migration", "migration"),
}


def afficher_aide():
    print("Étapes disponibles :")
    for nom in ETAPES_DISPONIBLES:
        print(f"  - {nom}")
    print("\nUsage : python main.py <nom_etape>")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ETAPES_DISPONIBLES:
        afficher_aide()
        sys.exit(1)

    nom_etape_cli = sys.argv[1]
    module_path, nom_log = ETAPES_DISPONIBLES[nom_etape_cli]

    import importlib
    module = importlib.import_module(module_path)

    run_step(nom_log, module.main)


if __name__ == "__main__":
    main()
"""
Utilitaire commun à toutes les étapes : mesure le temps d'exécution et
capture les erreurs, avec un résumé clair à la fin de chaque étape.

Usage dans un script d'étape :

    from utils.timing import run_step

    def main():
        ... traitement ...

    if __name__ == "__main__":
        run_step("step1_discovery", main)
"""

import time
import traceback
from config import get_logger

resume_logger = get_logger("resume_executions")


def run_step(nom_etape: str, fonction, *args, **kwargs):
    """
    Exécute `fonction`, chronomètre, capture les erreurs, et logue un résumé
    clair : durée totale + statut (succès / échec).
    """
    logger = get_logger(nom_etape)
    debut = time.time()
    logger.info("=== Démarrage de l'étape : %s ===", nom_etape)

    try:
        resultat = fonction(*args, **kwargs)
        duree = time.time() - debut
        logger.info("=== Étape '%s' terminée SANS ERREUR en %.2f secondes ===", nom_etape, duree)
        resume_logger.info("%s : OK, aucune erreur, durée = %.2f s", nom_etape, duree)
        return resultat

    except Exception as e:
        duree = time.time() - debut
        logger.error("=== Étape '%s' a ÉCHOUÉ après %.2f secondes ===", nom_etape, duree)
        logger.error("Erreur : %s", e)
        logger.error(traceback.format_exc())
        resume_logger.error("%s : ÉCHEC après %.2f s -> %s", nom_etape, duree, e)
        raise
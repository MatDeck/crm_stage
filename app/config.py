from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"

# Attente (en jours) avant chaque relance d'une candidature « envoyée » restée sans nouvelles :
# 1re relance 7 j après l'envoi, 2e relance 14 j après la 1re. Ajouter une valeur = une relance de plus.
DELAIS_RELANCE_JOURS = [7, 14]
# Après la dernière relance prévue, sans nouvelles depuis ce délai, la candidature passe « Sans réponse ».
DELAI_SANS_REPONSE_JOURS = 14

TAILLE_MAX_DOCUMENT_MO = 10

SOURCES_PAR_DEFAUT = [
    "Candidature spontanée",
    "LinkedIn",
    "Indeed",
    "Site de l'entreprise",
    "École / réseau",
]
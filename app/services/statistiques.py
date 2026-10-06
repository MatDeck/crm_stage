"""Statistiques de l'accueil, calculées à partir de la liste des candidatures (statuts effectifs)."""

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from app.models.candidature import Candidature, Statut
from app.models.evenement import TypeEvenement

# Statuts qui montrent que l'entreprise a répondu, et entrées d'historique qui datent cette réponse.
STATUTS_REPONSE = {Statut.ENTRETIEN, Statut.ACCEPTE, Statut.REFUSE}
EVENEMENTS_REPONSE = {TypeEvenement.REPONSE, TypeEvenement.ENTRETIEN}
SOURCE_INCONNUE = "Non renseignée"


@dataclass
class ChiffresCles:
    envoyees: int
    taux_reponse: float | None  # entre 0 et 1, None si rien d'envoyé
    taux_entretien: float | None
    delai_moyen_reponse: float | None  # en jours, None si aucune réponse datée


def _envoyee(c: Candidature) -> bool:
    return c.statut != Statut.A_ENVOYER


def _a_repondu(c: Candidature) -> bool:
    return c.statut in STATUTS_REPONSE or any(e.type in EVENEMENTS_REPONSE for e in c.historique)


def _a_eu_entretien(c: Candidature) -> bool:
    return c.statut in (Statut.ENTRETIEN, Statut.ACCEPTE) or any(
        e.type == TypeEvenement.ENTRETIEN for e in c.historique
    )


def _delai_reponse(c: Candidature) -> int | None:
    """Jours entre l'envoi et la première réponse notée dans l'historique."""
    if c.date_envoi is None:
        return None
    reponses = [e.jour for e in c.historique if e.type in EVENEMENTS_REPONSE and e.jour >= c.date_envoi]
    return (min(reponses) - c.date_envoi).days if reponses else None


def chiffres_cles(candidatures: list[Candidature]) -> ChiffresCles:
    envoyees = [c for c in candidatures if _envoyee(c)]
    delais = [d for d in map(_delai_reponse, envoyees) if d is not None]
    return ChiffresCles(
        envoyees=len(envoyees),
        taux_reponse=sum(map(_a_repondu, envoyees)) / len(envoyees) if envoyees else None,
        taux_entretien=sum(map(_a_eu_entretien, envoyees)) / len(envoyees) if envoyees else None,
        delai_moyen_reponse=sum(delais) / len(delais) if delais else None,
    )


def par_source(candidatures: list[Candidature]) -> list[tuple[str, int, int]]:
    """(source, nb envoyées, nb entretiens obtenus), de la source la plus utilisée à la moins utilisée."""
    envoyees = Counter()
    entretiens = Counter()
    for c in filter(_envoyee, candidatures):
        source = c.source or SOURCE_INCONNUE
        envoyees[source] += 1
        entretiens[source] += _a_eu_entretien(c)
    return [(source, nb, entretiens[source]) for source, nb in envoyees.most_common()]


def activite_par_semaine(candidatures: list[Candidature], nb_semaines: int = 12) -> list[tuple[date, int]]:
    """(lundi de la semaine, nb de candidatures envoyées) sur les dernières semaines, semaines vides comprises."""
    lundi_courant = date.today() - timedelta(days=date.today().weekday())
    lundis = [lundi_courant - timedelta(weeks=i) for i in reversed(range(nb_semaines))]
    compteur = Counter(
        c.date_envoi - timedelta(days=c.date_envoi.weekday()) for c in candidatures if c.date_envoi is not None
    )
    return [(lundi, compteur[lundi]) for lundi in lundis]
from collections import Counter

from fastapi import APIRouter, Request

from app.models.candidature import Statut
from app.services import statistiques
from app.services.candidature_service import candidature_service
from app.templating import templates

router = APIRouter()


@router.get("/")
def accueil(request: Request):
    candidatures = candidature_service.lister()
    repartition = candidature_service.repartition_statuts()
    sources = statistiques.par_source(candidatures)
    semaines = statistiques.activite_par_semaine(candidatures)
    graphiques = {
        "statuts": {
            "libelles": [s.libelle for s in repartition],
            "valeurs": list(repartition.values()),
            "couleurs": [s.couleur for s in repartition],
        },
        "sources": {
            "libelles": [source for source, _, _ in sources],
            "envoyees": [nb for _, nb, _ in sources],
            "entretiens": [nb for _, _, nb in sources],
            "couleurs": [Statut.ENVOYE.couleur, Statut.ENTRETIEN.couleur],
        },
        "semaines": {
            "libelles": [lundi.strftime("%d/%m") for lundi, _ in semaines],
            "valeurs": [nb for _, nb in semaines],
            "couleur": Statut.ENVOYE.couleur,
        },
    }
    return templates.TemplateResponse(
        request,
        "accueil.html",
        {
            "a_relancer": candidature_service.a_relancer(),
            "entretiens": candidature_service.entretiens_a_venir(),
            "chiffres": statistiques.chiffres_cles(candidatures),
            "total": len(candidatures),
            "graphiques": graphiques,
        },
    )


@router.get("/candidatures")
def liste_candidatures(request: Request, ouvrir: str | None = None, erreur: str | None = None):
    candidatures = candidature_service.lister()
    return templates.TemplateResponse(
        request,
        "candidatures.html",
        {
            "candidatures": candidatures,
            "compteurs": Counter(c.statut for c in candidatures),
            "ouvrir": ouvrir,
            "erreur": erreur,
        },
    )
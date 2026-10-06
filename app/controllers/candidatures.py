from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from app.models.candidature import Candidature, Statut
from app.models.document import TypeDocument
from app.schemas.candidature import CandidatureForm
from app.schemas.evenement import EvenementForm
from app.services.candidature_service import DocumentInvalide, candidature_service
from app.templating import templates

router = APIRouter(prefix="/candidatures")


def _rediriger(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def _url_retour(retour: str | None, defaut: str) -> str:
    if retour and retour.startswith("/") and not retour.startswith("//"):
        return retour
    return defaut


def _obtenir_ou_404(candidature_id: str) -> Candidature:
    candidature = candidature_service.obtenir(candidature_id)
    if candidature is None:
        raise HTTPException(404, "Candidature introuvable")
    return candidature


def _panneau_formulaire(request: Request, candidature: Candidature, nouvelle: bool):
    return templates.TemplateResponse(
        request,
        "_panneau_formulaire.html",
        {"c": candidature, "nouvelle": nouvelle, "sources": candidature_service.sources()},
    )


# --- Fragments HTML chargés dans le panneau latéral ---

@router.get("/nouvelle/panneau")
def panneau_nouvelle(request: Request):
    return _panneau_formulaire(request, Candidature(entreprise=""), nouvelle=True)


@router.get("/{candidature_id}/panneau")
def panneau_detail(request: Request, candidature_id: str, erreur: str | None = None):
    return templates.TemplateResponse(
        request, "_panneau_detail.html", {"c": _obtenir_ou_404(candidature_id), "erreur": erreur}
    )


@router.get("/{candidature_id}/panneau/modifier")
def panneau_modifier(request: Request, candidature_id: str):
    return _panneau_formulaire(request, _obtenir_ou_404(candidature_id), nouvelle=False)


# --- Actions (formulaires HTML, redirection après POST) ---

@router.post("")
def creer(form: Annotated[CandidatureForm, Form()]):
    candidature = candidature_service.creer(form)
    return _rediriger(f"/candidatures?ouvrir={candidature.id}")


@router.post("/{candidature_id}")
def modifier(candidature_id: str, form: Annotated[CandidatureForm, Form()]):
    if candidature_service.modifier(candidature_id, form) is None:
        raise HTTPException(404, "Candidature introuvable")
    return _rediriger(f"/candidatures?ouvrir={candidature_id}")


@router.post("/{candidature_id}/statut")
def changer_statut(candidature_id: str, statut: Annotated[Statut, Form()]):
    candidature_service.changer_statut(candidature_id, statut)
    return _rediriger("/candidatures")


@router.post("/{candidature_id}/relancee")
def marquer_relancee(candidature_id: str, retour: Annotated[str | None, Form()] = None):
    candidature_service.marquer_relancee(candidature_id)
    return _rediriger(_url_retour(retour, "/candidatures"))


@router.post("/{candidature_id}/supprimer")
def supprimer(candidature_id: str):
    candidature_service.supprimer(candidature_id)
    return _rediriger("/candidatures")


# --- Historique (échanges, entretiens, notes) ---

@router.post("/{candidature_id}/historique")
def ajouter_evenement(candidature_id: str, form: Annotated[EvenementForm, Form()]):
    if candidature_service.ajouter_evenement(candidature_id, form) is None:
        raise HTTPException(404, "Candidature introuvable")
    return _rediriger(f"/candidatures?ouvrir={candidature_id}")


@router.post("/{candidature_id}/historique/{evenement_id}/supprimer")
def supprimer_evenement(candidature_id: str, evenement_id: str):
    candidature_service.supprimer_evenement(candidature_id, evenement_id)
    return _rediriger(f"/candidatures?ouvrir={candidature_id}")


# --- Documents (CV, lettre de motivation) ---

@router.get("/{candidature_id}/documents/{type_document}")
def voir_document(candidature_id: str, type_document: TypeDocument):
    document = candidature_service.document(candidature_id, type_document)
    if document is None:
        raise HTTPException(404, "Document introuvable")
    chemin, nom = document
    # « inline » : le PDF s'affiche dans le navigateur au lieu d'être téléchargé.
    return FileResponse(chemin, media_type="application/pdf", filename=nom, content_disposition_type="inline")


@router.post("/{candidature_id}/documents/{type_document}")
async def envoyer_document(candidature_id: str, type_document: TypeDocument, fichier: UploadFile):
    contenu = await fichier.read()
    try:
        if candidature_service.ajouter_document(candidature_id, type_document, fichier.filename or "", contenu) is None:
            raise HTTPException(404, "Candidature introuvable")
    except DocumentInvalide as e:
        return _rediriger(f"/candidatures?ouvrir={candidature_id}&erreur={quote(str(e))}")
    return _rediriger(f"/candidatures?ouvrir={candidature_id}")


@router.post("/{candidature_id}/documents/{type_document}/supprimer")
def supprimer_document(candidature_id: str, type_document: TypeDocument):
    candidature_service.supprimer_document(candidature_id, type_document)
    return _rediriger(f"/candidatures?ouvrir={candidature_id}")
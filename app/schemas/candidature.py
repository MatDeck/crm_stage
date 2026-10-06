from datetime import date

from pydantic import BaseModel, field_validator

from app.models.candidature import Statut


class CandidatureForm(BaseModel):
    """Champs saisis dans le formulaire du panneau de détail."""

    entreprise: str
    site_entreprise: str = ""
    poste: str = ""
    lieu: str = ""
    source: str = ""
    statut: Statut = Statut.A_ENVOYER
    date_envoi: date | None = None
    contact_nom: str = ""
    contact_email: str = ""
    contact_telephone: str = ""
    sujet: str = ""
    url_offre: str = ""
    description: str = ""
    salaire_min: int | None = None
    salaire_max: int | None = None

    @field_validator("date_envoi", "salaire_min", "salaire_max", mode="before")
    @classmethod
    def vide_en_none(cls, valeur):
        # Un champ HTML laissé vide arrive sous forme de chaîne vide.
        return None if valeur == "" else valeur

    @field_validator("entreprise", "source", mode="after")
    @classmethod
    def nettoyer(cls, valeur: str) -> str:
        return valeur.strip()

    @field_validator("site_entreprise", "url_offre", mode="after")
    @classmethod
    def normaliser_url(cls, valeur: str) -> str:
        # « www.acme.fr » devient « https://www.acme.fr » ; seuls http(s) sont acceptés comme liens.
        valeur = valeur.strip()
        if valeur and not valeur.lower().startswith(("http://", "https://")):
            valeur = "https://" + valeur
        return valeur
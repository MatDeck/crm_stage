from datetime import date, time

from pydantic import BaseModel, field_validator

from app.models.evenement import TypeEvenement


class EvenementForm(BaseModel):
    """Champs du formulaire « Ajouter un échange » de la fiche."""

    type: TypeEvenement
    jour: date
    heure: time | None = None
    lieu: str = ""
    note: str = ""

    @field_validator("heure", mode="before")
    @classmethod
    def vide_en_none(cls, valeur):
        return None if valeur == "" else valeur

    @field_validator("lieu", "note", mode="after")
    @classmethod
    def nettoyer(cls, valeur: str) -> str:
        return valeur.strip()
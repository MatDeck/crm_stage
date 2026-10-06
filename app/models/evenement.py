from datetime import date, time
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class TypeEvenement(str, Enum):
    ENVOI = "envoi"
    RELANCE = "relance"
    REPONSE = "reponse"
    APPEL = "appel"
    ENTRETIEN = "entretien"
    NOTE = "note"

    @property
    def libelle(self) -> str:
        return EVENEMENT_LIBELLES[self]

    @property
    def couleur(self) -> str:
        return EVENEMENT_COULEURS[self]


EVENEMENT_LIBELLES = {
    TypeEvenement.ENVOI: "Envoi",
    TypeEvenement.RELANCE: "Relance",
    TypeEvenement.REPONSE: "Réponse reçue",
    TypeEvenement.APPEL: "Appel",
    TypeEvenement.ENTRETIEN: "Entretien",
    TypeEvenement.NOTE: "Note",
}

EVENEMENT_COULEURS = {
    TypeEvenement.ENVOI: "#3b82f6",
    TypeEvenement.RELANCE: "#f59e0b",
    TypeEvenement.REPONSE: "#22c55e",
    TypeEvenement.APPEL: "#0ea5e9",
    TypeEvenement.ENTRETIEN: "#8b5cf6",
    TypeEvenement.NOTE: "#64748b",
}


class Evenement(BaseModel):
    """Une entrée de l'historique d'une candidature (échange, entretien, note…)."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    type: TypeEvenement
    jour: date
    heure: time | None = None
    lieu: str = ""  # adresse ou lien visio, surtout pour les entretiens
    note: str = ""

    @property
    def moment(self) -> tuple[date, time]:
        """Clé de tri chronologique."""
        return self.jour, self.heure or time.min

    @property
    def entretien_a_venir(self) -> bool:
        return self.type == TypeEvenement.ENTRETIEN and self.jour >= date.today()

    @property
    def lieu_est_lien(self) -> bool:
        return self.lieu.startswith(("http://", "https://"))
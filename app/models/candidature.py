from datetime import date
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.models.evenement import Evenement, TypeEvenement


class Statut(str, Enum):
    A_ENVOYER = "a_envoyer"
    ENVOYE = "envoye"
    A_RELANCER = "a_relancer"
    SANS_REPONSE = "sans_reponse"
    ENTRETIEN = "entretien"
    ACCEPTE = "accepte"
    REFUSE = "refuse"
    ABANDONNE = "abandonne"

    @property
    def libelle(self) -> str:
        return STATUT_LIBELLES[self]

    @property
    def couleur(self) -> str:
        return STATUT_COULEURS[self]

    @property
    def ordre(self) -> int:
        return list(Statut).index(self)


STATUT_LIBELLES = {
    Statut.A_ENVOYER: "À envoyer",
    Statut.ENVOYE: "Envoyée",
    Statut.A_RELANCER: "À relancer",
    Statut.SANS_REPONSE: "Sans réponse",
    Statut.ENTRETIEN: "Entretien",
    Statut.ACCEPTE: "Acceptée",
    Statut.REFUSE: "Refusée",
    Statut.ABANDONNE: "Abandonnée",
}

STATUT_COULEURS = {
    Statut.A_ENVOYER: "#94a3b8",
    Statut.ENVOYE: "#3b82f6",
    Statut.A_RELANCER: "#f59e0b",
    Statut.SANS_REPONSE: "#a16207",
    Statut.ENTRETIEN: "#8b5cf6",
    Statut.ACCEPTE: "#22c55e",
    Statut.REFUSE: "#ef4444",
    Statut.ABANDONNE: "#64748b",
}


class Candidature(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    entreprise: str
    site_entreprise: str = ""
    poste: str = ""
    lieu: str = ""
    source: str = ""
    statut: Statut = Statut.A_ENVOYER

    date_creation: date = Field(default_factory=date.today)
    date_envoi: date | None = None

    contact_nom: str = ""
    contact_email: str = ""
    contact_telephone: str = ""

    sujet: str = ""
    url_offre: str = ""
    description: str = ""
    salaire_min: int | None = None
    salaire_max: int | None = None

    cv_fichier: str | None = None
    lettre_fichier: str | None = None

    historique: list[Evenement] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrer_date_relance(cls, donnees):
        if isinstance(donnees, dict) and "date_relance" in donnees:
            donnees = dict(donnees)
            date_relance = donnees.pop("date_relance")
            if date_relance:
                relance = {"type": TypeEvenement.RELANCE, "jour": date_relance}
                donnees["historique"] = [*donnees.get("historique", []), relance]
        return donnees

    @property
    def historique_chronologique(self) -> list[Evenement]:
        """Du plus récent au plus ancien."""
        return sorted(self.historique, key=lambda e: e.moment, reverse=True)

    @property
    def nb_relances(self) -> int:
        return sum(1 for e in self.historique if e.type == TypeEvenement.RELANCE)

    @property
    def date_relance(self) -> date | None:
        """Date de la dernière relance, d'après l'historique."""
        return max((e.jour for e in self.historique if e.type == TypeEvenement.RELANCE), default=None)

    @property
    def dernier_contact(self) -> date | None:
        """Envoi ou dernier échange passé de l'historique (les notes et les entretiens à venir ne comptent pas)."""
        echanges = (
            e.jour for e in self.historique if e.type != TypeEvenement.NOTE and e.jour <= date.today()
        )
        return max((d for d in (self.date_envoi, *echanges) if d), default=None)

    @property
    def jours_sans_nouvelles(self) -> int | None:
        if self.dernier_contact is None:
            return None
        return (date.today() - self.dernier_contact).days
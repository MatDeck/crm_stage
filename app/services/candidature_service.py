from collections import Counter
from datetime import date
from pathlib import Path

from app.config import (
    DATA_DIR,
    DELAI_SANS_REPONSE_JOURS,
    DELAIS_RELANCE_JOURS,
    SOURCES_PAR_DEFAUT,
    TAILLE_MAX_DOCUMENT_MO,
)
from app.dao.candidature_dao import CandidatureDao
from app.dao.document_dao import DocumentDao
from app.dao.json_store import JsonStore
from app.dao.source_dao import SourceDao
from app.models.candidature import Candidature, Statut
from app.models.document import TypeDocument
from app.models.evenement import Evenement, TypeEvenement
from app.schemas.candidature import CandidatureForm
from app.schemas.evenement import EvenementForm


class DocumentInvalide(ValueError):
    """Fichier refusé (pas un PDF, trop gros…). Le message est affiché tel quel à l'utilisateur."""


class CandidatureService:
    def __init__(
        self,
        candidature_dao: CandidatureDao,
        source_dao: SourceDao,
        document_dao: DocumentDao,
        delais_relance_jours: list[int],
        delai_sans_reponse_jours: int,
        taille_max_document_mo: int,
    ):
        self.candidature_dao = candidature_dao
        self.source_dao = source_dao
        self.document_dao = document_dao
        self.delais_relance_jours = delais_relance_jours
        self.delai_sans_reponse_jours = delai_sans_reponse_jours
        self.taille_max_document_mo = taille_max_document_mo

    # --- Lecture ---

    def lister(self) -> list[Candidature]:
        candidatures = [self._statut_effectif(c) for c in self.candidature_dao.lister()]
        return sorted(candidatures, key=lambda c: c.date_creation, reverse=True)

    def obtenir(self, candidature_id: str) -> Candidature | None:
        candidature = self.candidature_dao.trouver(candidature_id)
        return self._statut_effectif(candidature) if candidature else None

    def a_relancer(self) -> list[Candidature]:
        candidatures = [c for c in self.lister() if c.statut == Statut.A_RELANCER]
        return sorted(candidatures, key=lambda c: c.dernier_contact or date.min)

    def entretiens_a_venir(self) -> list[tuple[Candidature, Evenement]]:
        entretiens = [(c, e) for c in self.lister() for e in c.historique if e.entretien_a_venir]
        return sorted(entretiens, key=lambda ce: ce[1].moment)

    def repartition_statuts(self) -> dict[Statut, int]:
        compteur = Counter(c.statut for c in self.lister())
        return {statut: compteur[statut] for statut in Statut}

    def sources(self) -> list[str]:
        return self.source_dao.lister()

    def document(self, candidature_id: str, type_document: TypeDocument) -> tuple[Path, str] | None:
        """Chemin du PDF et son nom d'origine, ou None s'il n'existe pas."""
        candidature = self.candidature_dao.trouver(candidature_id)
        nom = getattr(candidature, type_document.champ) if candidature else None
        chemin = self.document_dao.trouver(candidature_id, type_document) if nom else None
        return (chemin, nom) if chemin else None

    # --- Écriture ---

    def creer(self, form: CandidatureForm) -> Candidature:
        candidature = self._completer(Candidature(**form.model_dump()))
        self._enregistrer(candidature)
        return candidature

    def modifier(self, candidature_id: str, form: CandidatureForm) -> Candidature | None:
        return self._mettre_a_jour(candidature_id, form.model_dump())

    def changer_statut(self, candidature_id: str, statut: Statut) -> Candidature | None:
        return self._mettre_a_jour(candidature_id, {"statut": statut})

    def marquer_relancee(self, candidature_id: str) -> Candidature | None:
        return self._ajouter_a_historique(candidature_id, Evenement(type=TypeEvenement.RELANCE, jour=date.today()))

    def ajouter_evenement(self, candidature_id: str, form: EvenementForm) -> Candidature | None:
        return self._ajouter_a_historique(candidature_id, Evenement(**form.model_dump()))

    def supprimer_evenement(self, candidature_id: str, evenement_id: str) -> Candidature | None:
        existante = self.candidature_dao.trouver(candidature_id)
        if existante is None:
            return None
        historique = [e for e in existante.historique if e.id != evenement_id]
        return self._mettre_a_jour(candidature_id, {"historique": historique})

    def supprimer(self, candidature_id: str) -> None:
        if self.candidature_dao.trouver(candidature_id) is None:
            return
        self.candidature_dao.supprimer(candidature_id)
        self.document_dao.supprimer_tous(candidature_id)

    def ajouter_document(
        self, candidature_id: str, type_document: TypeDocument, nom_fichier: str, contenu: bytes
    ) -> Candidature | None:
        """Enregistre (ou remplace) le PDF. Lève DocumentInvalide si le fichier est refusé."""
        if self.candidature_dao.trouver(candidature_id) is None:
            return None
        if not contenu.startswith(b"%PDF-"):
            raise DocumentInvalide("Le fichier doit être un PDF.")
        if len(contenu) > self.taille_max_document_mo * 1024 * 1024:
            raise DocumentInvalide(f"Le fichier dépasse {self.taille_max_document_mo} Mo.")
        self.document_dao.enregistrer(candidature_id, type_document, contenu)
        nom = Path(nom_fichier).name or f"{type_document.value}.pdf"
        return self._mettre_a_jour(candidature_id, {type_document.champ: nom})

    def supprimer_document(self, candidature_id: str, type_document: TypeDocument) -> Candidature | None:
        if self.candidature_dao.trouver(candidature_id) is None:
            return None
        self.document_dao.supprimer(candidature_id, type_document)
        return self._mettre_a_jour(candidature_id, {type_document.champ: None})

    # --- Règles métier ---

    def _statut_effectif(self, candidature: Candidature) -> Candidature:
        """Relances échelonnées d'une candidature envoyée restée sans nouvelles.

        Tant qu'il reste des relances prévues, elle passe « à relancer » après le délai correspondant ;
        après la dernière, elle passe « sans réponse ». Calculé à la lecture, rien n'est enregistré.
        """
        if candidature.statut != Statut.ENVOYE or candidature.jours_sans_nouvelles is None:
            return candidature
        if candidature.nb_relances < len(self.delais_relance_jours):
            delai, statut = self.delais_relance_jours[candidature.nb_relances], Statut.A_RELANCER
        else:
            delai, statut = self.delai_sans_reponse_jours, Statut.SANS_REPONSE
        if candidature.jours_sans_nouvelles >= delai:
            return candidature.model_copy(update={"statut": statut})
        return candidature

    @staticmethod
    def _completer(candidature: Candidature) -> Candidature:
        if candidature.statut == Statut.ENVOYE and candidature.date_envoi is None:
            return candidature.model_copy(update={"date_envoi": date.today()})
        return candidature

    def _ajouter_a_historique(self, candidature_id: str, evenement: Evenement) -> Candidature | None:
        existante = self.candidature_dao.trouver(candidature_id)
        if existante is None:
            return None
        changements = {"historique": [*existante.historique, evenement]}
        # Une relance remet le compteur à zéro : la candidature redevient « envoyée » en attente de réponse.
        if evenement.type == TypeEvenement.RELANCE and existante.statut in (Statut.A_RELANCER, Statut.SANS_REPONSE):
            changements["statut"] = Statut.ENVOYE
        return self._mettre_a_jour(candidature_id, changements)

    def _mettre_a_jour(self, candidature_id: str, changements: dict) -> Candidature | None:
        existante = self.candidature_dao.trouver(candidature_id)
        if existante is None:
            return None
        candidature = self._completer(existante.model_copy(update=changements))
        self._enregistrer(candidature)
        return candidature

    def _enregistrer(self, candidature: Candidature) -> None:
        self.candidature_dao.enregistrer(candidature)
        self.source_dao.ajouter(candidature.source)


candidature_service = CandidatureService(
    CandidatureDao(JsonStore(DATA_DIR / "candidatures.json", [])),
    SourceDao(JsonStore(DATA_DIR / "sources.json", SOURCES_PAR_DEFAUT)),
    DocumentDao(DATA_DIR / "documents"),
    DELAIS_RELANCE_JOURS,
    DELAI_SANS_REPONSE_JOURS,
    TAILLE_MAX_DOCUMENT_MO,
)
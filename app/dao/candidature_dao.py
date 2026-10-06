from app.dao.json_store import JsonStore
from app.models.candidature import Candidature


class CandidatureDao:

    def __init__(self, store: JsonStore):
        self.store = store

    def lister(self) -> list[Candidature]:
        return [Candidature.model_validate(d) for d in self.store.lire()]

    def trouver(self, candidature_id: str) -> Candidature | None:
        return next((c for c in self.lister() if c.id == candidature_id), None)

    def enregistrer(self, candidature: Candidature) -> None:
        candidatures = [c for c in self.lister() if c.id != candidature.id]
        candidatures.append(candidature)
        self._sauver(candidatures)

    def supprimer(self, candidature_id: str) -> None:
        self._sauver([c for c in self.lister() if c.id != candidature_id])

    def _sauver(self, candidatures: list[Candidature]) -> None:
        self.store.ecrire([c.model_dump(mode="json") for c in candidatures])
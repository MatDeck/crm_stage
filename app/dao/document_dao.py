import shutil
from pathlib import Path

from app.models.document import TypeDocument


class DocumentDao:
    """Fichiers PDF des candidatures, rangés dans <dossier>/<id candidature>/<type>.pdf."""

    def __init__(self, dossier: Path):
        self.dossier = dossier

    def _chemin(self, candidature_id: str, type_document: TypeDocument) -> Path:
        return self.dossier / candidature_id / f"{type_document.value}.pdf"

    def enregistrer(self, candidature_id: str, type_document: TypeDocument, contenu: bytes) -> None:
        chemin = self._chemin(candidature_id, type_document)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(contenu)

    def trouver(self, candidature_id: str, type_document: TypeDocument) -> Path | None:
        chemin = self._chemin(candidature_id, type_document)
        return chemin if chemin.exists() else None

    def supprimer(self, candidature_id: str, type_document: TypeDocument) -> None:
        self._chemin(candidature_id, type_document).unlink(missing_ok=True)

    def supprimer_tous(self, candidature_id: str) -> None:
        shutil.rmtree(self.dossier / candidature_id, ignore_errors=True)
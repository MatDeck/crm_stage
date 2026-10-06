from enum import Enum


class TypeDocument(str, Enum):
    CV = "cv"
    LETTRE = "lettre"

    @property
    def libelle(self) -> str:
        return {TypeDocument.CV: "CV", TypeDocument.LETTRE: "Lettre de motivation"}[self]

    @property
    def champ(self) -> str:
        """Attribut de `Candidature` qui contient le nom d'origine du fichier."""
        return f"{self.value}_fichier"
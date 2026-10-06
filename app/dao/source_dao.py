from app.dao.json_store import JsonStore


class SourceDao:

    def __init__(self, store: JsonStore):
        self.store = store

    def lister(self) -> list[str]:
        return self.store.lire()

    def ajouter(self, source: str) -> None:
        sources = self.lister()
        if source and source.casefold() not in {s.casefold() for s in sources}:
            sources.append(source)
            self.store.ecrire(sources)
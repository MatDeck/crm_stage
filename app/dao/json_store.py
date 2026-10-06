import copy
import json
import threading
from pathlib import Path


class JsonStore:

    def __init__(self, chemin: Path, defaut):
        self.chemin = chemin
        self.defaut = defaut
        self._verrou = threading.Lock()

    def lire(self):
        if not self.chemin.exists():
            return copy.deepcopy(self.defaut)
        with self.chemin.open(encoding="utf-8") as f:
            return json.load(f)

    def ecrire(self, donnees) -> None:
        with self._verrou:
            self.chemin.parent.mkdir(parents=True, exist_ok=True)
            temporaire = self.chemin.with_suffix(".tmp")
            temporaire.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
            temporaire.replace(self.chemin)
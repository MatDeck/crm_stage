from datetime import date, time

from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.models.candidature import Statut
from app.models.document import TypeDocument
from app.models.evenement import TypeEvenement

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def date_fr(valeur: date | None) -> str:
    return valeur.strftime("%d/%m/%Y") if valeur else "—"


def heure_fr(valeur: time | None) -> str:
    return valeur.strftime("%Hh%M") if valeur else ""


def pourcentage(valeur: float | None) -> str:
    return f"{round(valeur * 100)} %" if valeur is not None else "—"


def decimal_fr(valeur: float | None) -> str:
    return f"{valeur:.1f}".replace(".", ",") if valeur is not None else "—"


def statique(chemin: str) -> str:
    """URL d'un fichier de static/ qui change à chaque modification, pour que le navigateur ne garde pas l'ancien."""
    version = int((BASE_DIR / "static" / chemin).stat().st_mtime)
    return f"/static/{chemin}?v={version}"


templates.env.filters["date_fr"] = date_fr
templates.env.filters["heure_fr"] = heure_fr
templates.env.filters["pourcentage"] = pourcentage
templates.env.filters["decimal_fr"] = decimal_fr
templates.env.globals["statuts"] = list(Statut)
templates.env.globals["types_documents"] = list(TypeDocument)
templates.env.globals["types_evenements"] = list(TypeEvenement)
templates.env.globals["aujourd_hui"] = date.today
templates.env.globals["statique"] = statique
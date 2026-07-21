import os
import sys
from pathlib import Path

APP_DIR_NAME = "GoPro-Tracking"


def user_data_root() -> Path:
    """
    Dossier où l'app stocke ce qui doit survivre à une mise à jour/réinstallation
    (profils, résultats de tracking) : %APPDATA%\\GoPro-Tracking sous Windows, ou
    ~/.gopro-tracking ailleurs. Indispensable une fois packagée (Program Files est en
    lecture seule pour un utilisateur standard) — utilisé aussi en développement pour
    ne dépendre que d'un seul chemin, testé dans les deux cas.
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def resource_path(relative_path: str) -> Path:
    """
    Chemin vers une ressource embarquée en lecture seule (icône, etc.) : le dossier
    d'extraction PyInstaller une fois packagée, celui du script en développement.
    """
    base = Path(getattr(sys, "_MEIPASS", None) or Path(__file__).parent)
    return base / relative_path


def default_tracking_output_path() -> str:
    return str(user_data_root() / "data" / "tracking.json")


def install_dir() -> Path:
    """
    Dossier où se trouve le code de l'app : celui de l'exécutable une fois packagée
    (PyInstaller), celui du script en développement.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

import json
import shutil
from pathlib import Path

from app_paths import install_dir, user_data_root

PROFILES_ROOT = user_data_root() / "profiles"
_LEGACY_PROFILES_ROOT = install_dir() / "profiles"


def _migrate_legacy_profiles():
    """
    Avant cette version, les profils étaient stockés à côté du script/exécutable — un
    dossier en lecture seule une fois l'app installée (Program Files). On les copie une
    seule fois vers le nouveau dossier utilisateur, sans jamais toucher/supprimer
    l'ancien dossier.
    """
    if PROFILES_ROOT.exists() or not _LEGACY_PROFILES_ROOT.exists():
        return
    shutil.copytree(_LEGACY_PROFILES_ROOT, PROFILES_ROOT)


_migrate_legacy_profiles()


def _dir_for(kind: str) -> Path:
    path = PROFILES_ROOT / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_profiles(kind: str) -> list[str]:
    return sorted(path.stem for path in _dir_for(kind).glob("*.json"))


def load_profile(kind: str, name: str) -> dict:
    path = _dir_for(kind) / f"{name}.json"
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_profile(kind: str, name: str, data: dict) -> Path:
    path = _dir_for(kind) / f"{name}.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    return path

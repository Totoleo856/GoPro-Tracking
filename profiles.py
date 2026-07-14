import json
from pathlib import Path

PROFILES_ROOT = Path(__file__).parent / "profiles"


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

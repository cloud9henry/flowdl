import json
from pathlib import Path

from flowdl.utils.errors import PresetNotFoundError


def _preset_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "presets.json"


def _user_preset_file_path() -> Path:
    return Path.home() / ".config" / "flowdl" / "presets.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file_obj:
        data = json.load(file_obj)
    if not isinstance(data, dict):
        raise RuntimeError(f"Preset file must contain a JSON object: {path}")
    return data


def load_presets() -> dict:
    presets = _load_json(_preset_file_path())
    user_preset_path = _user_preset_file_path()
    if user_preset_path.exists():
        user_presets = _load_json(user_preset_path)
        # User presets override built-in presets on key collision.
        presets.update(user_presets)
    return presets


def get_preset(name: str) -> dict:
    presets = load_presets()
    if name not in presets:
        available = ", ".join(sorted(presets.keys()))
        raise PresetNotFoundError(f"Preset '{name}' not found. Available presets: {available}")
    return presets[name]

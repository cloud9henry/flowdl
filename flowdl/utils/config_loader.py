import json
from pathlib import Path

from flowdl.utils.errors import PresetNotFoundError


def _preset_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "presets.json"


def load_presets() -> dict:
    with _preset_file_path().open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def get_preset(name: str) -> dict:
    presets = load_presets()
    if name not in presets:
        available = ", ".join(sorted(presets.keys()))
        raise PresetNotFoundError(f"Preset '{name}' not found. Available presets: {available}")
    return presets[name]


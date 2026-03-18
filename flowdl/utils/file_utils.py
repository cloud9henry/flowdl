from pathlib import Path


def ensure_directory(path: str | Path) -> Path:
    target = Path(path).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    return target


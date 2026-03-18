from pathlib import Path
import shutil

from flowdl.utils.file_utils import ensure_directory


def organise_output(file_path: str, preset: dict) -> str:
    output_dir = ensure_directory(preset["output_dir"])
    source = Path(file_path)
    destination = output_dir / source.name
    shutil.move(str(source), str(destination))
    return str(destination)


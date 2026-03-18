from pathlib import Path
import shutil

from flowdl.utils.file_utils import ensure_directory
from flowdl.utils.naming import ensure_unique_path, render_filename_template


def organise_output(
    file_path: str,
    preset: dict,
    metadata: dict[str, str] | None = None,
    preset_name: str | None = None,
) -> str:
    output_dir = ensure_directory(preset["output_dir"])
    source = Path(file_path)
    filename_template = preset.get("filename_template")
    if filename_template:
        destination_name = render_filename_template(
            filename_template,
            metadata=metadata,
            preset_name=preset_name,
            source_file_path=str(source),
        )
    else:
        destination_name = source.name
    destination = ensure_unique_path(output_dir / destination_name)
    shutil.move(str(source), str(destination))
    return str(destination)

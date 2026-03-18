import re
import string
from pathlib import Path


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1F]')
WHITESPACE_RUN = re.compile(r"\s+")

ALLOWED_TEMPLATE_FIELDS = {
    "title",
    "uploader",
    "channel",
    "id",
    "upload_date",
    "preset",
    "ext",
}


def sanitize_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("-", name)
    cleaned = WHITESPACE_RUN.sub(" ", cleaned).strip().strip(".")
    return cleaned


def render_filename_template(
    template: str,
    metadata: dict[str, str] | None,
    preset_name: str | None,
    source_file_path: str,
) -> str:
    metadata = metadata or {}
    source = Path(source_file_path)
    ext = source.suffix.lstrip(".")
    fallback_title = source.stem

    formatter = string.Formatter()
    for _, field_name, _, _ in formatter.parse(template):
        if field_name and field_name not in ALLOWED_TEMPLATE_FIELDS:
            allowed = ", ".join(sorted(ALLOWED_TEMPLATE_FIELDS))
            raise RuntimeError(f"Unknown template key '{field_name}'. Allowed keys: {allowed}")

    context = {
        "title": metadata.get("title", fallback_title),
        "uploader": metadata.get("uploader", ""),
        "channel": metadata.get("channel", ""),
        "id": metadata.get("id", ""),
        "upload_date": metadata.get("upload_date", ""),
        "preset": preset_name or "",
        "ext": ext,
    }

    rendered = template.format(**context)
    rendered = sanitize_filename(rendered)
    if not rendered:
        rendered = sanitize_filename(source.name) or source.name

    if "." not in rendered and ext:
        rendered = f"{rendered}.{ext}"

    return rendered


def ensure_unique_path(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


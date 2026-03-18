from pathlib import Path
from urllib.parse import urlparse

from flowdl.core.downloader import download_media
from flowdl.integrations.ffmpeg_wrapper import extract_audio_for_transcription
from flowdl.integrations.whispercpp_wrapper import transcribe_with_whispercpp


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def run_transcription(
    source: str,
    model_path: str,
    output_dir: str = "Transcripts",
    language: str | None = None,
) -> tuple[str, str]:
    output_root = Path(output_dir).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)

    source_path: Path
    cleanup_paths: list[Path] = []
    metadata: dict[str, str] = {}
    if _is_url(source):
        downloaded = download_media(source, {"mode": "audio"})
        source_path = Path(downloaded.file_path)
        cleanup_paths.append(source_path)
        metadata = downloaded.metadata
    else:
        source_path = Path(source).expanduser()
        if not source_path.exists():
            raise RuntimeError(f"Input file not found: {source}")

    stem = metadata.get("title") or source_path.stem
    transcript_stem = (stem or "transcript").replace("/", "-").strip()
    audio_for_transcribe = output_root / f"{transcript_stem}.wav"
    output_prefix = output_root / transcript_stem

    wav_path = Path(extract_audio_for_transcription(str(source_path), str(audio_for_transcribe)))
    cleanup_paths.append(wav_path)

    txt_path, json_path = transcribe_with_whispercpp(
        input_audio=str(wav_path),
        model_path=model_path,
        output_prefix=str(output_prefix),
        language=language,
    )

    for path in cleanup_paths:
        if path.exists():
            path.unlink()

    return txt_path, json_path


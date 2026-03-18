import subprocess
from pathlib import Path

from flowdl.utils.errors import DependencyMissingError


def _run_ffmpeg(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise DependencyMissingError("ffmpeg is not installed or not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"ffmpeg command failed: {stderr}") from exc


def convert_audio(input_file: str, output_format: str = "mp3", bitrate: str = "192k") -> str:
    source = Path(input_file)
    output = source.with_suffix(f".{output_format}")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ab",
        bitrate,
        str(output),
    ]
    _run_ffmpeg(command)
    return str(output)


def compress_audio(input_file: str, bitrate: str = "96k") -> str:
    source = Path(input_file)
    output = source.with_name(f"{source.stem}.compressed{source.suffix}")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-ab",
        bitrate,
        str(output),
    ]
    _run_ffmpeg(command)
    return str(output)


def compress_video(input_file: str, crf: str = "28") -> str:
    source = Path(input_file)
    output = source.with_name(f"{source.stem}.compressed{source.suffix}")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vcodec",
        "libx264",
        "-crf",
        crf,
        "-preset",
        "medium",
        "-acodec",
        "aac",
        str(output),
    ]
    _run_ffmpeg(command)
    return str(output)


def trim_media(input_file: str, start: str, end: str, output_file: str | None = None) -> str:
    source = Path(input_file)
    if output_file is None:
        output_path = source.with_name(f"{source.stem}.trimmed{source.suffix}")
    else:
        output_path = Path(output_file)

    command = [
        "ffmpeg",
        "-y",
        "-ss",
        start,
        "-to",
        end,
        "-i",
        str(source),
        "-c",
        "copy",
        str(output_path),
    ]
    _run_ffmpeg(command)
    return str(output_path)


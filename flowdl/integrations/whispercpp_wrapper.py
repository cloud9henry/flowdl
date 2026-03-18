import subprocess
from pathlib import Path

from flowdl.utils.errors import DependencyMissingError


def transcribe_with_whispercpp(
    input_audio: str,
    model_path: str,
    output_prefix: str,
    language: str | None = None,
    binary: str = "whisper-cli",
) -> tuple[str, str]:
    command = [
        binary,
        "-m",
        model_path,
        "-f",
        input_audio,
        "-of",
        output_prefix,
        "-otxt",
        "-oj",
    ]
    if language:
        command.extend(["-l", language])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise DependencyMissingError(
            "whisper.cpp binary not found. Install whisper.cpp and ensure 'whisper-cli' is on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"whisper.cpp failed: {stderr}") from exc

    output_base = Path(output_prefix)
    return str(output_base.with_suffix(".txt")), str(output_base.with_suffix(".json"))


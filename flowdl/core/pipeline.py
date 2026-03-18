from pathlib import Path

from flowdl.core.downloader import download_media
from flowdl.core.organiser import organise_output
from flowdl.core.processor import postprocess
from flowdl.integrations.ffmpeg_wrapper import convert_audio


def run_pipeline(
    url: str,
    preset: dict,
    audio_sidecar: bool = False,
    preset_name: str | None = None,
) -> str:
    downloaded = download_media(url, preset)
    processed_file = postprocess(downloaded.file_path, preset)
    final_path = organise_output(
        processed_file,
        preset,
        metadata=downloaded.metadata,
        preset_name=preset_name,
    )

    if audio_sidecar and preset.get("mode") == "video":
        audio_format = preset.get("audio_format", "mp3")
        audio_file = convert_audio(final_path, output_format=audio_format)
        audio_output_dir = preset.get(
            "audio_output_dir",
            str(Path(preset["output_dir"]) / "Audio"),
        )
        audio_preset = {
            "output_dir": audio_output_dir,
            "filename_template": preset.get("filename_template"),
        }
        organise_output(audio_file, audio_preset, metadata=downloaded.metadata, preset_name=preset_name)

    return final_path

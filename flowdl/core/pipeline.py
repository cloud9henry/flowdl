from pathlib import Path

from flowdl.core.downloader import download_media
from flowdl.core.organiser import organise_output
from flowdl.core.processor import postprocess
from flowdl.integrations.ffmpeg_wrapper import convert_audio


def run_pipeline(url: str, preset: dict, audio_sidecar: bool = False) -> str:
    file_path = download_media(url, preset)
    processed_file = postprocess(file_path, preset)
    final_path = organise_output(processed_file, preset)

    if audio_sidecar and preset.get("mode") == "video":
        audio_format = preset.get("audio_format", "mp3")
        audio_file = convert_audio(processed_file, output_format=audio_format)
        audio_output_dir = preset.get(
            "audio_output_dir",
            str(Path(preset["output_dir"]) / "Audio"),
        )
        audio_preset = {"output_dir": audio_output_dir}
        organise_output(audio_file, audio_preset)

    return final_path

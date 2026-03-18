from pathlib import Path

from flowdl.integrations.ffmpeg_wrapper import compress_audio, compress_video, convert_audio


def postprocess(file_path: str, preset: dict) -> str:
    mode = preset.get("mode")
    output_file = file_path

    if mode == "audio":
        output_format = preset.get("format", "mp3")
        if Path(file_path).suffix.lower() != f".{output_format}":
            output_file = convert_audio(file_path, output_format=output_format)

        if preset.get("compress"):
            output_file = compress_audio(output_file)

        return output_file

    if mode == "video" and preset.get("compress"):
        return compress_video(file_path)

    return output_file


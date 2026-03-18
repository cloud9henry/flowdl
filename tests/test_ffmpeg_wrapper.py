import subprocess
import unittest
from unittest.mock import patch

from flowdl.integrations.ffmpeg_wrapper import (
    _run_ffmpeg,
    compress_audio,
    compress_video,
    convert_audio,
    extract_audio_for_transcription,
    trim_media,
)
from flowdl.utils.errors import DependencyMissingError


class FFmpegWrapperTests(unittest.TestCase):
    def test_run_ffmpeg_invokes_subprocess(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper.subprocess.run") as run_mock:
            _run_ffmpeg(["ffmpeg", "-version"])
        run_mock.assert_called_once_with(
            ["ffmpeg", "-version"],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_run_ffmpeg_maps_missing_binary_error(self) -> None:
        with patch(
            "flowdl.integrations.ffmpeg_wrapper.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with self.assertRaises(DependencyMissingError):
                _run_ffmpeg(["ffmpeg"])

    def test_run_ffmpeg_maps_called_process_error(self) -> None:
        error = subprocess.CalledProcessError(1, ["ffmpeg"], stderr="bad input")
        with patch("flowdl.integrations.ffmpeg_wrapper.subprocess.run", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                _run_ffmpeg(["ffmpeg"])
        self.assertIn("bad input", str(ctx.exception))

    def test_convert_audio_builds_expected_command(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = convert_audio("/tmp/in.webm", output_format="mp3", bitrate="128k")

        self.assertEqual(output, "/tmp/in.mp3")
        run_mock.assert_called_once_with(
            ["ffmpeg", "-y", "-i", "/tmp/in.webm", "-vn", "-ab", "128k", "/tmp/in.mp3"]
        )

    def test_compress_audio_builds_expected_command(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = compress_audio("/tmp/in.mp3", bitrate="64k")

        self.assertEqual(output, "/tmp/in.compressed.mp3")
        run_mock.assert_called_once_with(
            ["ffmpeg", "-y", "-i", "/tmp/in.mp3", "-ab", "64k", "/tmp/in.compressed.mp3"]
        )

    def test_compress_video_builds_expected_command(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = compress_video("/tmp/in.mp4", crf="30")

        self.assertEqual(output, "/tmp/in.compressed.mp4")
        run_mock.assert_called_once_with(
            [
                "ffmpeg",
                "-y",
                "-i",
                "/tmp/in.mp4",
                "-vcodec",
                "libx264",
                "-crf",
                "30",
                "-preset",
                "medium",
                "-acodec",
                "aac",
                "/tmp/in.compressed.mp4",
            ]
        )

    def test_trim_media_uses_default_output_name(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = trim_media("/tmp/in.mp4", start="00:01", end="00:10")

        self.assertEqual(output, "/tmp/in.trimmed.mp4")
        run_mock.assert_called_once_with(
            [
                "ffmpeg",
                "-y",
                "-ss",
                "00:01",
                "-to",
                "00:10",
                "-i",
                "/tmp/in.mp4",
                "-c",
                "copy",
                "/tmp/in.trimmed.mp4",
            ]
        )

    def test_trim_media_respects_custom_output_file(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = trim_media("/tmp/in.mp4", start="00:01", end="00:10", output_file="/tmp/out.mp4")

        self.assertEqual(output, "/tmp/out.mp4")
        run_mock.assert_called_once_with(
            ["ffmpeg", "-y", "-ss", "00:01", "-to", "00:10", "-i", "/tmp/in.mp4", "-c", "copy", "/tmp/out.mp4"]
        )

    def test_extract_audio_for_transcription_builds_expected_command(self) -> None:
        with patch("flowdl.integrations.ffmpeg_wrapper._run_ffmpeg") as run_mock:
            output = extract_audio_for_transcription("/tmp/in.mp4", output_file="/tmp/out.wav")

        self.assertEqual(output, "/tmp/out.wav")
        run_mock.assert_called_once_with(
            ["ffmpeg", "-y", "-i", "/tmp/in.mp4", "-vn", "-ac", "1", "-ar", "16000", "/tmp/out.wav"]
        )


if __name__ == "__main__":
    unittest.main()

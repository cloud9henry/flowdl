import unittest
from unittest.mock import patch

from flowdl.core.processor import postprocess


class ProcessorTests(unittest.TestCase):
    def test_audio_converts_when_extension_differs(self) -> None:
        with patch("flowdl.core.processor.convert_audio", return_value="/tmp/file.mp3") as convert_mock, patch(
            "flowdl.core.processor.compress_audio"
        ) as compress_mock:
            result = postprocess("/tmp/file.webm", {"mode": "audio", "format": "mp3"})

        self.assertEqual(result, "/tmp/file.mp3")
        convert_mock.assert_called_once_with("/tmp/file.webm", output_format="mp3")
        compress_mock.assert_not_called()

    def test_audio_skips_convert_when_extension_matches(self) -> None:
        with patch("flowdl.core.processor.convert_audio") as convert_mock, patch(
            "flowdl.core.processor.compress_audio"
        ) as compress_mock:
            result = postprocess("/tmp/file.mp3", {"mode": "audio", "format": "mp3"})

        self.assertEqual(result, "/tmp/file.mp3")
        convert_mock.assert_not_called()
        compress_mock.assert_not_called()

    def test_audio_compresses_after_conversion(self) -> None:
        with patch("flowdl.core.processor.convert_audio", return_value="/tmp/file.mp3") as convert_mock, patch(
            "flowdl.core.processor.compress_audio", return_value="/tmp/file.compressed.mp3"
        ) as compress_mock:
            result = postprocess("/tmp/file.webm", {"mode": "audio", "format": "mp3", "compress": True})

        self.assertEqual(result, "/tmp/file.compressed.mp3")
        convert_mock.assert_called_once()
        compress_mock.assert_called_once_with("/tmp/file.mp3")

    def test_video_compresses_when_enabled(self) -> None:
        with patch("flowdl.core.processor.compress_video", return_value="/tmp/video.compressed.mp4") as compress_mock:
            result = postprocess("/tmp/video.mp4", {"mode": "video", "compress": True})

        self.assertEqual(result, "/tmp/video.compressed.mp4")
        compress_mock.assert_called_once_with("/tmp/video.mp4")

    def test_video_without_compress_is_passthrough(self) -> None:
        with patch("flowdl.core.processor.compress_video") as compress_mock:
            result = postprocess("/tmp/video.mp4", {"mode": "video"})

        self.assertEqual(result, "/tmp/video.mp4")
        compress_mock.assert_not_called()

    def test_unknown_mode_is_passthrough(self) -> None:
        result = postprocess("/tmp/raw.bin", {"mode": "other"})
        self.assertEqual(result, "/tmp/raw.bin")


if __name__ == "__main__":
    unittest.main()

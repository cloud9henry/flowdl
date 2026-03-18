import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import flowdl.integrations.ytdlp_wrapper as yw
from flowdl.utils.errors import InvalidURLError


class YtDlpWrapperTests(unittest.TestCase):
    def test_is_likely_url(self) -> None:
        self.assertTrue(yw._is_likely_url("https://example.com/video"))
        self.assertTrue(yw._is_likely_url("http://example.com/video"))
        self.assertFalse(yw._is_likely_url("ftp://example.com/video"))
        self.assertFalse(yw._is_likely_url("not-a-url"))

    def test_download_with_ytdlp_rejects_invalid_url(self) -> None:
        with self.assertRaises(InvalidURLError):
            yw.download_with_ytdlp("bad", {"mode": "audio"})

    def test_download_with_ytdlp_errors_if_package_missing(self) -> None:
        with patch.object(yw, "YoutubeDL", None):
            with self.assertRaises(RuntimeError) as ctx:
                yw.download_with_ytdlp("https://example.com", {"mode": "audio"})
        self.assertIn("yt-dlp is not installed", str(ctx.exception))

    def test_download_with_ytdlp_success_audio_mode(self) -> None:
        ydl_instance = MagicMock()
        ydl_instance.extract_info.return_value = {"id": "1"}
        ydl_instance.prepare_filename.return_value = "/tmp/out.webm"
        ydl_context = MagicMock()
        ydl_context.__enter__.return_value = ydl_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yw, "YoutubeDL", return_value=ydl_context) as ydl_ctor:
                output = yw.download_with_ytdlp("https://example.com", {"mode": "audio"}, temp_dir=tmpdir)

        self.assertEqual(output, "/tmp/out.webm")
        ydl_ctor.assert_called_once()
        opts = ydl_ctor.call_args.args[0]
        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertEqual(opts["outtmpl"], str(Path(tmpdir) / "%(title)s.%(ext)s"))
        ydl_instance.extract_info.assert_called_once_with("https://example.com", download=True)

    def test_download_with_ytdlp_success_video_mode(self) -> None:
        ydl_instance = MagicMock()
        ydl_instance.extract_info.return_value = {"id": "1"}
        ydl_instance.prepare_filename.return_value = "/tmp/out.mp4"
        ydl_context = MagicMock()
        ydl_context.__enter__.return_value = ydl_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yw, "YoutubeDL", return_value=ydl_context) as ydl_ctor:
                output = yw.download_with_ytdlp("https://example.com", {"mode": "video"}, temp_dir=tmpdir)

        self.assertEqual(output, "/tmp/out.mp4")
        opts = ydl_ctor.call_args.args[0]
        self.assertEqual(opts["format"], "bestvideo+bestaudio/best")

    def test_download_with_ytdlp_wraps_download_error(self) -> None:
        ydl_instance = MagicMock()
        ydl_instance.extract_info.side_effect = RuntimeError("network")
        ydl_context = MagicMock()
        ydl_context.__enter__.return_value = ydl_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yw, "YoutubeDL", return_value=ydl_context), patch.object(yw, "DownloadError", RuntimeError):
                with self.assertRaises(RuntimeError) as ctx:
                    yw.download_with_ytdlp("https://example.com", {"mode": "audio"}, temp_dir=tmpdir)

        self.assertIn("Download failed for URL", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

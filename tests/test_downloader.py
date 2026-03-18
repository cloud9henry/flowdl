import unittest
from unittest.mock import patch

from flowdl.core.downloader import download_media


class DownloaderTests(unittest.TestCase):
    def test_download_media_delegates_to_wrapper(self) -> None:
        preset = {"mode": "audio"}
        with patch("flowdl.core.downloader.download_with_ytdlp", return_value="/tmp/out.mp3") as mock_dl:
            result = download_media("https://example.com", preset)

        self.assertEqual(result, "/tmp/out.mp3")
        mock_dl.assert_called_once_with("https://example.com", preset)


if __name__ == "__main__":
    unittest.main()

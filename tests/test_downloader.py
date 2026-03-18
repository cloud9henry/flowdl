import unittest
from unittest.mock import patch

from flowdl.core.models import DownloadedMedia
from flowdl.core.downloader import download_media, get_playlist_urls


class DownloaderTests(unittest.TestCase):
    def test_download_media_delegates_to_wrapper(self) -> None:
        preset = {"mode": "audio"}
        expected = DownloadedMedia(file_path="/tmp/out.mp3", metadata={"title": "x"})
        with patch("flowdl.core.downloader.download_with_ytdlp", return_value=expected) as mock_dl:
            result = download_media("https://example.com", preset)

        self.assertEqual(result, expected)
        mock_dl.assert_called_once_with("https://example.com", preset)

    def test_get_playlist_urls_delegates_to_wrapper(self) -> None:
        with patch(
            "flowdl.core.downloader.list_playlist_urls",
            return_value=["https://example.com/a", "https://example.com/b"],
        ) as mock_list:
            result = get_playlist_urls("https://example.com/playlist")

        self.assertEqual(result, ["https://example.com/a", "https://example.com/b"])
        mock_list.assert_called_once_with("https://example.com/playlist")


if __name__ == "__main__":
    unittest.main()

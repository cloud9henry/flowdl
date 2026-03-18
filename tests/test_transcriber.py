import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowdl.core.models import DownloadedMedia
from flowdl.core.transcriber import run_transcription


class TranscriberTests(unittest.TestCase):
    def test_run_transcription_for_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "lecture.mp4"
            source.write_text("data", encoding="utf-8")

            with patch(
                "flowdl.core.transcriber.extract_audio_for_transcription",
                return_value=str(Path(tmpdir) / "Transcripts" / "lecture.wav"),
            ) as extract_mock, patch(
                "flowdl.core.transcriber.transcribe_with_whispercpp",
                return_value=(str(Path(tmpdir) / "Transcripts" / "lecture.txt"), str(Path(tmpdir) / "Transcripts" / "lecture.json")),
            ) as transcribe_mock:
                txt_path, json_path = run_transcription(
                    source=str(source),
                    model_path="/models/base.bin",
                    output_dir=str(Path(tmpdir) / "Transcripts"),
                    language="en",
                )

        self.assertTrue(txt_path.endswith(".txt"))
        self.assertTrue(json_path.endswith(".json"))
        extract_mock.assert_called_once()
        transcribe_mock.assert_called_once()

    def test_run_transcription_for_url_downloads_audio_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_file = Path(tmpdir) / "downloaded.webm"
            downloaded_file.write_text("data", encoding="utf-8")
            wav_file = Path(tmpdir) / "Transcripts" / "Lecture.wav"
            wav_file.parent.mkdir(parents=True, exist_ok=True)
            wav_file.write_text("wav", encoding="utf-8")

            with patch(
                "flowdl.core.transcriber.download_media",
                return_value=DownloadedMedia(
                    file_path=str(downloaded_file),
                    metadata={"title": "Lecture"},
                ),
            ) as dl_mock, patch(
                "flowdl.core.transcriber.extract_audio_for_transcription",
                return_value=str(wav_file),
            ) as extract_mock, patch(
                "flowdl.core.transcriber.transcribe_with_whispercpp",
                return_value=(str(Path(tmpdir) / "Transcripts" / "Lecture.txt"), str(Path(tmpdir) / "Transcripts" / "Lecture.json")),
            ):
                run_transcription(
                    source="https://example.com/video",
                    model_path="/models/base.bin",
                    output_dir=str(Path(tmpdir) / "Transcripts"),
                )

            dl_mock.assert_called_once()
            extract_mock.assert_called_once()
            self.assertFalse(downloaded_file.exists())
            self.assertFalse(wav_file.exists())


if __name__ == "__main__":
    unittest.main()


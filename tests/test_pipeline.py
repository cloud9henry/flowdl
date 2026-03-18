import unittest
from unittest.mock import patch

from flowdl.core.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_run_pipeline_chains_stages(self) -> None:
        preset = {"mode": "audio", "output_dir": "/tmp"}
        with patch("flowdl.core.pipeline.download_media", return_value="/tmp/source.webm") as d_mock, patch(
            "flowdl.core.pipeline.postprocess", return_value="/tmp/source.mp3"
        ) as p_mock, patch("flowdl.core.pipeline.organise_output", return_value="/tmp/final/source.mp3") as o_mock:
            final_path = run_pipeline("https://example.com/video", preset)

        self.assertEqual(final_path, "/tmp/final/source.mp3")
        d_mock.assert_called_once_with("https://example.com/video", preset)
        p_mock.assert_called_once_with("/tmp/source.webm", preset)
        o_mock.assert_called_once_with("/tmp/source.mp3", preset)

    def test_run_pipeline_propagates_stage_errors(self) -> None:
        preset = {"mode": "audio"}
        with patch("flowdl.core.pipeline.download_media", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                run_pipeline("https://example.com/video", preset)

    def test_run_pipeline_creates_audio_sidecar_for_video_mode(self) -> None:
        preset = {"mode": "video", "output_dir": "/tmp/videos", "audio_output_dir": "/tmp/audio"}
        with patch("flowdl.core.pipeline.download_media", return_value="/tmp/source.webm"), patch(
            "flowdl.core.pipeline.postprocess", return_value="/tmp/source.mp4"
        ), patch(
            "flowdl.core.pipeline.organise_output",
            side_effect=["/tmp/videos/source.mp4", "/tmp/audio/source.mp3"],
        ) as organise_mock, patch(
            "flowdl.core.pipeline.convert_audio", return_value="/tmp/source.mp3"
        ) as audio_mock:
            final_path = run_pipeline("https://example.com/video", preset, audio_sidecar=True)

        self.assertEqual(final_path, "/tmp/videos/source.mp4")
        audio_mock.assert_called_once_with("/tmp/source.mp4", output_format="mp3")
        self.assertEqual(organise_mock.call_count, 2)

    def test_run_pipeline_does_not_create_sidecar_for_audio_mode(self) -> None:
        preset = {"mode": "audio", "output_dir": "/tmp/audio"}
        with patch("flowdl.core.pipeline.download_media", return_value="/tmp/source.webm"), patch(
            "flowdl.core.pipeline.postprocess", return_value="/tmp/source.mp3"
        ), patch(
            "flowdl.core.pipeline.organise_output", return_value="/tmp/audio/source.mp3"
        ), patch("flowdl.core.pipeline.convert_audio") as audio_mock:
            run_pipeline("https://example.com/video", preset, audio_sidecar=True)

        audio_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
